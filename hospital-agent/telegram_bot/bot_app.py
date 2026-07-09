from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from agent.loop import HospitalAgentLoop
from config import Settings
from tools.backend_api import BackendApiError

logger = logging.getLogger(__name__)


class HospitalTelegramBot:
    def __init__(self, settings: Settings, *, agent: HospitalAgentLoop) -> None:
        self.settings = settings
        self.agent = agent

    def run(self) -> None:
        if not self.settings.telegram_bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is missing. Add it to hospital-agent/.env.")

        application = self._build_application()
        application.run_polling()

    def _build_application(self) -> Application:
        application = ApplicationBuilder().token(self.settings.telegram_bot_token).build()
        application.add_handler(CommandHandler("start", self._start))
        application.add_handler(CommandHandler("help", self._help))
        application.add_handler(CommandHandler("login", self._login))
        application.add_handler(CommandHandler("verify", self._verify))
        application.add_handler(CommandHandler("logout", self._logout))
        application.add_handler(CommandHandler("doctors", self._doctors))
        application.add_handler(CommandHandler("availability", self._availability))
        application.add_handler(CommandHandler("appointments", self._appointments))
        application.add_handler(CommandHandler("prescriptions", self._prescriptions))
        application.add_handler(CommandHandler("prescription", self._prescription))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._text))
        return application

    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(
            "Welcome to the hospital assistant.\n"
            "You can ask general hospital questions without login.\n"
            "For patient-specific actions like appointments or prescriptions, use `/login <email> <password>`.\n"
            "Then use `/verify <otp>` after you receive the email OTP.\n"
            "Use `/help` for commands."
        )

    async def _help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(
            "Public use:\n"
            "- ask hospital questions in normal text\n"
            "\n"
            "Protected patient actions:\n"
            "Commands:\n"
            "/login <email> <password>\n"
            "/verify <otp>\n"
            "/logout\n"
            "/doctors\n"
            "/availability <doctor_id>\n"
            "/appointments\n"
            "/prescriptions\n"
            "/prescription <appointment_id>\n"
            "\n"
            "You can also type: `show me doctors`, `doctor working hours`, `book appointment`, `cancel appointment`, `reschedule appointment`, or `show my prescription`."
        )

    async def _login(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if len(context.args) < 2:
            await update.effective_message.reply_text("Use `/login <email> <password>`.")
            return
        email = context.args[0]
        password = " ".join(context.args[1:])
        await self._safe_reply(update, self.agent.handle_login(update.effective_user.id, email, password))

    async def _verify(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if len(context.args) < 1:
            await update.effective_message.reply_text("Use `/verify <otp>`.")
            return
        otp = context.args[-1]
        email = context.args[0] if len(context.args) > 1 else None
        await self._safe_reply(update, self.agent.handle_verify(update.effective_user.id, otp, email))

    async def _logout(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(self.agent.handle_logout(update.effective_user.id))

    async def _doctors(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self._safe_reply(update, self.agent.handle_list_doctors(update.effective_user.id))

    async def _availability(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.effective_message.reply_text("Use `/availability <doctor_id>`.")
            return
        await self._safe_reply(update, self.agent.handle_availability(update.effective_user.id, context.args[0]))

    async def _appointments(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self._safe_reply(update, self.agent.handle_appointments(update.effective_user.id))

    async def _prescriptions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self._safe_reply(update, self.agent.handle_prescriptions(update.effective_user.id))

    async def _prescription(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.effective_message.reply_text("Use `/prescription <appointment_id>`.")
            return
        await self._safe_reply(
            update,
            self.agent.handle_prescription_by_appointment(update.effective_user.id, context.args[0]),
        )

    async def _text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_message or not update.effective_user:
            return
        message = update.effective_message.text or ""
        await self._safe_reply(update, self.agent.handle_text(update.effective_user.id, message))

    async def _safe_reply(self, update: Update, coro) -> None:
        try:
            reply = await coro
        except BackendApiError as error:
            reply = str(error)
        except Exception as error:  # pragma: no cover - defensive runtime handling
            logger.exception("Unhandled hospital-agent Telegram error: %s", error)
            reply = "Something went wrong in the hospital assistant. Please try again."
        await update.effective_message.reply_text(reply)
