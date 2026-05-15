"""
Google Calendar service.

Uses OAuth 2.0 user credentials to create calendar events.
Credentials and token paths are configured via .env variables.
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

_TZ = ZoneInfo("Europe/Madrid")
_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

# Workspace root is 3 levels above this file:
# services/ -> telegram_bot/ -> app/ -> workspace_root/
_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


def _get_credentials():
    """Load or refresh OAuth 2.0 credentials. Opens browser on first run."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds_path = _WORKSPACE_ROOT / os.getenv(
        "GOOGLE_CALENDAR_CREDENTIALS_PATH",
        "credentials/google_calendar_credentials.json",
    )
    token_path = _WORKSPACE_ROOT / os.getenv(
        "GOOGLE_CALENDAR_TOKEN_PATH",
        "credentials/google_calendar_token.json",
    )

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), _SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                raise FileNotFoundError(
                    f"No se encontró el archivo de credenciales: {creds_path}\n"
                    "Descarga el JSON de OAuth desde Google Cloud Console y "
                    "guárdalo en esa ruta. Ver README para instrucciones."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(creds_path), _SCOPES
            )
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")
        logger.info("Token de Google Calendar guardado en %s", token_path)

    return creds


def create_calendar_event(
    title: str,
    start_datetime: datetime,
    duration_minutes: int = 30,
    description: str = "",
    force: bool = False,
) -> dict:
    """
    Create an event in Google Calendar.

    Returns a dict with status "created", "duplicate", or "conflict".
    - "duplicate": exact same title+time already exists (always blocked).
    - "conflict": a different event overlaps the time slot; blocked unless force=True.
    - "created": event successfully created.
    Raises on API error or missing credentials.
    """
    from googleapiclient.discovery import build

    creds = _get_credentials()
    service = build("calendar", "v3", credentials=creds)

    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

    if start_datetime.tzinfo is None:
        start_datetime = start_datetime.replace(tzinfo=_TZ)

    end_datetime = start_datetime + timedelta(minutes=duration_minutes)

    event_body = {
        "summary": title,
        "description": description,
        "start": {
            "dateTime": start_datetime.isoformat(),
            "timeZone": "Europe/Madrid",
        },
        "end": {
            "dateTime": end_datetime.isoformat(),
            "timeZone": "Europe/Madrid",
        },
        # Telegram handles the important reminder — disable Google Calendar ones
        "reminders": {
            "useDefault": False,
            "overrides": [],
        },
    }

    # Check for duplicates: query events in a ±5-minute window around start time
    window_start = (start_datetime - timedelta(minutes=5)).isoformat()
    window_end = (start_datetime + timedelta(minutes=5)).isoformat()
    existing_events = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=window_start,
            timeMax=window_end,
            singleEvents=True,
        )
        .execute()
        .get("items", [])
    )

    normalized_title = title.lower().strip()
    for ev in existing_events:
        if ev.get("summary", "").lower().strip() == normalized_title:
            logger.info(
                "Evento duplicado detectado: '%s' ya existe (%s)", title, ev.get("id")
            )
            return {
                "status": "duplicate",
                "id": ev.get("id"),
                "htmlLink": ev.get("htmlLink"),
                "summary": ev.get("summary"),
                "start": ev.get("start"),
                "end": ev.get("end"),
            }

    # Check for schedule conflicts (different title, overlapping time slot)
    if not force:
        overlap_events = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=start_datetime.isoformat(),
                timeMax=end_datetime.isoformat(),
                singleEvents=True,
            )
            .execute()
            .get("items", [])
        )
        conflicts = [
            {
                "id": ev.get("id"),
                "summary": ev.get("summary"),
                "start": ev.get("start"),
                "end": ev.get("end"),
                "htmlLink": ev.get("htmlLink"),
            }
            for ev in overlap_events
            if ev.get("summary", "").lower().strip() != normalized_title
        ]
        if conflicts:
            logger.info(
                "Conflicto horario detectado al crear '%s': %d evento(s) superpuesto(s).",
                title,
                len(conflicts),
            )
            return {"status": "conflict", "conflicts": conflicts}

    event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
    logger.info("Evento creado en Google Calendar: %s (%s)", title, event.get("id"))

    return {
        "status": "created",
        "id": event.get("id"),
        "htmlLink": event.get("htmlLink"),
        "summary": event.get("summary"),
        "start": event.get("start"),
        "end": event.get("end"),
    }


def find_calendar_events(
    title: str | None = None,
    event_date=None,
    event_time=None,
    search_window_days: int = 14,
) -> list:
    """
    Search for calendar events matching an optional title, date and/or time.

    - date + time: ±5-minute window around the given datetime
    - date only: entire day
    - no date: next search_window_days days from now

    Title matching: normalized substring (title in event or event in title).
    Returns a list of dicts: id, summary, start, end, htmlLink.
    """
    from googleapiclient.discovery import build

    creds = _get_credentials()
    service = build("calendar", "v3", credentials=creds)

    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    now = datetime.now(tz=_TZ)

    if event_date and event_time:
        hour, minute = event_time
        center = datetime(
            event_date.year, event_date.month, event_date.day,
            hour, minute, tzinfo=_TZ,
        )
        time_min = (center - timedelta(minutes=5)).isoformat()
        time_max = (center + timedelta(minutes=5)).isoformat()
    elif event_date:
        day_start = datetime(
            event_date.year, event_date.month, event_date.day, 0, 0, 0, tzinfo=_TZ
        )
        time_min = day_start.isoformat()
        time_max = (day_start + timedelta(days=1)).isoformat()
    else:
        time_min = now.isoformat()
        time_max = (now + timedelta(days=search_window_days)).isoformat()

    raw = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
        .get("items", [])
    )

    def _item(ev):
        return {
            "id": ev.get("id"),
            "summary": ev.get("summary"),
            "start": ev.get("start"),
            "end": ev.get("end"),
            "htmlLink": ev.get("htmlLink"),
        }

    if not title:
        return [_item(ev) for ev in raw]

    normalized = title.lower().strip()
    return [
        _item(ev)
        for ev in raw
        if normalized in ev.get("summary", "").lower().strip()
        or ev.get("summary", "").lower().strip() in normalized
    ]


def delete_calendar_event(event_id: str) -> dict:
    """
    Delete a Google Calendar event by its ID.
    Returns {"status": "deleted", "event_id": event_id}.
    Raises on API error.
    """
    from googleapiclient.discovery import build

    creds = _get_credentials()
    service = build("calendar", "v3", credentials=creds)

    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    logger.info("Evento eliminado de Google Calendar: %s", event_id)
    return {"status": "deleted", "event_id": event_id}
