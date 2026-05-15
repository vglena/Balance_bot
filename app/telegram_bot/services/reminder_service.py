"""
Reminder service for calendar events.

Schedules Telegram messages 2 hours before events created via the bot.
Persists pending reminders in context/scheduled_reminders.json so they
survive bot restarts.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

_TZ = ZoneInfo("Europe/Madrid")

# Workspace root is 3 levels above this file:
# services/ -> telegram_bot/ -> app/ -> workspace_root/
_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
_REMINDERS_FILE = _WORKSPACE_ROOT / "context" / "scheduled_reminders.json"

_REMINDER_HOURS = float(os.getenv("EVENT_REMINDER_HOURS_BEFORE", "2"))
_ENABLED = os.getenv("ENABLE_TELEGRAM_EVENT_REMINDERS", "true").strip().lower() != "false"


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def _load_reminders() -> list:
    if not _REMINDERS_FILE.exists():
        return []
    try:
        return json.loads(_REMINDERS_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("No se pudo leer %s: %s", _REMINDERS_FILE, exc)
        return []


def _save_reminders(reminders: list) -> None:
    _REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _REMINDERS_FILE.write_text(
        json.dumps(reminders, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Callback factory
# ---------------------------------------------------------------------------

def _make_reminder_callback(title: str, reminder_id: str):
    """Return an async JobQueue callback that sends the reminder message."""

    async def callback(context) -> None:
        # Skip if reminder has been cancelled, sent, or skipped since it was scheduled
        current = _load_reminders()
        for r in current:
            if r.get("id") == reminder_id:
                if r.get("status") in ("cancelled", "sent", "skipped"):
                    logger.info(
                        "Recordatorio omitido (estado '%s'): %s",
                        r.get("status"),
                        reminder_id,
                    )
                    return
                break

        user_id = os.getenv("AUTHORIZED_TELEGRAM_USER_ID", "").strip()
        if not user_id:
            logger.warning(
                "Recordatorio omitido: AUTHORIZED_TELEGRAM_USER_ID no configurado."
            )
            return

        text = f"Recordatorio: en 2 horas tienes {title}."
        await context.bot.send_message(chat_id=int(user_id), text=text)
        logger.info("Recordatorio enviado: %s", title)

        # Mark as sent in the JSON file
        reminders = _load_reminders()
        for r in reminders:
            if r.get("id") == reminder_id:
                r["status"] = "sent"
                break
        _save_reminders(reminders)

    return callback


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def schedule_event_reminder(
    job_queue,
    calendar_event_id: str,
    title: str,
    event_datetime: datetime,
) -> dict:
    """
    Schedule a Telegram reminder 2 hours before the event.

    Returns a dict with:
      - status: "scheduled" | "skipped" | "disabled"
      - reminder_datetime: ISO string (present when scheduled or skipped)
    """
    if not _ENABLED:
        logger.info("Recordatorios de Telegram desactivados.")
        return {"status": "disabled"}

    if event_datetime.tzinfo is None:
        event_datetime = event_datetime.replace(tzinfo=_TZ)

    reminder_dt = event_datetime - timedelta(hours=_REMINDER_HOURS)
    now = datetime.now(tz=_TZ)

    reminder_id = f"{calendar_event_id}_reminder"
    reminder_data = {
        "id": reminder_id,
        "calendar_event_id": calendar_event_id,
        "title": title,
        "event_datetime": event_datetime.isoformat(),
        "reminder_datetime": reminder_dt.isoformat(),
        "status": "pending",
    }

    if reminder_dt <= now:
        logger.warning(
            "Recordatorio para '%s' ya ha pasado (%s), se omite.", title, reminder_dt
        )
        reminder_data["status"] = "skipped"
        reminders = _load_reminders()
        reminders = [r for r in reminders if r.get("id") != reminder_id]
        reminders.append(reminder_data)
        _save_reminders(reminders)
        return {"status": "skipped", "reminder_datetime": reminder_dt.isoformat()}

    # Persist
    reminders = _load_reminders()
    reminders = [r for r in reminders if r.get("id") != reminder_id]
    reminders.append(reminder_data)
    _save_reminders(reminders)

    # Schedule
    job_queue.run_once(
        callback=_make_reminder_callback(title, reminder_id),
        when=reminder_dt,
        name=reminder_id,
    )
    logger.info(
        "Recordatorio programado para '%s' a las %s",
        title,
        reminder_dt.strftime("%d/%m/%Y %H:%M"),
    )
    return {"status": "scheduled", "reminder_datetime": reminder_dt.isoformat()}


def load_pending_reminders(job_queue) -> None:
    """
    Load reminders from disk and reschedule any that are still in the future.
    Call this once at bot startup.
    """
    reminders = _load_reminders()
    now = datetime.now(tz=_TZ)
    rescheduled = 0

    for r in reminders:
        if r.get("status") != "pending":
            continue
        try:
            reminder_dt = datetime.fromisoformat(r["reminder_datetime"])
            if reminder_dt.tzinfo is None:
                reminder_dt = reminder_dt.replace(tzinfo=_TZ)

            if reminder_dt <= now:
                r["status"] = "skipped"
                logger.info(
                    "Recordatorio '%s' ya pasó al arrancar, marcado como skipped.",
                    r.get("title"),
                )
                continue

            reminder_id = r["id"]
            title = r["title"]
            job_queue.run_once(
                callback=_make_reminder_callback(title, reminder_id),
                when=reminder_dt,
                name=reminder_id,
            )
            rescheduled += 1
        except Exception as exc:
            logger.error("Error reprogramando recordatorio %s: %s", r.get("id"), exc)

    _save_reminders(reminders)

    if rescheduled:
        logger.info("%d recordatorio(s) reprogramado(s) al arrancar.", rescheduled)


def cancel_reminder(calendar_event_id: str, job_queue) -> bool:
    """
    Cancel a pending Telegram reminder for the given calendar event ID.

    Marks the reminder as 'cancelled' in the JSON file so the callback skips
    sending if it fires. Also removes the job from the APScheduler queue.
    Returns True if a pending reminder was found and cancelled, False otherwise.
    """
    reminders = _load_reminders()
    cancelled = False
    reminder_id = None

    for r in reminders:
        if r.get("calendar_event_id") == calendar_event_id and r.get("status") == "pending":
            r["status"] = "cancelled"
            reminder_id = r.get("id")
            cancelled = True
            logger.info(
                "Recordatorio cancelado para evento %s (reminder_id=%s)",
                calendar_event_id,
                reminder_id,
            )
            break

    if cancelled:
        _save_reminders(reminders)

    if reminder_id and job_queue:
        for job in job_queue.get_jobs_by_name(reminder_id):
            job.schedule_removal()
            logger.info("Job de recordatorio eliminado de la cola: %s", reminder_id)

    return cancelled
