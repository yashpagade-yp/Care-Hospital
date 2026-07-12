from __future__ import annotations

import logging
import re
from datetime import date, datetime, time, timedelta
from typing import Any

from agent.intents import Intent, detect_intent, normalize_intent_label
from agent.llm_client import GroqLlmClient, LlmClientError
from memory.long_term import LongTermMemory
from prompts.faq import answer_faq
from state.sqlite_store import SQLiteStore
from tools.backend_api import BackendApiClient, BackendApiError

logger = logging.getLogger(__name__)

DEFAULT_CONSULTATION_FEE = 0.0
DATE_TIME_FORMAT_HINT = "Please send the date and time like `2026-07-18 09:00`."

LANGUAGE_LABELS = {
    "english": "English",
    "hindi": "Hindi",
    "marathi": "Marathi",
}

SPECIALTY_KEYWORDS = {
    "General Medicine": {
        "general",
        "general physician",
        "physician",
        "family doctor",
        "fever",
        "cold",
        "cough",
        "diabetes",
        "bp",
        "blood pressure",
        "फिजिशियन",
        "सामान्य",
        "ताप",
        "खोकला",
        "बुखार",
        "सर्दी",
    },
    "Orthopedics": {
        "orthopedic",
        "orthopedics",
        "bone",
        "joint",
        "fracture",
        "back pain",
        "knee",
        "हाड",
        "जोड़",
        "हड्डी",
        "फ्रॅक्चर",
        "फ्रैक्चर",
        "कमर",
        "गुडघा",
    },
    "Dermatology": {
        "skin",
        "skincare",
        "skin care",
        "dermatology",
        "dermatologist",
        "acne",
        "rash",
        "hair",
        "त्वचा",
        "चर्म",
        "स्किन",
        "मुरुम",
        "दाने",
        "बाल",
        "केस",
    },
    "Pediatrics": {
        "child",
        "children",
        "kid",
        "baby",
        "pediatric",
        "pediatrics",
        "बच्चा",
        "बाळ",
        "लहान मुल",
        "मुलांचा",
    },
    "Cardiology": {
        "heart",
        "cardiology",
        "cardiologist",
        "chest pain",
        "दिल",
        "हृदय",
        "छाती",
    },
    "Neurology": {
        "neuro",
        "neurology",
        "neurologist",
        "headache",
        "migraine",
        "brain",
        "nerves",
        "डोकेदुखी",
        "सिरदर्द",
        "नस",
        "दिमाग",
    },
    "Gynecology": {
        "gynecology",
        "gynaecology",
        "gynecologist",
        "women",
        "pregnancy",
        "period",
        "महिला",
        "गर्भ",
        "प्रेग्नेंसी",
        "पीरियड",
    },
    "ENT": {
        "ent",
        "ear",
        "nose",
        "throat",
        "hearing",
        "कान",
        "नाक",
        "गला",
        "घसा",
    },
    "Ophthalmology": {
        "eye",
        "eyes",
        "vision",
        "ophthalmology",
        "ophthalmologist",
        "आंख",
        "डोळा",
        "नजर",
        "दृष्टी",
    },
}


class HospitalAgentLoop:
    def __init__(
        self,
        *,
        backend_client: BackendApiClient,
        store: SQLiteStore,
        long_term_memory: LongTermMemory,
        llm_client: GroqLlmClient,
    ) -> None:
        self.backend_client = backend_client
        self.store = store
        self.long_term_memory = long_term_memory
        self.llm_client = llm_client

    async def handle_text(self, telegram_user_id: int, message: str) -> str:
        message = message.strip()
        if not message:
            return self._default_help()

        flow: dict[str, Any] = {}
        language = "english"
        otp = self._extract_otp(message)
        if otp and self._pending_login_email(telegram_user_id):
            return await self.handle_verify(telegram_user_id, otp)

        self.store.add_short_term_memory(telegram_user_id, "user", message)
        conversation_history = self._build_recent_history(telegram_user_id)

        try:
            flow = self.store.get_flow_state(telegram_user_id)
            language = self._detect_language(message, flow)
            if flow:
                reply = await self._continue_flow(telegram_user_id, message, flow)
            else:
                intent = await self._detect_intent(message, conversation_history)
                if intent == Intent.DOCTOR_INFO:
                    reply = await self.handle_list_doctors(
                        telegram_user_id,
                        include_timings=self._asks_for_timings(message),
                        query=message,
                    )
                elif intent == Intent.REGISTER:
                    reply = (
                        self._registration_process_help()
                        if self._is_process_question(message)
                        else self._start_patient_registration(telegram_user_id)
                    )
                elif intent == Intent.APPOINTMENTS:
                    reply = await self.handle_appointments(telegram_user_id)
                elif intent == Intent.BOOK:
                    reply = await self._start_booking(telegram_user_id, query=message)
                elif intent == Intent.AVAILABILITY:
                    reply = self._start_availability(telegram_user_id)
                elif intent == Intent.CANCEL:
                    reply = await self._start_cancel(telegram_user_id)
                elif intent == Intent.RESCHEDULE:
                    reply = await self._start_reschedule(telegram_user_id)
                elif intent == Intent.PRESCRIPTION:
                    reply = await self._start_prescription_lookup(telegram_user_id)
                elif intent == Intent.FAQ:
                    reply = await self._answer_faq(telegram_user_id, message)
                else:
                    reply = await self._answer_general_query(telegram_user_id, message)
        except BackendApiError as error:
            if self._is_auth_error(error):
                self.store.clear_auth_session(telegram_user_id)
            reply = self.format_error(error)
            self.store.clear_flow_state(telegram_user_id)

        reply = await self._localize_reply(reply, language)
        self._remember_flow_language(telegram_user_id, language)
        self.store.add_short_term_memory(telegram_user_id, "assistant", reply)
        return reply

    async def handle_login(self, telegram_user_id: int, email: str, password: str) -> str:
        try:
            response = await self.backend_client.start_login(email=email, password=password)
        except BackendApiError as error:
            return self.format_error(error)
        self.store.set_pending_login(telegram_user_id, email.lower())
        return (
            "I sent a 6-digit verification code to your email.\n"
            f"Email: {response.get('email', email)}\n"
            "Please send the code here, for example: `123456`."
        )

    async def handle_verify(self, telegram_user_id: int, otp: str, email: str | None = None) -> str:
        pending_flow = self.store.get_flow_state(telegram_user_id)
        if not email:
            session = self.store.get_auth_session(telegram_user_id)
            email = session.get("pending_email") if session else None
        if not email:
            return (
                "I do not see a login in progress.\n"
                "Please login with your patient email first."
            )

        try:
            response = await self.backend_client.verify_login_otp(email=email, otp=otp)
        except BackendApiError as error:
            return self.format_error(error)

        user = response.get("user", {})
        role = (response.get("role") or user.get("role") or "").upper()
        if role != "PATIENT":
            self.store.clear_auth_session(telegram_user_id)
            self.store.clear_flow_state(telegram_user_id)
            return (
                "This Telegram assistant is only for patients.\n"
                "Please login with a patient account to book or manage appointments."
            )

        self.store.upsert_auth_session(
            telegram_user_id=telegram_user_id,
            email=email,
            patient_id=user.get("id"),
            role=role,
            access_token=response["access_token"],
            token_type=response.get("token_type", "bearer"),
        )
        self.store.clear_flow_state(telegram_user_id)
        if (
            pending_flow
            and pending_flow.get("active_intent") == Intent.BOOK.value
            and pending_flow.get("step") == "awaiting_login_otp"
        ):
            booking_message = await self._start_booking(telegram_user_id)
            return (
                "You are logged in as a patient.\n"
                f"Hello {user.get('name', 'there')}.\n\n"
                f"{booking_message}"
            )
        if (
            pending_flow
            and pending_flow.get("active_intent") == Intent.PRESCRIPTION.value
            and pending_flow.get("step") == "awaiting_login_otp"
        ):
            prescription_message = await self.handle_prescriptions(telegram_user_id)
            return (
                "You are logged in as a patient.\n"
                f"Hello {user.get('name', 'there')}.\n\n"
                f"{prescription_message}"
            )
        return (
            "You are logged in as a patient.\n"
            f"Hello {user.get('name', 'there')}.\n"
            "You can now book an appointment, see your appointments, cancel or reschedule, or view prescriptions."
        )

    def handle_logout(self, telegram_user_id: int) -> str:
        self.store.clear_auth_session(telegram_user_id)
        self.store.clear_flow_state(telegram_user_id)
        return "You have been logged out."

    async def handle_list_doctors(
        self,
        telegram_user_id: int,
        *,
        include_timings: bool = False,
        query: str = "",
    ) -> str:
        doctors = await self._load_doctors(telegram_user_id)
        if not doctors:
            return "No doctors are available right now. Please try again later."
        doctors, specialty = self._filter_doctors_for_message(query, doctors)

        self.store.set_flow_state(
            telegram_user_id,
            active_intent=Intent.AVAILABILITY.value,
            step="doctor_choice",
            payload={
                "doctor_options": doctors,
                "from_doctor_list": True,
                "specialty_filter": specialty,
            },
        )
        intro = (
            f"I found these {specialty} doctors for you:"
            if specialty
            else "Here are the available doctors:"
        )
        if include_timings:
            return (
                f"{intro}\n"
                f"{await self._format_doctor_options_with_timings(telegram_user_id, doctors)}\n\n"
                "To book, say `book appointment`."
            )
        return (
            f"{intro}\n"
            f"{self._format_doctor_options(doctors)}\n\n"
            "Reply with a doctor number to see timings, or say `book appointment` to start booking."
        )

    async def handle_availability(self, telegram_user_id: int, doctor_ref: str) -> str:
        doctors = await self._load_doctors(telegram_user_id)
        doctor, matches = self._resolve_doctor(doctor_ref, doctors)
        if doctor is None and matches:
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.AVAILABILITY.value,
                step="doctor_choice",
                payload={"doctor_options": matches},
            )
            return (
                "I found more than one matching doctor:\n"
                f"{self._format_doctor_options(matches)}\n\n"
                "Please reply with the doctor number."
            )
        if doctor is None:
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.AVAILABILITY.value,
                step="doctor_choice",
                payload={"doctor_options": doctors},
            )
            return (
                "I could not find that doctor.\n"
                "Please choose from this list:\n"
                f"{self._format_doctor_options(doctors)}"
            )

        return await self._doctor_availability_reply(telegram_user_id, doctor)

    async def handle_appointments(self, telegram_user_id: int) -> str:
        auth = self._require_patient_session(telegram_user_id)
        appointments = await self._load_patient_appointments(auth)
        if not appointments:
            return "You do not have any appointments yet."

        return (
            "Your appointments:\n"
            f"{self._format_appointment_options(appointments)}\n\n"
            "You can say `cancel appointment` or `reschedule appointment` if you need to make a change."
        )

    async def handle_prescriptions(self, telegram_user_id: int) -> str:
        auth = self._require_patient_session(telegram_user_id)
        response = await self.backend_client.list_patient_prescriptions(
            auth["access_token"],
            auth["patient_id"],
        )
        items = response.get("items", [])
        if not items:
            return "No prescriptions are available for your account yet."
        if len(items) == 1:
            self.store.clear_flow_state(telegram_user_id)
            return await self.handle_prescription_by_appointment(
                telegram_user_id,
                items[0]["appointment_id"],
            )

        self.store.set_flow_state(
            telegram_user_id,
            active_intent=Intent.PRESCRIPTION.value,
            step="appointment_choice",
            payload={"prescription_options": items},
        )
        return (
            "I found these prescriptions:\n"
            f"{self._format_prescription_options(items)}\n\n"
            "Reply with the visit number you want to open."
        )

    async def handle_prescription_by_appointment(self, telegram_user_id: int, appointment_ref: str) -> str:
        auth = self._require_patient_session(telegram_user_id)
        response = await self.backend_client.get_prescription_by_appointment(
            auth["access_token"],
            appointment_ref,
        )
        return self._format_prescription_detail(response)

    async def _start_booking(
        self,
        telegram_user_id: int,
        *,
        query: str = "",
        doctor_options: list[dict[str, Any]] | None = None,
        specialty_filter: str | None = None,
    ) -> str:
        doctors = doctor_options or await self._load_doctors(telegram_user_id)
        if not doctors:
            return "No doctors are available right now. Please try again later."
        if doctor_options is None:
            doctors, specialty_filter = self._filter_doctors_for_message(query, doctors)

        self.store.set_flow_state(
            telegram_user_id,
            active_intent=Intent.BOOK.value,
            step="doctor_choice",
            payload={"doctor_options": doctors, "specialty_filter": specialty_filter},
        )
        doctor_line = (
            f"Please choose a {specialty_filter} doctor:"
            if specialty_filter
            else "Please choose a doctor:"
        )
        return (
            "Of course, I can help you book an appointment.\n"
            "You do not need to register first.\n"
            f"{doctor_line}\n"
            f"{self._format_doctor_options(doctors)}\n\n"
            "You can reply with the doctor number, name, or specialty."
        )

    def _start_auth_choice(self, telegram_user_id: int) -> str:
        self.store.set_flow_state(
            telegram_user_id,
            active_intent=Intent.BOOK.value,
            step="auth_choice",
            payload={},
        )
        return (
            "I can help you book an appointment.\n"
            "Are you an existing patient or a new patient?\n\n"
            "Reply `existing` to login, or `new` to register first."
        )

    def _start_patient_registration(self, telegram_user_id: int) -> str:
        self.store.set_flow_state(
            telegram_user_id,
            active_intent=Intent.REGISTER.value,
            step="register_name",
            payload={},
        )
        return (
            "Sure, I can register the patient here in Telegram.\n"
            "Please send the patient's full name."
        )

    def _start_availability(self, telegram_user_id: int) -> str:
        self.store.set_flow_state(
            telegram_user_id,
            active_intent=Intent.AVAILABILITY.value,
            step="doctor_choice",
            payload={},
        )
        return "Which doctor or specialty do you want to check?"

    async def _start_cancel(self, telegram_user_id: int) -> str:
        auth = self._require_patient_session(telegram_user_id)
        appointments = self._manageable_appointments(await self._load_patient_appointments(auth))
        if not appointments:
            return "You do not have any upcoming appointments that can be cancelled."

        self.store.set_flow_state(
            telegram_user_id,
            active_intent=Intent.CANCEL.value,
            step="appointment_choice",
            payload={"appointment_options": appointments},
        )
        return (
            "Which appointment would you like to cancel?\n"
            f"{self._format_appointment_options(appointments)}\n\n"
            "Reply with the appointment number."
        )

    async def _start_reschedule(self, telegram_user_id: int) -> str:
        auth = self._require_patient_session(telegram_user_id)
        appointments = self._manageable_appointments(await self._load_patient_appointments(auth))
        if not appointments:
            return "You do not have any upcoming appointments that can be rescheduled."

        self.store.set_flow_state(
            telegram_user_id,
            active_intent=Intent.RESCHEDULE.value,
            step="appointment_choice",
            payload={"appointment_options": appointments},
        )
        return (
            "Which appointment would you like to reschedule?\n"
            f"{self._format_appointment_options(appointments)}\n\n"
            "Reply with the appointment number."
        )

    async def _start_prescription_lookup(self, telegram_user_id: int) -> str:
        if not self._get_patient_session(telegram_user_id):
            return self._start_patient_login(
                telegram_user_id,
                next_action=Intent.PRESCRIPTION.value,
            )
        try:
            return await self.handle_prescriptions(telegram_user_id)
        except BackendApiError as error:
            if not self._is_auth_error(error):
                raise
            self.store.clear_auth_session(telegram_user_id)
            return self._start_patient_login(
                telegram_user_id,
                next_action=Intent.PRESCRIPTION.value,
            )

    def _start_patient_login(self, telegram_user_id: int, *, next_action: str | None = None) -> str:
        self.store.set_flow_state(
            telegram_user_id,
            active_intent=Intent.PRESCRIPTION.value,
            step="login_email",
            payload={"next_action": next_action or Intent.PRESCRIPTION.value},
        )
        return (
            "Please login with your patient account to view prescriptions.\n"
            "Send your patient email address first."
        )

    async def _continue_flow(self, telegram_user_id: int, message: str, flow: dict[str, Any]) -> str:
        if self._is_cancel_word(message):
            self.store.clear_flow_state(telegram_user_id)
            return "No problem. I stopped the current request."

        switch_reply = await self._maybe_switch_flow(telegram_user_id, message, flow)
        if switch_reply is not None:
            return switch_reply

        intent = flow["active_intent"]
        step = flow["step"]
        payload = flow["payload"]

        if intent == Intent.AVAILABILITY.value:
            return await self._continue_availability(telegram_user_id, message, payload)
        if intent == Intent.PRESCRIPTION.value:
            return await self._continue_prescription(telegram_user_id, message, step, payload)
        if intent == Intent.REGISTER.value:
            return await self._continue_patient_registration(telegram_user_id, message, step, payload)
        if intent == Intent.CANCEL.value:
            return await self._continue_cancel(telegram_user_id, message, step, payload)
        if intent == Intent.RESCHEDULE.value:
            return await self._continue_reschedule(telegram_user_id, message, step, payload)
        if intent == Intent.BOOK.value:
            return await self._continue_booking(telegram_user_id, message, step, payload)

        self.store.clear_flow_state(telegram_user_id)
        return self._default_help()

    async def _continue_availability(
        self,
        telegram_user_id: int,
        message: str,
        payload: dict[str, Any],
    ) -> str:
        if detect_intent(message) == Intent.BOOK:
            self.store.clear_flow_state(telegram_user_id)
            return await self._start_booking(
                telegram_user_id,
                doctor_options=payload.get("doctor_options"),
                specialty_filter=payload.get("specialty_filter"),
            )

        doctors = payload.get("doctor_options") or await self._load_doctors(telegram_user_id)
        doctor, matches = self._resolve_doctor(message, doctors)
        if doctor is None and matches:
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.AVAILABILITY.value,
                step="doctor_choice",
                payload={"doctor_options": matches, "specialty_filter": payload.get("specialty_filter")},
            )
            return (
                "I found these matching doctors:\n"
                f"{self._format_doctor_options(matches)}\n\n"
                "Please reply with the doctor number."
            )
        if doctor is None:
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.AVAILABILITY.value,
                step="doctor_choice",
                payload={"doctor_options": doctors, "specialty_filter": payload.get("specialty_filter")},
            )
            if self._is_confusion_message(message):
                return (
                    "No problem. The list shows available doctors and their profile.\n"
                    "Reply with a doctor number to see timings, or say `book appointment` if you want to book."
                )
            return (
                "Please choose a doctor from this list:\n"
                f"{self._format_doctor_options(doctors)}"
            )

        self.store.clear_flow_state(telegram_user_id)
        return await self._doctor_availability_reply(telegram_user_id, doctor)

    async def _continue_patient_registration(
        self,
        telegram_user_id: int,
        message: str,
        step: str,
        payload: dict[str, Any],
    ) -> str:
        if step == "post_booking_offer":
            if self._is_yes(message) or detect_intent(message) == Intent.REGISTER:
                payload["name"] = payload.get("patient_name", "")
                self.store.set_flow_state(
                    telegram_user_id,
                    active_intent=Intent.REGISTER.value,
                    step="register_name" if not payload["name"] else "register_phone",
                    payload=payload,
                )
                if payload["name"]:
                    return (
                        f"I will register the patient as {payload['name']}.\n"
                        "Please send the patient's phone number."
                    )
                return "Please send the patient's full name."
            self.store.clear_flow_state(telegram_user_id)
            return (
                "No problem. The appointment is still booked.\n"
                "You can say `register` later if you want prescriptions and appointment history in the patient dashboard."
            )

        if step == "register_name":
            if len(message.strip()) < 2:
                return "Please send the patient's full name."
            payload["name"] = message.strip()
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.REGISTER.value,
                step="register_phone",
                payload=payload,
            )
            return "Please send the patient's phone number."

        if step == "register_phone":
            phone = self._normalize_phone(message)
            if not phone:
                return "Please send a valid phone number with at least 10 digits."
            payload["phone"] = phone
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.REGISTER.value,
                step="register_email",
                payload=payload,
            )
            return "Please send the patient's email address."

        if step == "register_email":
            email = message.strip().lower()
            if not self._looks_like_email(email):
                return "Please send a valid email address."
            payload["email"] = email
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.REGISTER.value,
                step="register_password",
                payload=payload,
            )
            return "Please create a password with at least 8 characters."

        if step == "register_password":
            password = message.strip()
            if len(password) < 8:
                return "Password must be at least 8 characters. Please send a stronger password."
            payload["password"] = password
            try:
                await self.backend_client.register_patient(
                    name=payload["name"],
                    phone=payload["phone"],
                    email=payload["email"],
                    password=password,
                )
            except BackendApiError as error:
                if "already exists" in str(error).lower():
                    self.store.clear_flow_state(telegram_user_id)
                    return (
                        "A patient account already exists for this email.\n"
                        "Please login with that account to view appointments and prescriptions."
                    )
                return self.format_error(error)
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.REGISTER.value,
                step="register_verify_otp",
                payload=payload,
            )
            return (
                "I created the patient account and sent a verification code to the email.\n"
                "Please send the code here."
            )

        if step == "register_verify_otp":
            otp = self._extract_otp(message)
            if not otp:
                return "Please send the verification code from your email."
            try:
                await self.backend_client.verify_patient_registration_otp(
                    email=payload["email"],
                    otp=otp,
                    telegram_guest_appointment_id=payload.get("telegram_guest_appointment_id"),
                    telegram_user_id=str(telegram_user_id),
                )
                await self.backend_client.start_login(
                    email=payload["email"],
                    password=payload["password"],
                )
            except BackendApiError as error:
                return self.format_error(error)
            self.store.set_pending_login(telegram_user_id, payload["email"])
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.REGISTER.value,
                step="awaiting_login_otp",
                payload={"email": payload["email"]},
            )
            return (
                "Your patient account is verified.\n"
                "I sent one more login code to your email so this Telegram chat can access the patient account securely.\n"
                "Please send that code here."
            )

        if step == "awaiting_login_otp":
            otp = self._extract_otp(message)
            if not otp:
                return "Please send the 6-digit login code from your email."
            return await self.handle_verify(telegram_user_id, otp, payload.get("email"))

        self.store.clear_flow_state(telegram_user_id)
        return self._default_help()

    async def _continue_booking(
        self,
        telegram_user_id: int,
        message: str,
        step: str,
        payload: dict[str, Any],
    ) -> str:
        legacy_auth_steps = {
            "auth_choice",
            "login_email",
            "login_password",
            "awaiting_login_otp",
            "register_name",
            "register_phone",
            "register_email",
            "register_password",
            "register_verify_otp",
        }
        if step in legacy_auth_steps:
            self.store.clear_flow_state(telegram_user_id)
            return (
                "Booking no longer needs login or registration in Telegram.\n\n"
                f"{await self._start_booking(telegram_user_id)}"
            )

        if step == "auth_choice":
            self.store.clear_flow_state(telegram_user_id)
            return await self._start_booking(telegram_user_id)

        if step == "login_email":
            email = message.strip().lower()
            if not self._looks_like_email(email):
                return "Please send a valid email address."
            payload["email"] = email
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.BOOK.value,
                step="login_password",
                payload=payload,
            )
            return "Please send your patient account password."

        if step == "login_password":
            if self._is_password_help_question(message):
                return (
                    "Yes. Please send the patient account password in one message.\n"
                    "After that, I will send a verification code to the registered email."
                )
            try:
                response = await self.backend_client.start_login(email=payload["email"], password=message.strip())
            except BackendApiError as error:
                return self.format_error(error)
            self.store.set_pending_login(telegram_user_id, payload["email"])
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.BOOK.value,
                step="awaiting_login_otp",
                payload={"email": payload["email"]},
            )
            login_reply = (
                "I sent a 6-digit verification code to your email.\n"
                f"Email: {response.get('email', payload['email'])}\n"
                "Please send the code here."
            )
            return f"{login_reply}\n\nAfter verification, I will continue your booking."

        if step == "awaiting_login_otp":
            otp = self._extract_otp(message)
            if not otp:
                return "Please send the 6-digit verification code from your email."
            return await self.handle_verify(telegram_user_id, otp, payload.get("email"))

        if step == "register_name":
            if len(message.strip()) < 2:
                return "Please send the patient's full name."
            payload["name"] = message.strip()
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.BOOK.value,
                step="register_phone",
                payload=payload,
            )
            return "Please send the patient's phone number. You can type it or share your Telegram contact."

        if step == "register_phone":
            phone = self._normalize_phone(message)
            if not phone:
                return "Please send a valid phone number with at least 10 digits."
            payload["phone"] = phone
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.BOOK.value,
                step="register_email",
                payload=payload,
            )
            return "Please send the patient's email address."

        if step == "register_email":
            email = message.strip().lower()
            if not self._looks_like_email(email):
                return "Please send a valid email address."
            payload["email"] = email
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.BOOK.value,
                step="register_password",
                payload=payload,
            )
            return "Please create a password with at least 8 characters."

        if step == "register_password":
            password = message.strip()
            if len(password) < 8:
                return "Password must be at least 8 characters. Please send a stronger password."
            payload["password"] = password
            try:
                await self.backend_client.register_patient(
                    name=payload["name"],
                    phone=payload["phone"],
                    email=payload["email"],
                    password=password,
                )
            except BackendApiError as error:
                if "already exists" in str(error).lower():
                    self.store.set_flow_state(
                        telegram_user_id,
                        active_intent=Intent.BOOK.value,
                        step="login_email",
                        payload={},
                    )
                    return "A patient account already exists for this email. Please send your email to login."
                return self.format_error(error)
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.BOOK.value,
                step="register_verify_otp",
                payload=payload,
            )
            return (
                "I created the patient account and sent a verification code to the email.\n"
                "Please send the code here."
            )

        if step == "register_verify_otp":
            otp = self._extract_otp(message)
            if not otp:
                return "Please send the verification code from your email."
            try:
                await self.backend_client.verify_patient_registration_otp(
                    email=payload["email"],
                    otp=otp,
                )
                await self.backend_client.start_login(
                    email=payload["email"],
                    password=payload["password"],
                )
            except BackendApiError as error:
                return self.format_error(error)
            self.store.set_pending_login(telegram_user_id, payload["email"])
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.BOOK.value,
                step="awaiting_login_otp",
                payload={"email": payload["email"]},
            )
            return (
                "Your patient account is verified.\n"
                "I sent one more login code to your email so we can securely book the appointment.\n"
                "Please send that code here."
            )

        if step == "doctor_choice":
            doctors = payload.get("doctor_options") or await self._load_doctors(telegram_user_id)
            doctor, matches = self._resolve_doctor(message, doctors)
            if doctor is None and matches:
                self.store.set_flow_state(
                    telegram_user_id,
                    active_intent=Intent.BOOK.value,
                    step="doctor_choice",
                    payload={"doctor_options": matches, "specialty_filter": payload.get("specialty_filter")},
                )
                return (
                    "I found these matching doctors:\n"
                    f"{self._format_doctor_options(matches)}\n\n"
                    "Please reply with the doctor number."
                )
            if doctor is None:
                return (
                    "I could not match that doctor.\n"
                    f"{self._format_doctor_options(doctors)}\n\n"
                    "Please reply with a doctor number, name, or specialty."
                )

            payload["doctor"] = doctor
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.BOOK.value,
                step="datetime",
                payload=payload,
            )
            availability_text = await self._doctor_availability_summary(telegram_user_id, doctor)
            return (
                f"You selected {doctor.get('name', 'the doctor')}.\n"
                f"{availability_text}\n\n"
                f"{DATE_TIME_FORMAT_HINT}"
            )

        if step == "datetime":
            try:
                date_time = self._parse_patient_datetime(
                    message,
                    base_date=payload.get("pending_date"),
                )
            except BackendApiError as error:
                if str(error) == "missing_time":
                    patient_date = self._parse_patient_date(message)
                    if patient_date:
                        payload["pending_date"] = patient_date.isoformat()
                        self.store.set_flow_state(
                            telegram_user_id,
                            active_intent=Intent.BOOK.value,
                            step="datetime",
                            payload=payload,
                        )
                    return "What time should I book for that date? Example: `10:00 AM`."
                if str(error) == "missing_date":
                    return "Please send the appointment date also. Example: `13 July 2026 10:00 AM`."
                if str(error) == "invalid_datetime":
                    return (
                        "Please send both date and time for the appointment.\n"
                        "Example: `13 July 2026 10:00 AM` or `2026-07-13 10:00 AM`."
                    )
                raise
            doctor = payload["doctor"]
            payload["date_time"] = date_time
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.BOOK.value,
                step="patient_name",
                payload=payload,
            )
            return (
                "That timing works.\n"
                "Please send the patient's full name."
            )

        if step == "patient_name":
            if len(message) < 2:
                return "Please send the patient's full name."
            payload["patient_name"] = message
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.BOOK.value,
                step="patient_age",
                payload=payload,
            )
            return "Please send the patient's age."

        if step == "patient_age":
            age = self._parse_age(message)
            if age is None:
                return "Please send a valid age between 0 and 120."
            payload["patient_age"] = age
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.BOOK.value,
                step="patient_gender",
                payload=payload,
            )
            return "Please send the patient's gender."

        if step == "patient_gender":
            if not message.strip():
                return "Please send the patient's gender."
            payload["patient_gender"] = message.strip()
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.BOOK.value,
                step="blood_group",
                payload=payload,
            )
            return "Please send the patient's blood group. You can type `skip` if not known."

        if step == "blood_group":
            if message.lower() != "skip":
                payload["patient_blood_group"] = message.strip()
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.BOOK.value,
                step="confirm",
                payload=payload,
            )
            return self._booking_review_message(payload)

        if step == "confirm":
            if not self._is_yes(message):
                self.store.clear_flow_state(telegram_user_id)
                return "Okay, I did not book the appointment."

            request_payload = {
                "telegram_user_id": str(telegram_user_id),
                "doctor_id": self._doctor_id(payload["doctor"]),
                "date_time": payload["date_time"],
                "patient_name": payload["patient_name"],
                "patient_age": payload["patient_age"],
                "patient_gender": payload["patient_gender"],
                "fee": float(payload.get("fee", DEFAULT_CONSULTATION_FEE)),
            }
            if payload.get("patient_blood_group"):
                request_payload["patient_blood_group"] = payload["patient_blood_group"]

            response = await self.backend_client.create_telegram_guest_appointment(request_payload)
            appointment = response.get("appointment", {})
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.REGISTER.value,
                step="post_booking_offer",
                payload={
                    "telegram_guest_appointment_id": appointment.get("id"),
                    "telegram_user_id": str(telegram_user_id),
                    "patient_name": payload["patient_name"],
                },
            )
            return (
                "Your appointment is booked.\n"
                f"Doctor: {response.get('doctor_name') or payload['doctor'].get('name', '-')}\n"
                f"Date and time: {self._format_datetime(appointment.get('date_time') or payload['date_time'])}\n"
                f"{self._format_queue_line(appointment)}\n"
                "Payment: mock payment completed.\n\n"
                "To view prescriptions and appointment history later, please register.\n"
                "Would you like to register now? Reply `yes` or `no`."
            )

        self.store.clear_flow_state(telegram_user_id)
        return self._default_help()

    async def _continue_cancel(
        self,
        telegram_user_id: int,
        message: str,
        step: str,
        payload: dict[str, Any],
    ) -> str:
        if step == "appointment_choice":
            appointment = self._resolve_appointment(message, payload.get("appointment_options", []))
            if appointment is None:
                return (
                    "Please choose an appointment number from this list:\n"
                    f"{self._format_appointment_options(payload.get('appointment_options', []))}"
                )
            payload["appointment"] = appointment
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.CANCEL.value,
                step="reason",
                payload=payload,
            )
            return "Please tell me the reason for cancelling."

        auth = self._require_patient_session(telegram_user_id)
        response = await self.backend_client.cancel_appointment(
            auth["access_token"],
            payload["appointment"]["id"],
            message.strip(),
        )
        self.store.clear_flow_state(telegram_user_id)
        return (
            "Your appointment has been cancelled.\n"
            f"Doctor: {response.get('doctor_name') or payload['appointment'].get('doctor_name', '-')}\n"
            f"Date and time: {self._format_datetime(response.get('date_time') or payload['appointment'].get('date_time'))}"
        )

    async def _continue_reschedule(
        self,
        telegram_user_id: int,
        message: str,
        step: str,
        payload: dict[str, Any],
    ) -> str:
        if step == "appointment_choice":
            appointment = self._resolve_appointment(message, payload.get("appointment_options", []))
            if appointment is None:
                return (
                    "Please choose an appointment number from this list:\n"
                    f"{self._format_appointment_options(payload.get('appointment_options', []))}"
                )
            payload["appointment"] = appointment
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.RESCHEDULE.value,
                step="new_datetime",
                payload=payload,
            )
            return (
                "Please send the new preferred date and time.\n"
                f"{DATE_TIME_FORMAT_HINT}"
            )

        if step == "new_datetime":
            try:
                payload["new_date_time"] = self._parse_patient_datetime(
                    message,
                    base_date=payload.get("pending_date"),
                )
            except BackendApiError as error:
                if str(error) == "missing_time":
                    patient_date = self._parse_patient_date(message)
                    if patient_date:
                        payload["pending_date"] = patient_date.isoformat()
                        self.store.set_flow_state(
                            telegram_user_id,
                            active_intent=Intent.RESCHEDULE.value,
                            step="new_datetime",
                            payload=payload,
                        )
                    return "What time should I reschedule it to? Example: `10:00 AM`."
                if str(error) == "missing_date":
                    return "Please send the new date also. Example: `13 July 2026 10:00 AM`."
                if str(error) == "invalid_datetime":
                    return (
                        "Please send both date and time for rescheduling.\n"
                        "Example: `13 July 2026 10:00 AM`."
                    )
                raise
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.RESCHEDULE.value,
                step="reason",
                payload=payload,
            )
            return "Reason for rescheduling is optional. Send it now, or type `skip`."

        auth = self._require_patient_session(telegram_user_id)
        reason = None if message.strip().lower() == "skip" else message.strip()
        response = await self.backend_client.reschedule_appointment(
            auth["access_token"],
            payload["appointment"]["id"],
            payload["new_date_time"],
            reason,
        )
        self.store.clear_flow_state(telegram_user_id)
        new = response.get("new_appointment", {})
        return (
            "Your appointment has been rescheduled.\n"
            f"Doctor: {new.get('doctor_name') or payload['appointment'].get('doctor_name', '-')}\n"
            f"New date and time: {self._format_datetime(new.get('date_time') or payload['new_date_time'])}"
        )

    async def _continue_prescription(
        self,
        telegram_user_id: int,
        message: str,
        step: str,
        payload: dict[str, Any],
    ) -> str:
        if step == "login_email":
            email = self._extract_email(message)
            if not email:
                return "Please send a valid patient email address."
            payload["email"] = email
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.PRESCRIPTION.value,
                step="login_password",
                payload=payload,
            )
            return "Please send your patient account password."

        if step == "login_password":
            password = message.strip()
            if not password:
                return "Please send your patient account password."
            try:
                response = await self.backend_client.start_login(
                    email=payload["email"],
                    password=password,
                )
            except BackendApiError as error:
                return self.format_error(error)
            self.store.set_pending_login(telegram_user_id, payload["email"])
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.PRESCRIPTION.value,
                step="awaiting_login_otp",
                payload={"email": payload["email"]},
            )
            return (
                "I sent a 6-digit login code to your email.\n"
                f"Email: {response.get('email', payload['email'])}\n"
                "Please send the code here."
            )

        if step == "awaiting_login_otp":
            otp = self._extract_otp(message)
            if not otp:
                return "Please send the 6-digit login code from your email."
            login_reply = await self.handle_verify(telegram_user_id, otp, payload.get("email"))
            if "You are logged in as a patient" not in login_reply:
                return login_reply
            prescription_reply = await self.handle_prescriptions(telegram_user_id)
            return f"{login_reply}\n\n{prescription_reply}"

        options = payload.get("prescription_options", [])
        selected = self._resolve_prescription(message, options)
        if selected is None:
            return (
                "Please choose one of these visits:\n"
                f"{self._format_prescription_options(options)}"
            )

        self.store.clear_flow_state(telegram_user_id)
        return await self.handle_prescription_by_appointment(
            telegram_user_id,
            selected["appointment_id"],
        )

    async def _maybe_switch_flow(
        self,
        telegram_user_id: int,
        message: str,
        flow: dict[str, Any],
    ) -> str | None:
        intent = await self._detect_intent(message, self._build_recent_history(telegram_user_id))
        if intent in {Intent.UNKNOWN, Intent.FAQ}:
            return None

        active_intent = flow["active_intent"]
        step = flow["step"]
        if intent.value == active_intent:
            return None

        protected_steps = {
            "auth_choice",
            "login_email",
            "login_password",
            "awaiting_login_otp",
            "register_name",
            "register_phone",
            "register_email",
            "register_password",
            "register_verify_otp",
            "post_booking_offer",
            "patient_phone",
            "patient_age",
            "patient_gender",
            "visit_reason",
            "blood_group",
            "confirm",
            "reason",
            "new_datetime",
        }
        if step in protected_steps:
            return None

        self.store.clear_flow_state(telegram_user_id)
        if intent == Intent.PRESCRIPTION:
            return await self._start_prescription_lookup(telegram_user_id)
        if intent == Intent.APPOINTMENTS:
            return await self.handle_appointments(telegram_user_id)
        if intent == Intent.DOCTOR_INFO:
            return await self.handle_list_doctors(
                telegram_user_id,
                include_timings=self._asks_for_timings(message),
                query=message,
            )
        if intent == Intent.BOOK:
            payload = flow.get("payload") or {}
            doctor_options = payload.get("doctor_options") if active_intent == Intent.AVAILABILITY.value else None
            return await self._start_booking(
                telegram_user_id,
                query=message,
                doctor_options=doctor_options,
                specialty_filter=payload.get("specialty_filter"),
            )
        if intent == Intent.REGISTER:
            return (
                self._registration_process_help()
                if self._is_process_question(message)
                else self._start_patient_registration(telegram_user_id)
            )
        if intent == Intent.AVAILABILITY:
            return self._start_availability(telegram_user_id)
        if intent == Intent.CANCEL:
            return await self._start_cancel(telegram_user_id)
        if intent == Intent.RESCHEDULE:
            return await self._start_reschedule(telegram_user_id)
        return None

    async def _answer_faq(self, telegram_user_id: int, message: str) -> str:
        memory_note = self.long_term_memory.build_context()
        conversation_history = self._build_recent_history(telegram_user_id)
        if self.llm_client.enabled:
            try:
                return await self.llm_client.answer_general_query(
                    user_message=message,
                    memory_hint=memory_note,
                    conversation_history=conversation_history,
                )
            except LlmClientError as error:
                logger.warning("Groq FAQ generation failed, using local FAQ fallback: %s", error)
        return answer_faq(message)

    def _default_help(self) -> str:
        return (
            "I can help patients with hospital information, available doctors, appointments, and prescriptions.\n"
            "You can type things like:\n"
            "- Show available doctors\n"
            "- Book appointment\n"
            "- Show my appointments\n"
            "- Cancel appointment\n"
            "- Show my prescription"
        )

    def _registration_process_help(self) -> str:
        return (
            "For Telegram appointment booking, registration is not needed.\n"
            "I only ask basic details and book the appointment.\n\n"
            "Registration/login is needed later in the web app for private things like prescriptions and appointment history."
        )

    def _existing_login_help(self) -> str:
        return (
            "For existing patient login:\n"
            "1. Send your patient email\n"
            "2. Send your password\n"
            "3. Send the email verification code\n\n"
            "Please send your patient email address now."
        )

    async def _answer_general_query(self, telegram_user_id: int, message: str) -> str:
        memory_note = self.long_term_memory.build_context()
        conversation_history = self._build_recent_history(telegram_user_id)
        if self.llm_client.enabled:
            try:
                return await self.llm_client.answer_general_query(
                    user_message=message,
                    memory_hint=memory_note,
                    conversation_history=conversation_history,
                )
            except LlmClientError as error:
                logger.warning("Groq general response generation failed, using default help: %s", error)
        return self._default_help()

    async def _detect_intent(self, message: str, conversation_history: str) -> Intent:
        if self._is_social_identity_message(message):
            return Intent.FAQ
        heuristic_intent = detect_intent(message)
        if heuristic_intent != Intent.UNKNOWN:
            return heuristic_intent
        if not self.llm_client.enabled:
            return Intent.UNKNOWN
        try:
            llm_label = await self.llm_client.classify_intent(
                message,
                conversation_history=conversation_history,
            )
            return normalize_intent_label(llm_label)
        except LlmClientError as error:
            logger.warning("Groq intent classification failed, using unknown intent: %s", error)
            return Intent.UNKNOWN

    def _detect_language(self, message: str, flow: dict[str, Any] | None = None) -> str:
        payload = (flow or {}).get("payload") or {}
        text = message.strip().lower()
        if not text:
            return payload.get("language", "english")

        devanagari_count = sum(1 for char in message if "\u0900" <= char <= "\u097f")
        if devanagari_count:
            marathi_markers = {
                "आहे",
                "मला",
                "माझ",
                "तुम्ही",
                "काय",
                "डॉक्टर",
                "रुग्ण",
                "भेट",
                "करायची",
                "सांगा",
                "पाहिजे",
            }
            hindi_markers = {
                "है",
                "मुझे",
                "मेरा",
                "आप",
                "क्या",
                "अस्पताल",
                "मरीज",
                "करना",
                "बताओ",
                "चाहिए",
            }
            marathi_score = sum(1 for word in marathi_markers if word in text)
            hindi_score = sum(1 for word in hindi_markers if word in text)
            return "marathi" if marathi_score >= hindi_score else "hindi"

        if any(word in text for word in {"namaste", "mujhe", "mera", "hai", "doctor chahiye", "dard"}):
            return "hindi"
        if any(word in text for word in {"mala", "majha", "aahe", "pahije", "sanga", "doctor hava"}):
            return "marathi"
        return payload.get("language", "english")

    async def _localize_reply(self, reply: str, language: str) -> str:
        if language == "english" or language not in LANGUAGE_LABELS:
            return reply
        if self.llm_client.enabled:
            try:
                return await self.llm_client.localize_reply(reply=reply, language=language)
            except LlmClientError as error:
                logger.warning("Groq reply localization failed, using English reply: %s", error)
        return reply

    def _remember_flow_language(self, telegram_user_id: int, language: str) -> None:
        if language not in LANGUAGE_LABELS:
            return
        flow = self.store.get_flow_state(telegram_user_id)
        if not flow:
            return
        payload = flow.get("payload") or {}
        if payload.get("language") == language:
            return
        payload["language"] = language
        self.store.set_flow_state(
            telegram_user_id,
            active_intent=flow["active_intent"],
            step=flow["step"],
            payload=payload,
        )

    def _filter_doctors_for_message(
        self,
        message: str,
        doctors: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], str | None]:
        specialty = self._specialty_from_message(message)
        if not specialty or self._asks_for_all_doctors(message):
            return doctors, None

        filtered = [
            doctor
            for doctor in doctors
            if specialty.lower() in str(doctor.get("specialty") or "").lower()
        ]
        return (filtered or doctors), specialty if filtered else None

    def _specialty_from_message(self, message: str) -> str | None:
        text = message.lower()
        if not text:
            return None
        for specialty, keywords in SPECIALTY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return specialty
        return None

    def _asks_for_all_doctors(self, message: str) -> bool:
        lowered = message.lower()
        return any(
            phrase in lowered
            for phrase in {
                "all doctors",
                "whole doctor list",
                "full doctor list",
                "list all",
                "सभी डॉक्टर",
                "सारे डॉक्टर",
                "सगळे डॉक्टर",
                "सर्व डॉक्टर",
            }
        )

    def _is_social_identity_message(self, message: str) -> bool:
        lowered = message.lower()
        return any(
            phrase in lowered
            for phrase in {
                "remember me",
                "do you know me",
                "who am i",
                "i am ",
                "my name is",
                "mujhe yaad",
                "mala aathav",
            }
        )

    def _require_patient_session(self, telegram_user_id: int) -> dict[str, Any]:
        session = self._get_patient_session(telegram_user_id)
        if not session or not session.get("access_token"):
            raise BackendApiError("patient_login_required")
        return session

    def _get_patient_session(self, telegram_user_id: int) -> dict[str, Any]:
        session = self.store.get_auth_session(telegram_user_id)
        if session and (session.get("role") or "").upper() == "PATIENT" and session.get("access_token"):
            return session
        return {}

    def _pending_login_email(self, telegram_user_id: int) -> str | None:
        session = self.store.get_auth_session(telegram_user_id)
        return session.get("pending_email") if session else None

    async def _load_doctors(self, telegram_user_id: int) -> list[dict[str, Any]]:
        response = await self.backend_client.list_public_doctors()
        return response.get("items", [])

    async def _load_patient_appointments(self, auth: dict[str, Any]) -> list[dict[str, Any]]:
        response = await self.backend_client.list_patient_appointments(
            auth["access_token"],
            auth["patient_id"],
        )
        return response.get("items", [])

    async def _doctor_availability_reply(self, telegram_user_id: int, doctor: dict[str, Any]) -> str:
        summary = await self._doctor_availability_summary(telegram_user_id, doctor)
        return (
            f"Here are the available timings for {doctor.get('name', 'this doctor')}:\n"
            f"{summary}\n\n"
            "If this works for you, say `book appointment`."
        )

    async def _doctor_availability_summary(self, telegram_user_id: int, doctor: dict[str, Any]) -> str:
        session = self._get_patient_session(telegram_user_id)
        doctor_id = self._doctor_id(doctor)
        if session:
            try:
                availability = await self.backend_client.get_doctor_availability(session["access_token"], doctor_id)
                booked = await self.backend_client.get_doctor_booked_slots(session["access_token"], doctor_id)
            except BackendApiError as error:
                if not self._is_auth_error(error):
                    raise
                self.store.clear_auth_session(telegram_user_id)
                availability = await self.backend_client.get_public_doctor_availability(doctor_id)
                booked = {"items": []}
        else:
            availability = await self.backend_client.get_public_doctor_availability(doctor_id)
            booked = {"items": []}

        entries = availability.get("items", availability) if isinstance(availability, dict) else availability
        if not isinstance(entries, list) or not entries:
            return "No working hours are listed right now."

        lines: list[str] = []
        for entry in entries[:10]:
            availability_type = str(entry.get("availability_type", "")).upper()
            start = self._format_time(entry.get("start_time"))
            end = self._format_time(entry.get("end_time"))
            if availability_type == "RECURRING":
                day = self._title_value(entry.get("day_of_week"))
                lines.append(f"- {day}: {start} to {end}")
            elif availability_type == "EXCEPTION_AVAILABLE":
                lines.append(f"- Special availability on {entry.get('exception_date')}: {start} to {end}")
            elif availability_type == "EXCEPTION_BLOCKED":
                lines.append(f"- Not available on {entry.get('exception_date')}: {start} to {end}")

        booked_items = booked.get("items", []) if isinstance(booked, dict) else []
        if session and booked_items:
            formatted_booked = ", ".join(self._format_datetime(item) for item in booked_items[:5])
            lines.append(f"Already booked slots: {formatted_booked}")
        return "\n".join(lines) if lines else "No working hours are listed right now."

    def _format_doctor_options(self, doctors: list[dict[str, Any]]) -> str:
        lines: list[str] = []
        for index, doctor in enumerate(doctors, start=1):
            specialty = doctor.get("specialty") or "General"
            qualification = doctor.get("qualification") or "Qualification not listed"
            experience = doctor.get("experience_years")
            experience_text = f"{experience} years experience" if experience is not None else "experience not listed"
            services = self._doctor_services(doctor)
            services_text = f" Services: {', '.join(services[:4])}." if services else ""
            lines.append(
                f"{index}. {doctor.get('name', 'Doctor')} - {specialty}, {qualification}, {experience_text}.{services_text}"
            )
        return "\n".join(lines)

    async def _format_doctor_options_with_timings(
        self,
        telegram_user_id: int,
        doctors: list[dict[str, Any]],
    ) -> str:
        blocks: list[str] = []
        for index, doctor in enumerate(doctors, start=1):
            profile = self._format_doctor_options([doctor]).replace("1.", f"{index}.", 1)
            timings = await self._doctor_availability_summary(telegram_user_id, doctor)
            blocks.append(f"{profile}\nTimings:\n{timings}")
        return "\n\n".join(blocks)

    def _format_appointment_options(self, appointments: list[dict[str, Any]]) -> str:
        lines: list[str] = []
        for index, item in enumerate(appointments[:10], start=1):
            doctor = item.get("doctor_name") or "Doctor"
            status = self._title_value(item.get("status"))
            queue = self._format_queue_line(item)
            lines.append(f"{index}. {doctor} - {self._format_datetime(item.get('date_time'))} - {status} - {queue}")
        return "\n".join(lines)

    def _format_prescription_options(self, prescriptions: list[dict[str, Any]]) -> str:
        lines: list[str] = []
        for index, item in enumerate(prescriptions[:10], start=1):
            doctor = item.get("doctor_name") or "Doctor"
            reason = item.get("visit_reason") or "Visit"
            created_at = self._format_datetime(item.get("created_at"))
            lines.append(f"{index}. {doctor} - {reason} - {created_at}")
        return "\n".join(lines)

    def _format_prescription_detail(self, response: dict[str, Any]) -> str:
        medicines = response.get("medicines", [])
        medicine_lines = "\n".join(f"- {medicine}" for medicine in medicines) if medicines else "- No medicines listed"
        notes = response.get("notes") or "No notes listed"
        return (
            "Prescription details:\n"
            f"Doctor: {response.get('doctor_name', '-')}\n"
            f"Visit reason: {response.get('visit_reason', '-')}\n"
            f"Medicines:\n{medicine_lines}\n"
            f"Notes: {notes}\n\n"
            "Please contact the hospital or your doctor before changing any medicine."
        )

    def _booking_review_message(self, payload: dict[str, Any]) -> str:
        doctor = payload["doctor"]
        lines = [
            "Please confirm the appointment details:",
            f"Doctor: {doctor.get('name', '-')}",
            f"Date and time: {self._format_datetime(payload.get('date_time'))}",
            f"Patient: {payload.get('patient_name', '-')}",
            f"Age: {payload.get('patient_age', '-')}",
            f"Gender: {payload.get('patient_gender', '-')}",
        ]
        if payload.get("patient_blood_group"):
            lines.append(f"Blood group: {payload['patient_blood_group']}")
        lines.append("")
        lines.append("Reply `yes` to confirm, or `no` to cancel.")
        return "\n".join(lines)

    def _resolve_doctor(
        self,
        raw_value: str,
        doctors: list[dict[str, Any]],
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        value = raw_value.strip().lower()
        if not value:
            return None, []

        if value.isdigit():
            index = int(value) - 1
            if 0 <= index < len(doctors):
                return doctors[index], []

        exact_id = [doctor for doctor in doctors if self._doctor_id(doctor).lower() == value]
        if exact_id:
            return exact_id[0], []

        matches = []
        for doctor in doctors:
            searchable_parts = [
                str(part or "")
                for part in (
                    doctor.get("name"),
                    doctor.get("specialty"),
                    doctor.get("qualification"),
                    " ".join(self._doctor_services(doctor)),
                )
            ]
            searchable = " ".join(
                searchable_parts
            ).lower()
            if value in searchable or any(part.strip().lower() and part.strip().lower() in value for part in searchable_parts):
                matches.append(doctor)

        if len(matches) == 1:
            return matches[0], []
        return None, matches

    def _doctor_services(self, doctor: dict[str, Any]) -> list[str]:
        services = doctor.get("services") or []
        if isinstance(services, list):
            return [str(service) for service in services if str(service).strip()]
        if isinstance(services, str):
            return [part.strip() for part in re.split(r"[,;]", services) if part.strip()]
        return []

    def _resolve_appointment(
        self,
        raw_value: str,
        appointments: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        value = raw_value.strip().lower()
        if value.isdigit():
            index = int(value) - 1
            if 0 <= index < len(appointments):
                return appointments[index]
        for appointment in appointments:
            if str(appointment.get("id", "")).lower() == value:
                return appointment
        return None

    def _resolve_prescription(
        self,
        raw_value: str,
        prescriptions: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        value = raw_value.strip().lower()
        if value.isdigit():
            index = int(value) - 1
            if 0 <= index < len(prescriptions):
                return prescriptions[index]
        for prescription in prescriptions:
            if str(prescription.get("appointment_id", "")).lower() == value:
                return prescription
        return None

    def _manageable_appointments(self, appointments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            appointment
            for appointment in appointments
            if str(appointment.get("status", "")).upper() == "CONFIRMED"
        ]

    def _parse_patient_datetime(self, value: str, *, base_date: str | None = None) -> str:
        patient_date = self._parse_patient_date(value)
        patient_time = self._parse_patient_time(value)

        if patient_date and patient_time:
            return datetime.combine(patient_date, patient_time).isoformat()
        if patient_date and not patient_time:
            raise BackendApiError("missing_time")
        if patient_time and base_date:
            return datetime.combine(date.fromisoformat(base_date), patient_time).isoformat()
        if patient_time and not patient_date:
            raise BackendApiError("missing_date")

        raise BackendApiError("invalid_datetime")

    def _parse_patient_date(self, value: str) -> date | None:
        text = self._clean_datetime_text(value)
        text_without_time = self._remove_time_text(text)

        for candidate in self._date_candidates(text_without_time):
            for fmt in (
                "%Y-%m-%d",
                "%d-%m-%Y",
                "%d-%m-%y",
                "%d %B %Y",
                "%d %b %Y",
                "%B %d %Y",
                "%b %d %Y",
            ):
                try:
                    return datetime.strptime(candidate, fmt).date()
                except ValueError:
                    continue

        weekday = self._weekday_from_text(text)
        if weekday is not None:
            today = datetime.now().date()
            days_ahead = (weekday - today.weekday()) % 7
            return today + timedelta(days=days_ahead)
        return None

    def _parse_patient_time(self, value: str) -> time | None:
        text = self._clean_datetime_text(value)
        range_match = re.search(
            r"\b([01]?\d|2[0-3])(?::([0-5]\d))\s*(am|pm)?\s*(?:to|-)\s*([01]?\d|2[0-3])(?::([0-5]\d))?\s*(am|pm)?\b",
            text,
            flags=re.IGNORECASE,
        )
        if range_match:
            return self._build_time(
                range_match.group(1),
                range_match.group(2) or "00",
                range_match.group(3) or range_match.group(6),
            )

        match = re.search(
            r"\b([01]?\d|2[0-3]):([0-5]\d)\s*(am|pm)?\b",
            text,
            flags=re.IGNORECASE,
        )
        if match:
            return self._build_time(match.group(1), match.group(2), match.group(3))

        match = re.search(r"\b(1[0-2]|0?[1-9])\s*(am|pm)\b", text, flags=re.IGNORECASE)
        if match:
            return self._build_time(match.group(1), "00", match.group(2))
        return None

    def _clean_datetime_text(self, value: str) -> str:
        text = value.strip().lower()
        text = text.replace("/", "-")
        text = re.sub(r"\b(\d{1,2})(st|nd|rd|th)\b", r"\1", text)
        text = re.sub(r"\b(date is|date|on|for|at|of)\b", " ", text)
        text = re.sub(r"[,\.]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _remove_time_text(self, value: str) -> str:
        text = re.sub(
            r"\b([01]?\d|2[0-3])\s*(?:[:]\s*([0-5]\d))?\s*(am|pm)\b",
            " ",
            value,
            flags=re.IGNORECASE,
        )
        text = re.sub(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", " ", text)
        text = re.sub(r"\bto\b\s+\d{1,2}(?::\d{2})?\s*(am|pm)?", " ", text, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", text).strip()

    def _date_candidates(self, text: str) -> list[str]:
        candidates = [text]
        patterns = [
            r"\b\d{4}-\d{1,2}-\d{1,2}\b",
            r"\b\d{1,2}-\d{1,2}-\d{2,4}\b",
            r"\b\d{1,2}\s+[a-z]+\s+\d{4}\b",
            r"\b[a-z]+\s+\d{1,2}\s+\d{4}\b",
        ]
        for pattern in patterns:
            candidates.extend(re.findall(pattern, text, flags=re.IGNORECASE))
        return list(dict.fromkeys(candidate.strip() for candidate in candidates if candidate.strip()))

    def _weekday_from_text(self, text: str) -> int | None:
        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        for name, index in weekdays.items():
            if re.search(rf"\b{name}\b", text):
                return index
        return None

    def _build_time(self, hour_text: str, minute_text: str, meridiem: str | None) -> time:
        hour = int(hour_text)
        minute = int(minute_text)
        if meridiem:
            meridiem = meridiem.lower()
            if meridiem == "pm" and hour != 12:
                hour += 12
            if meridiem == "am" and hour == 12:
                hour = 0
        return time(hour=hour, minute=minute)

    def _parse_age(self, value: str) -> int | None:
        match = re.search(r"\d{1,3}", value)
        if not match:
            return None
        age = int(match.group(0))
        return age if 0 <= age <= 120 else None

    def _normalize_phone(self, value: str) -> str | None:
        cleaned = re.sub(r"[^\d+]", "", value)
        digit_count = len(re.sub(r"\D", "", cleaned))
        if 10 <= digit_count <= 15:
            return cleaned
        return None

    def _looks_like_email(self, value: str) -> bool:
        return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value.strip()))

    def _extract_email(self, value: str) -> str | None:
        match = re.search(r"[^@\s]+@[^@\s]+\.[^@\s]+", value.strip())
        return match.group(0).lower() if match else None

    def _extract_otp(self, value: str) -> str | None:
        match = re.search(r"\b\d{6}\b", value)
        return match.group(0) if match else None

    async def _queue_preview_number(self, auth: dict[str, Any], doctor: dict[str, Any], date_time: str) -> int:
        try:
            booked = await self.backend_client.get_doctor_booked_slots(
                auth["access_token"],
                self._doctor_id(doctor),
            )
        except BackendApiError:
            return 1
        target_date = self._date_key(date_time)
        booked_items = booked.get("items", []) if isinstance(booked, dict) else []
        same_day_count = len(
            [
                item
                for item in booked_items
                if self._date_key(item) == target_date
            ]
        )
        return same_day_count + 1

    def _format_queue_line(self, appointment: dict[str, Any]) -> str:
        queue_number = appointment.get("queue_number")
        if not queue_number:
            return "Token: not assigned yet"
        current = appointment.get("current_queue_number")
        patients_before = appointment.get("patients_before")
        parts = [f"Token: {queue_number}"]
        if current:
            parts.append(f"current token: {current}")
        if patients_before is not None:
            parts.append(f"patients before you: {patients_before}")
        return ", ".join(parts)

    def _date_key(self, value: Any) -> str:
        if value in {None, ""}:
            return ""
        text = str(value)
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return parsed.date().isoformat()
        except ValueError:
            return text[:10]

    def _doctor_id(self, doctor: dict[str, Any]) -> str:
        return str(doctor.get("id") or doctor.get("doctor_id") or "")

    def _format_datetime(self, value: Any) -> str:
        if value in {None, ""}:
            return "-"
        text = str(value)
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return parsed.strftime("%d %b %Y, %I:%M %p")
        except ValueError:
            return text

    def _format_time(self, value: Any) -> str:
        if value in {None, ""}:
            return "-"
        return str(value)[:5]

    def _title_value(self, value: Any) -> str:
        return str(value or "-").replace("_", " ").title()

    def _is_yes(self, value: str) -> bool:
        return value.strip().lower() in {"yes", "y", "confirm", "ok", "okay", "book"}

    def _is_cancel_word(self, value: str) -> bool:
        return value.strip().lower() in {"stop", "cancel this", "exit", "never mind", "nevermind"}

    def _is_confusion_message(self, value: str) -> bool:
        lowered = value.strip().lower()
        return any(phrase in lowered for phrase in {"didn't understand", "dont understand", "don't understand", "explain"})

    def _is_process_question(self, value: str) -> bool:
        lowered = value.strip().lower()
        return any(word in lowered for word in {"process", "steps", "what to do", "how to", "guide"})

    def _is_password_help_question(self, value: str) -> bool:
        lowered = value.strip().lower()
        return "password" in lowered and any(word in lowered for word in {"can", "should", "give", "send", "share", "?"})

    def _asks_for_timings(self, value: str) -> bool:
        lowered = value.lower()
        return any(word in lowered for word in {"timing", "timings", "time", "hours", "schedule", "working"})

    def _is_auth_error(self, error: Exception) -> bool:
        lowered = str(error).lower()
        return "authentication" in lowered or "token" in lowered or "credentials" in lowered or "unauthorized" in lowered

    def _build_recent_history(self, telegram_user_id: int) -> str:
        items = self.store.get_recent_short_term_memory(telegram_user_id, limit=6)
        if not items:
            return ""
        ordered = list(reversed(items))
        return "\n".join(f"{item['role']}: {item['content']}" for item in ordered)

    def format_error(self, error: Exception) -> str:
        text = str(error)
        lowered = text.lower()
        if text == "patient_login_required":
            return "Please login with your patient account first."
        if text == "invalid_datetime":
            return DATE_TIME_FORMAT_HINT
        if "invalid email or password" in lowered:
            return "The email or password is incorrect. Please check and try again."
        if "otp" in lowered and "invalid" in lowered:
            return "The verification code is incorrect. Please check the code and try again."
        if "otp" in lowered and "expired" in lowered:
            return "The verification code has expired. Please login again to receive a new code."
        if "doctor not found" in lowered:
            return "I could not find that doctor. Please choose from the available doctors list."
        if "slot" in lowered and ("booked" in lowered or "held" in lowered):
            return "That slot is no longer available. Please choose another time."
        if "not available" in lowered:
            return "The doctor is not available at that time. Please choose another listed timing."
        if "2 hours" in lowered:
            return "Appointments can be changed only up to 2 hours before the scheduled time."
        if "authentication" in lowered or "token" in lowered:
            return "Your login session has expired. Please login again."
        return "Something went wrong while processing your request. Please try again."
