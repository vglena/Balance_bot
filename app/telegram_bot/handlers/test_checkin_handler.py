import logging
import os

from telegram import Update
from telegram.ext import ContextTypes

from services.scheduler_service import MSG_MIDDAY, MSG_AFTERNOON

logger = logging.getLogger(__name__)

_AUTHORIZED_USER_ID = os.getenv("AUTHORIZED_TELEGRAM_USER_ID", "").strip()


def _is_authorized(user_id: str) -> bool:
    authorized = os.getenv("AUTHORIZED_TELEGRAM_USER_ID", "").strip()
    return not authorized or user_id == authorized


async def handle_test_checkin_midday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if not _is_authorized(user_id):
        logger.warning("test_checkin_midday rechazado: usuario no autorizado %s", user_id)
        await update.message.reply_text("No autorizado.")
        return
    logger.info("test_checkin_midday enviado manualmente por usuario %s", user_id)
    await update.message.reply_text(MSG_MIDDAY)


async def handle_test_checkin_afternoon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if not _is_authorized(user_id):
        logger.warning("test_checkin_afternoon rechazado: usuario no autorizado %s", user_id)
        await update.message.reply_text("No autorizado.")
        return
    logger.info("test_checkin_afternoon enviado manualmente por usuario %s", user_id)
    await update.message.reply_text(MSG_AFTERNOON)
