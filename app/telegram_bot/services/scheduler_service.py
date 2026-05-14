"""
Proactive check-ins scheduler.

Sends a message to the authorized user at 13:00 and 18:30, Monday–Friday.
Uses python-telegram-bot's built-in JobQueue (APScheduler).
Does NOT call the LLM — messages are fixed text.
"""

import logging
import os
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

_TZ = ZoneInfo("Europe/Madrid")

MSG_MIDDAY = (
    "Son las 13:00. ¿Cómo vas?\n\n"
    "Cuéntame:\n"
    "- qué has terminado\n"
    "- qué queda pendiente\n"
    "- cómo estás\n"
    "- si hay algo nuevo"
)

MSG_AFTERNOON = (
    "Son las 18:30. ¿Cómo va la tarde?\n\n"
    "Cuéntame:\n"
    "- dónde estáis\n"
    "- cómo están los niños\n"
    "- cómo estás tú\n"
    "- qué queda pendiente"
)


async def _send_checkin(context, text: str) -> None:
    user_id = os.getenv("AUTHORIZED_TELEGRAM_USER_ID", "").strip()
    if not user_id:
        logger.warning("Check-in omitido: AUTHORIZED_TELEGRAM_USER_ID no configurado.")
        return
    await context.bot.send_message(chat_id=int(user_id), text=text)


async def _checkin_midday(context) -> None:
    await _send_checkin(context, MSG_MIDDAY)


async def _checkin_afternoon(context) -> None:
    await _send_checkin(context, MSG_AFTERNOON)


def register_checkins(app) -> None:
    """Register daily check-in jobs. Call after Application is built."""

    enabled = os.getenv("ENABLE_PROACTIVE_CHECKINS", "true").strip().lower()
    if enabled == "false":
        logger.info("Check-ins proactivos desactivados (ENABLE_PROACTIVE_CHECKINS=false).")
        return

    user_id = os.getenv("AUTHORIZED_TELEGRAM_USER_ID", "").strip()
    if not user_id:
        logger.warning(
            "Check-ins proactivos no programados: "
            "AUTHORIZED_TELEGRAM_USER_ID no está configurado."
        )
        return

    jq = app.job_queue
    if jq is None:
        logger.error("JobQueue no disponible. Instala 'apscheduler' para usar check-ins.")
        return

    # Monday=0 … Friday=4
    weekdays = tuple(range(5))

    jq.run_daily(
        callback=_checkin_midday,
        time=__import__("datetime").time(13, 0, tzinfo=_TZ),
        days=weekdays,
        name="checkin_midday",
    )
    jq.run_daily(
        callback=_checkin_afternoon,
        time=__import__("datetime").time(18, 30, tzinfo=_TZ),
        days=weekdays,
        name="checkin_afternoon",
    )

    logger.info(
        "Check-ins proactivos programados: 13:00 y 18:30 (L-V, Europe/Madrid) "
        "→ usuario %s", user_id
    )
