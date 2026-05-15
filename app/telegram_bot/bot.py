import logging
import os
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
# httpx logs every request including the URL which contains the bot token
logging.getLogger("httpx").setLevel(logging.WARNING)

# Add the telegram_bot directory to the path so imports work cleanly
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv

# Load .env from workspace root (two levels above app/telegram_bot/)
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=_env_path)

from telegram.ext import Application, MessageHandler, CommandHandler, filters
from handlers.message_handler import handle_message
from handlers.start_handler import handle_start
from handlers.test_checkin_handler import handle_test_checkin_midday, handle_test_checkin_afternoon
from services.scheduler_service import register_checkins
from services.reminder_service import load_pending_reminders


def main() -> None:
    token = os.getenv("BOT_API")
    if not token:
        raise ValueError(
            "BOT_API no está configurado. "
            "Añade BOT_API=<token> al archivo .env en la raíz del workspace."
        )

    bot_name = os.getenv("BOT_NAME", "bot")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("test_checkin_midday", handle_test_checkin_midday))
    app.add_handler(CommandHandler("test_checkin_afternoon", handle_test_checkin_afternoon))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    register_checkins(app)
    load_pending_reminders(app.job_queue)

    print(f"[{bot_name}] Bot iniciado en modo polling. Esperando mensajes...")
    app.run_polling()


if __name__ == "__main__":
    main()
