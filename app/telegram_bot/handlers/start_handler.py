import os

from telegram import Update
from telegram.ext import ContextTypes

_BOT_NAME = os.getenv("BOT_NAME", "balance_bot")

_GREETING = (
    "Hola. Soy tu asistente de vida cotidiana.\n\n"
    "Puedo ayudarte con:\n"
    "- Plan del día o de la semana\n"
    "- Qué hacer ahora o en un hueco\n"
    "- Decisiones de tarde con los niños\n"
    "- Prioridades de trabajo o casa\n\n"
    "Escríbeme en lenguaje natural. Por ejemplo:\n"
    "  \"qué hago ahora\"\n"
    "  \"planifica mañana\"\n"
    "  \"¿voy al parque o a casa?\"\n"
    "  \"estoy cansado\""
)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(_GREETING)
