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
        application.add_handler(MessageHandler(filters.CONTACT, self._contact))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._text))
        return application

    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(
            "Hi, I am the hospital assistant for patients.\n"
            "You can ask about hospital information, available doctors, doctor timings, and appointments.\n\n"
            "Try: show doctors, book appointment, show my appointments, or show my prescription.\n"
            "For booking, I can help existing patients login or new patients register first."
        )

    async def _help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(
            "You can type normally:\n"
            "- Show available doctors\n"
            "- Check doctor timings\n"
            "- Book appointment\n"
            "- Show my appointments\n"
            "- Cancel appointment\n"
            "- Reschedule appointment\n"
            "- Show my prescription\n\n"
            "For booking, say `book appointment`. I will ask whether you are an existing or new patient."
        )

    async def _login(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if len(context.args) < 2:
            await update.effective_message.reply_text(
                "Please send your patient email and password like this:\n"
                "/login your@email.com yourPassword"
            )
            return
        email = context.args[0]
        password = " ".join(context.args[1:])
        await self._safe_reply(update, self.agent.handle_login(update.effective_user.id, email, password))

    async def _verify(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if len(context.args) < 1:
            await update.effective_message.reply_text(
                "Please send the 6-digit code from your email. You can send only the code here."
            )
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
            await self._safe_reply(update, self.agent.handle_text(update.effective_user.id, "doctor timings"))
            return
        await self._safe_reply(update, self.agent.handle_availability(update.effective_user.id, " ".join(context.args)))

    async def _appointments(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self._safe_reply(update, self.agent.handle_appointments(update.effective_user.id))

    async def _prescriptions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self._safe_reply(update, self.agent.handle_prescriptions(update.effective_user.id))

    async def _prescription(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await self._safe_reply(update, self.agent.handle_prescriptions(update.effective_user.id))
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

    async def _contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_message or not update.effective_user or not update.effective_message.contact:
            return
        phone = update.effective_message.contact.phone_number or ""
        await self._safe_reply(update, self.agent.handle_text(update.effective_user.id, phone))

    async def _safe_reply(self, update: Update, coro) -> None:
        try:
            reply = await coro
        except BackendApiError as error:
            reply = self.agent.format_error(error)
        except Exception as error:  # pragma: no cover - defensive runtime handling
            logger.exception("Unhandled hospital-agent Telegram error: %s", error)
            reply = "Something went wrong in the hospital assistant. Please try again."
        await update.effective_message.reply_text(reply)
