import asyncio
import logging
import os
from pathlib import Path

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from services.runtime_context import get_runtime_context, format_runtime_context
from services.agent_context_loader import load_agent_context
from services.llm_client import call_llm

logger = logging.getLogger(__name__)

_AUTHORIZED_USER_ID = os.getenv("AUTHORIZED_TELEGRAM_USER_ID", "").strip()

# Conversation history per user (in-memory, resets on bot restart)
# Keys: user_id (str), Values: list of {"role": "user"/"assistant", "content": str}
_CONVERSATION_HISTORY: dict[str, list[dict]] = {}
_HISTORY_MAX_MESSAGES = 20  # 10 turns

if not _AUTHORIZED_USER_ID:
    logger.warning(
        "AUTHORIZED_TELEGRAM_USER_ID no está configurado. "
        "El bot responderá a cualquier usuario. "
        "Configura esta variable en .env antes de usar el bot en producción."
    )

# System prompt lives next to the handlers directory, in prompts/
_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "telegram_system_prompt.md"


def _load_system_prompt() -> str:
    try:
        return _PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return "Eres un asistente de vida cotidiana. Sé breve y práctico."


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
