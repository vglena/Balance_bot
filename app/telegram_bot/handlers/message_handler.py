import asyncio
import logging
import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from services.runtime_context import get_runtime_context, format_runtime_context
from services.agent_context_loader import load_agent_context
from services.llm_client import call_llm

logger = logging.getLogger(__name__)

_AUTHORIZED_USER_ID = os.getenv("AUTHORIZED_TELEGRAM_USER_ID", "").strip()
_TZ = ZoneInfo("Europe/Madrid")

# Conversation history per user (in-memory, resets on bot restart)
# Keys: user_id (str), Values: list of {"role": "user"/"assistant", "content": str}
_CONVERSATION_HISTORY: dict[str, list[dict]] = {}
_HISTORY_MAX_MESSAGES = 20  # 10 turns

# Pending calendar event state per user (in-memory, resets on bot restart)
# {user_id: {"awaiting": "datetime"|"title", "title": str|None,
#            "date": date|None, "time": tuple|None}}
_PENDING_EVENTS: dict[str, dict] = {}

if not _AUTHORIZED_USER_ID:
    logger.warning(
        "AUTHORIZED_TELEGRAM_USER_ID no está configurado. "
        "El bot responderá a cualquier usuario. "
        "Configura esta variable en .env antes de usar el bot en producción."
    )

# System prompt lives next to the handlers directory, in prompts/
_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "telegram_system_prompt.md"


# ---------------------------------------------------------------------------
# Calendar intent detection and parsing
# ---------------------------------------------------------------------------

# Only match when the user explicitly mentions Google Calendar.
# This avoids false positives with common words like "agenda" or "evento".
_CALENDAR_PATTERNS = [
    # añade/añadir/agrega/agregar a/al Google Calendar [contenido]
    r"(?:a[nñ]ade[r]?|a[nñ]adir|agregar?)\s+al?\s+google\s+calendar",
    # pon en Google Calendar [contenido]
    r"pon\s+en\s+google\s+calendar",
    # anota/anótame/anotar/apunta/apúntame en Google Calendar [contenido]
    r"(?:an[oó]ta[r]?(?:me)?|ap[uú]nta[r]?(?:me)?)\s+(?:en|al?)\s+google\s+calendar",
    # anota/apunta [contenido] en Google Calendar  (Google Calendar al final)
    r"(?:an[oó]ta[r]?(?:me)?|ap[uú]nta[r]?(?:me)?)\s+\S.+\s+en\s+google\s+calendar",
    # verb + "evento" — sin Google Calendar, acción explícita con palabra clave
    r"(?:crea[r]?|a[nñ]ade[r]?|a[nñ]adir|agregar?|an[oó]ta[r]?(?:me)?|ap[uú]nta[r]?(?:me)?|pon)\s+evento\b",
]

_MONTHS_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

_WEEKDAYS_ES = {
    "lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2,
    "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6,
}

_MONTH_NAMES_DISPLAY = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _is_calendar_intent(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in _CALENDAR_PATTERNS)


# Delete intent detection — requires "Google Calendar" OR verb + "evento"
_DELETE_PATTERNS = [
    # borra/elimina/quita de/del/en Google Calendar [...]
    r"(?:borra[r]?|elimina[r]?|quita[r]?)\s+(?:de[l]?|en)\s+google\s+calendar",
    # borra/elimina/quita [...] de/del/en Google Calendar
    r"(?:borra[r]?|elimina[r]?|quita[r]?)\s+\S.+\s+(?:de[l]?|en)\s+google\s+calendar",
    # verb + "evento" — sin Google Calendar, acción explícita con palabra clave
    r"(?:borra[r]?|elimina[r]?|quita[r]?|cancela[r]?)\s+evento\b",
]

_CONFIRM_YES = frozenset({
    "sí", "si", "confirmo", "créalo", "crealo", "adelante",
    "bórralo", "borralo", "elimínalo", "eliminalo",
})
_CONFIRM_NO = frozenset({"no", "cancelar", "cancela"})


def _is_delete_intent(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in _DELETE_PATTERNS)


# Bulk delete guard — prevents mass-deletion requests
_BULK_DELETE_PATTERNS = [
    r"\btodos\s+(?:los\s+)?eventos\b",
    r"\btodo\s+el\s+d[ií]a\b",
    r"\b(?:borra[r]?|elimina[r]?|quita[r]?|cancela[r]?)\s+todos\b",
    r"\bborra[r]?\s+mis\s+eventos\b",
    r"\belimina[r]?\s+mis\s+eventos\b",
]


def _is_bulk_delete(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in _BULK_DELETE_PATTERNS)


# Modify intent — verb + "evento" (feature not yet implemented)
_MODIFY_PATTERNS = [
    r"(?:modifica[r]?|cambia[r]?|mueve[r]?|actualiza[r]?)\s+evento\b",
]


def _is_modify_intent(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in _MODIFY_PATTERNS)


# Defensive fallback — calendar-like phrases without "evento" or "Google Calendar"
_CALENDAR_HINT_PATTERNS = [
    # crea/pon + anything (no "evento", no Google Calendar)
    r"^(?:crea[r]?|pon)\s+(?!evento\b)(?!.*\bgoogle\s+calendar\b)\S",
    # añade/anota/apunta + time indicator (no "evento", no Google Calendar)
    (
        r"^(?:a[nñ]ade[r]?|a[nñ]adir|agregar?|an[oó]ta[r]?(?:me)?|ap[uú]nta[r]?(?:me)?)"
        r"\s+(?!evento\b)(?!.*\bgoogle\s+calendar\b)"
        r".*\b(?:mañana|hoy|pasado\s+mañana|lunes|martes|mi[eé]rcoles|jueves|viernes"
        r"|s[aá]bado|domingo|a\s+las|\d{1,2}:\d{2})\b"
    ),
    # borra/elimina/quita + anything (no "evento", no bulk terms, no Google Calendar)
    r"^(?:borra[r]?|elimina[r]?|quita[r]?)\s+(?!evento\b)(?!todos?\b)(?!.*\bgoogle\s+calendar\b)\S",
    # cancela + time indicator (no "evento", no Google Calendar)
    (
        r"^cancela[r]?\s+(?!evento\b)(?!.*\bgoogle\s+calendar\b)"
        r".*\b(?:mañana|hoy|pasado\s+mañana|lunes|martes|mi[eé]rcoles|jueves|viernes"
        r"|s[aá]bado|domingo|a\s+las|\d{1,2}:\d{2})\b"
    ),
    # modifica + anything except "evento" ("modifica evento" handled by _is_modify_intent)
    r"^modifica[r]?\s+(?!evento\b)\S",
]


def _is_calendar_hint(text: str) -> bool:
    t = text.lower().strip()
    return any(re.search(p, t) for p in _CALENDAR_HINT_PATTERNS)


def _parse_date(text: str):
    """Return a date object or None."""
    t = text.lower().strip()
    today = datetime.now(tz=_TZ).date()

    if re.search(r"\bpasado\s+mañana\b", t):
        return today + timedelta(days=2)
    if re.search(r"\bmañana\b", t):
        return today + timedelta(days=1)
    if re.search(r"\bhoy\b", t):
        return today

    # Weekday names (with optional prefix)
    for day_name, day_num in _WEEKDAYS_ES.items():
        if re.search(rf"\b(?:el\s+|este\s+|pr[oó]ximo\s+)?{day_name}\b", t):
            days_ahead = day_num - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return today + timedelta(days=days_ahead)

    # "23 de mayo" or "el 23 de mayo de 2026"
    month_pattern = "|".join(_MONTHS_ES.keys())
    m = re.search(
        rf"\b(\d{{1,2}})\s+de\s+({month_pattern})(?:\s+(?:de\s+)?(\d{{4}}))?\b", t
    )
    if m:
        day = int(m.group(1))
        month = _MONTHS_ES[m.group(2)]
        year = int(m.group(3)) if m.group(3) else today.year
        try:
            d = date(year, month, day)
            if d < today:
                d = date(year + 1, month, day)
            return d
        except ValueError:
            pass

    # "el día 25" or "día 25"
    m = re.search(r"\b(?:el\s+)?d[ií]a\s+(\d{1,2})\b", t)
    if m:
        day = int(m.group(1))
        try:
            d = date(today.year, today.month, day)
            if d < today:
                next_month = today.month + 1 if today.month < 12 else 1
                next_year = today.year if today.month < 12 else today.year + 1
                d = date(next_year, next_month, day)
            return d
        except ValueError:
            pass

    # "23/05" or "23/05/2026" or "23-05" or "23-05-2026"
    m = re.search(r"\b(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{4}))?\b", t)
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3)) if m.group(3) else today.year
        try:
            d = date(year, month, day)
            if d < today:
                d = date(year + 1, month, day)
            return d
        except ValueError:
            pass

    return None


def _parse_time(text: str):
    """Return a (hour, minute) tuple or None."""
    t = text.lower()

    # "a las 10" or "a las 10:30"
    m = re.search(r"\ba\s+las\s+(\d{1,2})(?::(\d{2}))?\b", t)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (hour, minute)

    # "10:30", "17:30"
    m = re.search(r"\b(\d{1,2}):(\d{2})\b", t)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (hour, minute)

    return None


def _extract_title(text: str) -> str:
    """Remove trigger keywords, date and time tokens; return the remaining title.

    Original casing is preserved so event titles appear correctly in Calendar.
    All pattern matching uses re.IGNORECASE.
    """
    result = text.strip()
    F = re.IGNORECASE

    # Remove the Google Calendar trigger — prefix forms (verb + Google Calendar + content)
    result = re.sub(
        r"(?:a[nñ]ade[r]?|a[nñ]adir|agregar?)\s+al?\s+google\s+calendar"
        r"|pon\s+en\s+google\s+calendar"
        r"|(?:an[oó]ta[r]?(?:me)?|ap[uú]nta[r]?(?:me)?)\s+(?:en|al?)\s+google\s+calendar",
        " ", result, count=1, flags=F,
    )
    # Remove "en Google Calendar" suffix (verb + content + Google Calendar)
    result = re.sub(r"\s+en\s+google\s+calendar\b", " ", result, flags=F)
    # Remove leading verb if still present after suffix removal
    result = re.sub(
        r"^(?:an[oó]ta[r]?(?:me)?|ap[uú]nta[r]?(?:me)?)\s+",
        "", result, flags=F,
    )
    # Remove verb + "evento" prefix (shorthand pattern)
    result = re.sub(
        r"^(?:crea[r]?|a[nñ]ade[r]?|a[nñ]adir|agregar?|an[oó]ta[r]?(?:me)?|ap[uú]nta[r]?(?:me)?|pon)\s+evento\b",
        " ", result, count=1, flags=F,
    )

    # Remove date patterns (most specific first)
    result = re.sub(r"\bpasado\s+mañana\b", " ", result, flags=F)
    result = re.sub(r"\bmañana\b", " ", result, flags=F)
    result = re.sub(r"\bhoy\b", " ", result, flags=F)
    result = re.sub(
        r"\b(?:el\s+|este\s+|pr[oó]ximo\s+)?"
        r"(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\b",
        " ", result, flags=F,
    )
    month_pattern = "|".join(_MONTHS_ES.keys())
    result = re.sub(
        rf"\b(?:el\s+)?\d{{1,2}}\s+de\s+(?:{month_pattern})(?:\s+(?:de\s+)?\d{{4}})?\b",
        " ", result, flags=F,
    )
    result = re.sub(r"\b(?:el\s+)?d[ií]a\s+\d{1,2}\b", " ", result, flags=F)
    result = re.sub(r"\b\d{1,2}[/\-]\d{1,2}(?:[/\-]\d{4})?\b", " ", result, flags=F)

    # Remove time patterns
    result = re.sub(r"\ba\s+las\s+\d{1,2}(?::\d{2})?\b", " ", result, flags=F)
    result = re.sub(r"\b\d{1,2}:\d{2}\b", " ", result, flags=F)

    # Remove leading punctuation / whitespace
    result = re.sub(r"^[\s,;:\-]+", "", result)
    # Remove leading prepositions / articles only at start
    result = re.sub(r"^(?:para|el|la|los|las|de|a|en|un|una)\s+", "", result, flags=F)

    # Collapse multiple spaces
    result = re.sub(r"\s+", " ", result).strip()
    return result


def _extract_delete_title(text: str) -> str:
    """Extract event title from a delete-intent message.

    Removes the delete verb, 'de/en Google Calendar', date/time tokens.
    Original casing is preserved.
    """
    result = text.strip()
    F = re.IGNORECASE

    # Remove delete verb + "evento" prefix (shorthand pattern — verb + evento triggers)
    result = re.sub(
        r"^(?:borra[r]?|elimina[r]?|quita[r]?|cancela[r]?)\s+evento\b",
        " ", result, count=1, flags=F,
    )
    # Remove delete verb + "de/del/en Google Calendar" (prefix form)
    result = re.sub(
        r"(?:borra[r]?|elimina[r]?|quita[r]?|cancela[r]?)\s+(?:de[l]?|en)\s+google\s+calendar",
        " ", result, count=1, flags=F,
    )
    # Remove "de/del/en Google Calendar" suffix
    result = re.sub(r"\s+(?:de[l]?|en)\s+google\s+calendar\b", " ", result, flags=F)
    # Remove leading delete verb if still present
    result = re.sub(
        r"^(?:borra[r]?|elimina[r]?|quita[r]?|cancela[r]?)\s+", "", result, flags=F,
    )
    # Remove "el evento" or "el" article prefix
    result = re.sub(r"^el?\s+evento\s+", "", result, flags=F)

    # Remove date patterns (most specific first)
    result = re.sub(r"\bpasado\s+mañana\b", " ", result, flags=F)
    result = re.sub(r"\bmañana\b", " ", result, flags=F)
    result = re.sub(r"\bhoy\b", " ", result, flags=F)
    result = re.sub(
        r"\b(?:el\s+|este\s+|pr[oó]ximo\s+)?"
        r"(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\b",
        " ", result, flags=F,
    )
    month_pattern = "|".join(_MONTHS_ES.keys())
    result = re.sub(
        rf"\b(?:el\s+)?\d{{1,2}}\s+de\s+(?:{month_pattern})(?:\s+(?:de\s+)?\d{{4}})?\b",
        " ", result, flags=F,
    )
    result = re.sub(r"\b(?:el\s+)?d[ií]a\s+\d{1,2}\b", " ", result, flags=F)
    result = re.sub(r"\b\d{1,2}[/\-]\d{1,2}(?:[/\-]\d{4})?\b", " ", result, flags=F)

    # Remove time patterns
    result = re.sub(r"\ba\s+las\s+\d{1,2}(?::\d{2})?\b", " ", result, flags=F)
    result = re.sub(r"\b\d{1,2}:\d{2}\b", " ", result, flags=F)

    # Clean up
    result = re.sub(r"^[\s,;:\-]+", "", result)
    result = re.sub(r"^(?:para|el|la|los|las|de|a|en|un|una)\s+", "", result, flags=F)
    result = re.sub(r"\s+", " ", result).strip()
    return result


def _format_date_display(d: date) -> str:
    today = datetime.now(tz=_TZ).date()
    if d == today:
        return "hoy"
    if d == today + timedelta(days=1):
        return "mañana"
    if d == today + timedelta(days=2):
        return "pasado mañana"
    return f"el {d.day} de {_MONTH_NAMES_DISPLAY[d.month - 1]}"


def _format_event_display(ev: dict) -> str:
    """Format a Google Calendar event dict as a human-readable string."""
    summary = ev.get("summary", "Sin título")
    start = ev.get("start", {})
    dt_str = start.get("dateTime") or start.get("date", "")
    if dt_str:
        try:
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=_TZ)
            return (
                f"{summary}, {_format_date_display(dt.date())} "
                f"a las {dt.hour:02d}:{dt.minute:02d}"
            )
        except Exception:
            pass
    return summary


# ---------------------------------------------------------------------------
# Calendar creation helper
# ---------------------------------------------------------------------------

async def _handle_calendar_creation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    title: str,
    event_date: date,
    event_time: tuple,
    history: list,
    force: bool = False,
    skip_family_check: bool = False,
) -> None:
    """Create the Google Calendar event and schedule the Telegram reminder."""
    from services.google_calendar_service import create_calendar_event
    from services.reminder_service import schedule_event_reminder
    from services.family_schedule_guard import check_family_conflicts

    user_id = str(update.effective_user.id)
    hour, minute = event_time
    start_dt = datetime(
        event_date.year, event_date.month, event_date.day,
        hour, minute, tzinfo=_TZ,
    )

    # --- Family schedule guard ---
    if not skip_family_check:
        family_conflicts = check_family_conflicts(start_dt, duration_minutes=60)
        if family_conflicts:
            if len(family_conflicts) == 1:
                response = (
                    f"Ese horario coincide con {family_conflicts[0]}. "
                    "¿Quieres crearlo igualmente?"
                )
            else:
                items = "\n".join(f"- {c}" for c in family_conflicts)
                response = (
                    f"Ese horario tiene varios conflictos familiares:\n{items}\n"
                    "¿Quieres crearlo igualmente?"
                )
            _PENDING_EVENTS[user_id] = {
                "awaiting": "family_conflict_confirm",
                "title": title,
                "date": event_date,
                "time": event_time,
            }
            history.append({"role": "assistant", "content": response})
            await update.message.reply_text(response)
            return

    try:
        event = create_calendar_event(title=title, start_datetime=start_dt, force=force)
    except Exception as exc:
        logger.error("Error creando evento en Google Calendar: %s", exc)
        response = f"No pude crear el evento en Google Calendar: {exc}"
        history.append({"role": "assistant", "content": response})
        await update.message.reply_text(response)
        return

    if event.get("status") == "duplicate":
        date_display = _format_date_display(event_date)
        time_display = f"{hour:02d}:{minute:02d}"
        response = (
            f"Ya existe un evento parecido: {title}, "
            f"{date_display} a las {time_display}. No he creado duplicado."
        )
        history.append({"role": "assistant", "content": response})
        await update.message.reply_text(response)
        return

    if event.get("status") == "conflict":
        conflicts = event.get("conflicts", [])
        conflict_lines = "\n".join(f"- {_format_event_display(c)}" for c in conflicts)
        date_display = _format_date_display(event_date)
        time_display = f"{hour:02d}:{minute:02d}"
        response = (
            f"Ya tienes evento(s) a esa hora ({date_display} a las {time_display}):\n"
            f"{conflict_lines}\n"
            f"¿Quieres crearlo igualmente?"
        )
        _PENDING_EVENTS[user_id] = {
            "awaiting": "conflict_confirm",
            "title": title,
            "date": event_date,
            "time": event_time,
            "skip_family_check": skip_family_check,
        }
        history.append({"role": "assistant", "content": response})
        await update.message.reply_text(response)
        return

    reminder_result = schedule_event_reminder(
        job_queue=context.job_queue,
        calendar_event_id=event["id"],
        title=title,
        event_datetime=start_dt,
    )

    date_display = _format_date_display(event_date)
    time_display = f"{hour:02d}:{minute:02d}"
    base = f"Evento añadido: {title}, {date_display} a las {time_display}."

    reminder_status = reminder_result.get("status") if reminder_result else "disabled"
    if reminder_status == "scheduled":
        suffix = " Te escribiré 2 horas antes."
    elif reminder_status == "skipped":
        suffix = " No puedo avisarte 2 horas antes porque ese momento ya ha pasado."
    else:  # disabled
        suffix = " Los recordatorios por Telegram están desactivados."

    response = base + suffix
    history.append({"role": "assistant", "content": response})
    await update.message.reply_text(response)


# ---------------------------------------------------------------------------
# Delete intent helper
# ---------------------------------------------------------------------------

async def _handle_delete_intent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_message: str,
    history: list,
) -> None:
    """Search for matching calendar events and ask the user for confirmation before deleting."""
    from services.google_calendar_service import find_calendar_events

    user_id = str(update.effective_user.id)
    title = _extract_delete_title(user_message)
    event_date = _parse_date(user_message)
    event_time = _parse_time(user_message)

    try:
        candidates = find_calendar_events(
            title=title or None,
            event_date=event_date,
            event_time=event_time,
        )
    except Exception as exc:
        logger.error("Error buscando eventos para borrar: %s", exc)
        response = f"No pude buscar eventos en Google Calendar: {exc}"
        history.append({"role": "assistant", "content": response})
        await update.message.reply_text(response)
        return

    if not candidates:
        response = "No he encontrado ningún evento que coincida con tu búsqueda."
        history.append({"role": "assistant", "content": response})
        await update.message.reply_text(response)
        return

    if len(candidates) == 1:
        ev = candidates[0]
        display = _format_event_display(ev)
        response = f"He encontrado este evento: {display}. ¿Quieres borrarlo?"
        _PENDING_EVENTS[user_id] = {
            "awaiting": "delete_confirm",
            "event_id": ev["id"],
            "title": ev.get("summary", ""),
            "start": ev.get("start", {}),
        }
        history.append({"role": "assistant", "content": response})
        await update.message.reply_text(response)
        return

    # Multiple candidates — ask user to pick one
    lines = [f"{i + 1}. {_format_event_display(ev)}" for i, ev in enumerate(candidates)]
    response = "He encontrado varios eventos. ¿Cuál quieres borrar?\n" + "\n".join(lines)
    _PENDING_EVENTS[user_id] = {
        "awaiting": "delete_select",
        "candidates": candidates,
    }
    history.append({"role": "assistant", "content": response})
    await update.message.reply_text(response)


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

def _load_system_prompt() -> str:
    try:
        return _PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return "Eres un asistente de vida cotidiana. Sé breve y práctico."


# ---------------------------------------------------------------------------
# Main message handler
# ---------------------------------------------------------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)

    if _AUTHORIZED_USER_ID and user_id != _AUTHORIZED_USER_ID:
        logger.warning("Mensaje rechazado de usuario no autorizado: %s", user_id)
        await update.message.reply_text("No autorizado.")
        return

    user_message = (update.message.text or "").strip()
    if not user_message:
        return

    # Maintain conversation history per user
    history = _CONVERSATION_HISTORY.setdefault(user_id, [])
    history.append({"role": "user", "content": user_message})
    if len(history) > _HISTORY_MAX_MESSAGES:
        history[:] = history[-_HISTORY_MAX_MESSAGES:]

    # -----------------------------------------------------------------------
    # Calendar event flow
    # -----------------------------------------------------------------------

    # If user is responding to a pending clarification (and not starting anew)
    if (
        user_id in _PENDING_EVENTS
        and not _is_calendar_intent(user_message)
        and not _is_delete_intent(user_message)
        and not _is_bulk_delete(user_message)
    ):
        pending = _PENDING_EVENTS.pop(user_id)

        if pending["awaiting"] == "datetime":
            parsed_date = _parse_date(user_message)
            parsed_time = _parse_time(user_message)
            if parsed_date and parsed_time:
                await _handle_calendar_creation(
                    update, context, pending["title"], parsed_date, parsed_time, history
                )
                return
            # Still can't extract — fall through to LLM

        elif pending["awaiting"] == "title":
            title = user_message.strip()
            if title:
                await _handle_calendar_creation(
                    update, context, title, pending["date"], pending["time"], history
                )
                return
            # Empty title — fall through to LLM

        elif pending["awaiting"] == "family_conflict_confirm":
            msg = user_message.lower().strip()
            if msg in _CONFIRM_YES:
                await _handle_calendar_creation(
                    update, context,
                    pending["title"], pending["date"], pending["time"],
                    history, skip_family_check=True,
                )
                return
            elif msg in _CONFIRM_NO:
                response = "Cancelado. No he creado el evento."
                history.append({"role": "assistant", "content": response})
                await update.message.reply_text(response)
                return
            # Unclear response — fall through to LLM

        elif pending["awaiting"] == "conflict_confirm":
            msg = user_message.lower().strip()
            if msg in _CONFIRM_YES:
                await _handle_calendar_creation(
                    update, context,
                    pending["title"], pending["date"], pending["time"],
                    history, force=True,
                    skip_family_check=pending.get("skip_family_check", False),
                )
                return
            elif msg in _CONFIRM_NO:
                response = "Cancelado. No he creado el evento."
                history.append({"role": "assistant", "content": response})
                await update.message.reply_text(response)
                return
            # Unclear response — fall through to LLM

        elif pending["awaiting"] == "delete_confirm":
            msg = user_message.lower().strip()
            if msg in _CONFIRM_YES:
                from services.google_calendar_service import delete_calendar_event
                from services.reminder_service import cancel_reminder
                try:
                    delete_calendar_event(pending["event_id"])
                    cancel_reminder(pending["event_id"], context.job_queue)
                except Exception as exc:
                    logger.error("Error borrando evento: %s", exc)
                    response = f"No pude borrar el evento: {exc}"
                    history.append({"role": "assistant", "content": response})
                    await update.message.reply_text(response)
                    return
                start = pending.get("start", {})
                dt_str = start.get("dateTime") or start.get("date", "")
                if dt_str:
                    try:
                        dt = datetime.fromisoformat(dt_str)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=_TZ)
                        date_display = _format_date_display(dt.date())
                        time_display = f"{dt.hour:02d}:{dt.minute:02d}"
                        response = (
                            f"Evento borrado: {pending['title']}, "
                            f"{date_display} a las {time_display}."
                        )
                    except Exception:
                        response = f"Evento borrado: {pending['title']}."
                else:
                    response = f"Evento borrado: {pending['title']}."
                history.append({"role": "assistant", "content": response})
                await update.message.reply_text(response)
                return
            elif msg in _CONFIRM_NO:
                response = "Cancelado. No he borrado el evento."
                history.append({"role": "assistant", "content": response})
                await update.message.reply_text(response)
                return
            # Unclear — fall through to LLM

        elif pending["awaiting"] == "delete_select":
            msg = user_message.strip()
            candidates = pending["candidates"]
            try:
                idx = int(msg) - 1
                if 0 <= idx < len(candidates):
                    ev = candidates[idx]
                    display = _format_event_display(ev)
                    response = f"He seleccionado: {display}. ¿Quieres borrarlo?"
                    _PENDING_EVENTS[user_id] = {
                        "awaiting": "delete_confirm",
                        "event_id": ev["id"],
                        "title": ev.get("summary", ""),
                        "start": ev.get("start", {}),
                    }
                    history.append({"role": "assistant", "content": response})
                    await update.message.reply_text(response)
                    return
                # Out of range — re-prompt
                _PENDING_EVENTS[user_id] = pending
                response = f"Número no válido. Elige entre 1 y {len(candidates)}."
                history.append({"role": "assistant", "content": response})
                await update.message.reply_text(response)
                return
            except (ValueError, TypeError):
                if msg.lower() in _CONFIRM_NO:
                    response = "Cancelado."
                    history.append({"role": "assistant", "content": response})
                    await update.message.reply_text(response)
                    return
                # Not a number and not cancel — re-prompt
                _PENDING_EVENTS[user_id] = pending
                response = (
                    f"Responde con un número del 1 al {len(candidates)} "
                    f"o escribe \"cancelar\"."
                )
                history.append({"role": "assistant", "content": response})
                await update.message.reply_text(response)
                return

    # Bulk delete guard — block mass deletions before any other calendar checks
    if _is_bulk_delete(user_message):
        response = (
            "No puedo borrar eventos en masa por seguridad. "
            "Puedo ayudarte a borrar uno cada vez. "
            "Ejemplo: borra evento Dentista mañana a las 10."
        )
        history.append({"role": "assistant", "content": response})
        await update.message.reply_text(response)
        return

    # New calendar intent in the message
    if _is_calendar_intent(user_message):
        # Clear any stale pending state
        _PENDING_EVENTS.pop(user_id, None)

        enabled = os.getenv("ENABLE_GOOGLE_CALENDAR", "false").strip().lower()
        if enabled != "true":
            response = (
                "Google Calendar aún no está activado. "
                "Activa ENABLE_GOOGLE_CALENDAR=true en .env."
            )
            history.append({"role": "assistant", "content": response})
            await update.message.reply_text(response)
            return

        parsed_date = _parse_date(user_message)
        parsed_time = _parse_time(user_message)
        title = _extract_title(user_message)

        if not parsed_date or not parsed_time:
            _PENDING_EVENTS[user_id] = {"awaiting": "datetime", "title": title or None}
            response = "¿Qué día y a qué hora quieres crear el evento?"
            history.append({"role": "assistant", "content": response})
            await update.message.reply_text(response)
            return

        if not title:
            _PENDING_EVENTS[user_id] = {
                "awaiting": "title",
                "date": parsed_date,
                "time": parsed_time,
            }
            response = "¿Qué título quieres ponerle al evento?"
            history.append({"role": "assistant", "content": response})
            await update.message.reply_text(response)
            return

        await _handle_calendar_creation(
            update, context, title, parsed_date, parsed_time, history
        )
        return

    # New delete intent in the message
    if _is_delete_intent(user_message):
        _PENDING_EVENTS.pop(user_id, None)

        enabled = os.getenv("ENABLE_GOOGLE_CALENDAR", "false").strip().lower()
        if enabled != "true":
            response = (
                "Google Calendar aún no está activado. "
                "Activa ENABLE_GOOGLE_CALENDAR=true en .env."
            )
            history.append({"role": "assistant", "content": response})
            await update.message.reply_text(response)
            return

        await _handle_delete_intent(update, context, user_message, history)
        return

    # Modify intent — not yet implemented
    if _is_modify_intent(user_message):
        response = (
            "Todavía no modifico eventos directamente. "
            "Puedo ayudarte a borrar el evento anterior y crear uno nuevo. "
            "Ejemplo: borra evento Dentista mañana a las 10 "
            "y luego crea evento mañana a las 11 Dentista."
        )
        history.append({"role": "assistant", "content": response})
        await update.message.reply_text(response)
        return

    # Defensive fallback — guide user to use "evento" keyword before reaching LLM
    if _is_calendar_hint(user_message):
        response = (
            "Para acciones reales de calendario usa una frase con la palabra evento. "
            "Ejemplo: crea evento mañana a las 10 Dentista "
            "o borra evento Dentista mañana a las 10."
        )
        history.append({"role": "assistant", "content": response})
        await update.message.reply_text(response)
        return

    # -----------------------------------------------------------------------
    # Standard LLM flow
    # -----------------------------------------------------------------------

    runtime_ctx = get_runtime_context()
    runtime_text = format_runtime_context(runtime_ctx)
    agent_context = load_agent_context()
    base_prompt = _load_system_prompt()

    async def _keep_typing():
        while True:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=ChatAction.TYPING,
            )
            await asyncio.sleep(4)

    typing_task = asyncio.create_task(_keep_typing())
    await asyncio.sleep(0.5)  # dar tiempo a que Telegram muestre el indicador
    try:
        system_prompt = (
            f"{base_prompt}\n\n"
            f"---\n\n"
            f"## Contexto operativo actual\n\n{runtime_text}\n\n"
            f"---\n\n"
            f"## Contexto del sistema\n\n{agent_context}"
        )

        response = await call_llm(system_prompt=system_prompt, messages=list(history))
    finally:
        typing_task.cancel()

    # Add assistant response to history
    history.append({"role": "assistant", "content": response})

    # Eliminar formato Markdown que Telegram no renderiza sin parse_mode
    response = response.replace("**", "").replace("__", "")
    await update.message.reply_text(response)
