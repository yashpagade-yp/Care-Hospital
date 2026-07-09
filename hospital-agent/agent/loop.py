from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from agent.intents import Intent, detect_intent, normalize_intent_label
from agent.llm_client import GroqLlmClient, LlmClientError
from memory.long_term import LongTermMemory
from prompts.faq import answer_faq
from state.sqlite_store import SQLiteStore
from tools.backend_api import BackendApiClient, BackendApiError

logger = logging.getLogger(__name__)


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
        self.store.add_short_term_memory(telegram_user_id, "user", message)
        conversation_history = self._build_recent_history(telegram_user_id)

        flow = self.store.get_flow_state(telegram_user_id)
        if flow:
            reply = await self._continue_flow(telegram_user_id, message, flow)
            self.store.add_short_term_memory(telegram_user_id, "assistant", reply)
            return reply

        intent = await self._detect_intent(message, conversation_history)
        if intent == Intent.DOCTOR_INFO:
            reply = await self.handle_list_doctors(telegram_user_id)
        elif intent == Intent.BOOK:
            reply = self._start_booking(telegram_user_id)
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

        self.store.add_short_term_memory(telegram_user_id, "assistant", reply)
        return reply

    async def handle_login(self, telegram_user_id: int, email: str, password: str) -> str:
        response = await self.backend_client.start_login(email=email, password=password)
        self.store.set_pending_login(telegram_user_id, email)
        reply = (
            f"{response.get('message', 'OTP sent.')}\n"
            f"Email: {response.get('email', email)}\n"
            "Now send `/verify <otp>`."
        )
        self.store.add_short_term_memory(telegram_user_id, "assistant", reply)
        return reply

    async def handle_verify(self, telegram_user_id: int, otp: str, email: str | None = None) -> str:
        if not email:
            session = self.store.get_auth_session(telegram_user_id)
            email = session.get("pending_email") if session else None
        if not email:
            return "No pending login found. Use `/login <email> <password>` first."

        response = await self.backend_client.verify_login_otp(email=email, otp=otp)
        user = response.get("user", {})
        role = response.get("role", "")
        self.store.upsert_auth_session(
            telegram_user_id=telegram_user_id,
            email=email,
            patient_id=user.get("id"),
            role=role,
            access_token=response["access_token"],
            token_type=response.get("token_type", "bearer"),
        )
        return (
            f"Login successful.\n"
            f"Name: {user.get('name', '-')}\n"
            f"Role: {role}\n"
            "You can now use `/doctors`, `/appointments`, `/prescriptions`, or type `book appointment`."
        )

    def handle_logout(self, telegram_user_id: int) -> str:
        self.store.clear_auth_session(telegram_user_id)
        self.store.clear_flow_state(telegram_user_id)
        return "You have been logged out from the hospital assistant."

    async def handle_list_doctors(self, telegram_user_id: int) -> str:
        session = self._get_patient_session(telegram_user_id)
        if session:
            response = await self.backend_client.list_doctors(session["access_token"])
        else:
            response = await self.backend_client.list_public_doctors()
        items = response.get("items", [])
        if not items:
            return "No doctors found right now."

        lines = ["Available doctors:"]
        for item in items[:10]:
            doctor_id = item.get("id", "-")
            name = item.get("name", "Unknown")
            specialty = item.get("specialty") or "General"
            qualification = item.get("qualification") or "-"
            experience = item.get("experience_years")
            experience_text = f"{experience} yrs" if experience is not None else "-"
            lines.append(
                f"- {name} | {specialty} | {qualification} | exp: {experience_text} | id: {doctor_id}"
            )
        if session:
            lines.append("Use `/availability <doctor_id>` or type `book appointment` to continue.")
        else:
            lines.append(
                "Use `/availability <doctor_id>` to check doctor working hours. "
                "Login is only needed for booking or private patient actions."
            )
        return "\n".join(lines)

    async def handle_availability(self, telegram_user_id: int, doctor_id: str) -> str:
        session = self._get_patient_session(telegram_user_id)
        if session:
            availability = await self.backend_client.get_doctor_availability(session["access_token"], doctor_id)
            booked = await self.backend_client.get_doctor_booked_slots(session["access_token"], doctor_id)
        else:
            availability = await self.backend_client.get_public_doctor_availability(doctor_id)
            booked = {"items": []}
        entries = availability.get("items", availability) if isinstance(availability, dict) else availability
        booked_entries = booked.get("items", booked) if isinstance(booked, dict) else booked
        lines = [f"Availability for doctor `{doctor_id}`:"]
        if isinstance(entries, list) and entries:
            for entry in entries[:10]:
                lines.append(
                    f"- {entry.get('availability_type', '-')}"
                    f" | day: {entry.get('day_of_week', '-')}"
                    f" | {entry.get('start_time', '-')}-{entry.get('end_time', '-')}"
                    f" | exception_date: {entry.get('exception_date', '-')}"
                )
        else:
            lines.append("- No availability returned.")

        if session and isinstance(booked_entries, list) and booked_entries:
            lines.append("Booked slots:")
            for slot in booked_entries[:10]:
                lines.append(f"- {slot}")

        if session:
            lines.append("To book, type `book appointment`.")
        else:
            lines.append("If you want to book, first log in with `/login <email> <password>`.")
        return "\n".join(lines)

    async def handle_appointments(self, telegram_user_id: int) -> str:
        auth = self._require_patient_session(telegram_user_id)
        response = await self.backend_client.list_patient_appointments(
            auth["access_token"],
            auth["patient_id"],
        )
        items = response.get("items", [])
        if not items:
            return "No appointments found."

        lines = ["Your appointments:"]
        for item in items[:10]:
            lines.append(
                f"- id: {item.get('id', '-')}"
                f" | doctor: {item.get('doctor_name', item.get('doctor_id', '-'))}"
                f" | date: {item.get('date_time', '-')}"
                f" | status: {item.get('status', '-')}"
            )
        return "\n".join(lines)

    async def handle_prescriptions(self, telegram_user_id: int) -> str:
        auth = self._require_patient_session(telegram_user_id)
        response = await self.backend_client.list_patient_prescriptions(
            auth["access_token"],
            auth["patient_id"],
        )
        items = response.get("items", [])
        if not items:
            return "No prescriptions found for your account."

        lines = ["Your prescriptions:"]
        for item in items[:10]:
            lines.append(
                f"- appointment_id: {item.get('appointment_id', '-')}"
                f" | doctor: {item.get('doctor_name', '-')}"
                f" | visit_reason: {item.get('visit_reason', '-')}"
                f" | created_at: {item.get('created_at', '-')}"
            )
        lines.append("Use `/prescription <appointment_id>` to view one prescription.")
        return "\n".join(lines)

    async def handle_prescription_by_appointment(self, telegram_user_id: int, appointment_id: str) -> str:
        auth = self._require_patient_session(telegram_user_id)
        response = await self.backend_client.get_prescription_by_appointment(
            auth["access_token"],
            appointment_id,
        )
        medicines = response.get("medicines", [])
        medicine_lines = "\n".join(f"- {medicine}" for medicine in medicines) if medicines else "- None listed"
        return (
            f"Prescription for appointment `{appointment_id}`:\n"
            f"Doctor: {response.get('doctor_name', '-')}\n"
            f"Visit reason: {response.get('visit_reason', '-')}\n"
            f"Medicines:\n{medicine_lines}\n"
            f"Notes: {response.get('notes', '-')}"
        )

    def _start_booking(self, telegram_user_id: int) -> str:
        try:
            self._require_patient_session(telegram_user_id)
        except BackendApiError as error:
            return str(error)
        self.store.set_flow_state(
            telegram_user_id,
            active_intent=Intent.BOOK.value,
            step="doctor_id",
            payload={},
        )
        return "Booking started. Send the doctor id. You can use `/doctors` first."

    def _start_availability(self, telegram_user_id: int) -> str:
        self.store.set_flow_state(
            telegram_user_id,
            active_intent=Intent.AVAILABILITY.value,
            step="doctor_id",
            payload={},
        )
        session = self._get_patient_session(telegram_user_id)
        if session:
            return "Availability lookup started. Send the doctor id."
        return "Send the doctor id to check public working hours. You can use `/doctors` first."

    async def _start_cancel(self, telegram_user_id: int) -> str:
        try:
            self._require_patient_session(telegram_user_id)
        except BackendApiError as error:
            return str(error)
        self.store.set_flow_state(
            telegram_user_id,
            active_intent=Intent.CANCEL.value,
            step="appointment_id",
            payload={},
        )
        return "Cancellation started. Send the appointment id. You can use `/appointments` first."

    async def _start_reschedule(self, telegram_user_id: int) -> str:
        try:
            self._require_patient_session(telegram_user_id)
        except BackendApiError as error:
            return str(error)
        self.store.set_flow_state(
            telegram_user_id,
            active_intent=Intent.RESCHEDULE.value,
            step="appointment_id",
            payload={},
        )
        return "Reschedule started. Send the appointment id. You can use `/appointments` first."

    async def _start_prescription_lookup(self, telegram_user_id: int) -> str:
        try:
            self._require_patient_session(telegram_user_id)
        except BackendApiError as error:
            return str(error)
        self.store.set_flow_state(
            telegram_user_id,
            active_intent=Intent.PRESCRIPTION.value,
            step="appointment_id",
            payload={},
        )
        return "Prescription lookup started. Send the appointment id, or use `/prescriptions` first."

    async def _continue_flow(self, telegram_user_id: int, message: str, flow: dict[str, Any]) -> str:
        intent = flow["active_intent"]
        step = flow["step"]
        payload = flow["payload"]

        if intent == Intent.AVAILABILITY.value:
            self.store.clear_flow_state(telegram_user_id)
            return await self.handle_availability(telegram_user_id, message.strip())

        if intent == Intent.PRESCRIPTION.value and step == "appointment_id":
            self.store.clear_flow_state(telegram_user_id)
            return await self.handle_prescription_by_appointment(telegram_user_id, message.strip())

        if intent == Intent.CANCEL.value:
            return await self._continue_cancel(telegram_user_id, message, step, payload)

        if intent == Intent.RESCHEDULE.value:
            return await self._continue_reschedule(telegram_user_id, message, step, payload)

        if intent == Intent.BOOK.value:
            return await self._continue_booking(telegram_user_id, message, step, payload)

        self.store.clear_flow_state(telegram_user_id)
        return self._default_help()

    async def _continue_cancel(self, telegram_user_id: int, message: str, step: str, payload: dict[str, Any]) -> str:
        if step == "appointment_id":
            payload["appointment_id"] = message.strip()
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.CANCEL.value,
                step="reason",
                payload=payload,
            )
            return "Send the cancellation reason."

        auth = self._require_patient_session(telegram_user_id)
        response = await self.backend_client.cancel_appointment(
            auth["access_token"],
            payload["appointment_id"],
            message.strip(),
        )
        self.store.clear_flow_state(telegram_user_id)
        return (
            f"Appointment cancelled.\n"
            f"id: {response.get('id', payload['appointment_id'])}\n"
            f"status: {response.get('status', '-')}"
        )

    async def _continue_reschedule(self, telegram_user_id: int, message: str, step: str, payload: dict[str, Any]) -> str:
        if step == "appointment_id":
            payload["appointment_id"] = message.strip()
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.RESCHEDULE.value,
                step="new_datetime",
                payload=payload,
            )
            return "Send the new date-time in `YYYY-MM-DDTHH:MM` format."

        if step == "new_datetime":
            payload["new_date_time"] = self._parse_iso_datetime(message.strip())
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.RESCHEDULE.value,
                step="reason",
                payload=payload,
            )
            return "Send the reschedule reason, or type `skip`."

        auth = self._require_patient_session(telegram_user_id)
        reason = None if message.strip().lower() == "skip" else message.strip()
        response = await self.backend_client.reschedule_appointment(
            auth["access_token"],
            payload["appointment_id"],
            payload["new_date_time"],
            reason,
        )
        self.store.clear_flow_state(telegram_user_id)
        previous = response.get("previous_appointment", {})
        new = response.get("new_appointment", {})
        return (
            "Appointment rescheduled.\n"
            f"Previous id: {previous.get('id', payload['appointment_id'])}\n"
            f"New id: {new.get('id', '-')}\n"
            f"New date: {new.get('date_time', payload['new_date_time'])}"
        )

    async def _continue_booking(self, telegram_user_id: int, message: str, step: str, payload: dict[str, Any]) -> str:
        auth = self._require_patient_session(telegram_user_id)
        if step == "doctor_id":
            payload["doctor_id"] = message.strip()
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.BOOK.value,
                step="datetime",
                payload=payload,
            )
            return "Send the appointment date-time in `YYYY-MM-DDTHH:MM` format."

        if step == "datetime":
            payload["date_time"] = self._parse_iso_datetime(message.strip())
            hold = await self.backend_client.create_slot_hold(
                auth["access_token"],
                payload["doctor_id"],
                payload["date_time"],
            )
            payload["slot_hold_id"] = hold["id"]
            self.store.set_flow_state(
                telegram_user_id,
                active_intent=Intent.BOOK.value,
                step="details",
                payload=payload,
            )
            return (
                "Slot hold created.\n"
                f"slot_hold_id: {hold['id']}\n"
                "Now send booking details in this format:\n"
                "`name | phone | age | gender | fee | reason(optional) | blood_group(optional)`"
            )

        details = [item.strip() for item in message.split("|")]
        if len(details) < 5:
            return "Please send details as `name | phone | age | gender | fee | reason(optional) | blood_group(optional)`"

        request_payload = {
            "slot_hold_id": payload["slot_hold_id"],
            "patient_name": details[0],
            "patient_phone": details[1],
            "patient_age": int(details[2]),
            "patient_gender": details[3],
            "fee": float(details[4]),
        }
        if len(details) > 5 and details[5]:
            request_payload["reason"] = details[5]
        if len(details) > 6 and details[6]:
            request_payload["patient_blood_group"] = details[6]

        response = await self.backend_client.confirm_appointment(auth["access_token"], request_payload)
        self.store.clear_flow_state(telegram_user_id)
        return (
            "Appointment booked successfully.\n"
            f"Doctor: {response.get('doctor_name', '-')}\n"
            f"Patient: {response.get('patient_name', '-')}\n"
            f"Appointment id: {response.get('confirmed_appointment', {}).get('id', response.get('id', '-'))}"
        )

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
            "I can help with appointments, availability, prescriptions, and hospital FAQs.\n"
            "Use `/help` to see commands, or type things like `book appointment`, `show my prescription`, or `cancel appointment`."
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

    def _require_patient_session(self, telegram_user_id: int) -> dict[str, Any]:
        session = self._get_patient_session(telegram_user_id)
        if not session or not session.get("access_token"):
            raise BackendApiError(
                "This action needs a verified patient account. "
                "General hospital enquiries can be asked without login, but for this action please use "
                "`/login <email> <password>` first."
            )
        if session.get("role", "").upper() != "PATIENT":
            raise BackendApiError("Only patient accounts are supported in this hospital-agent V1.")
        return session

    def _get_patient_session(self, telegram_user_id: int) -> dict[str, Any]:
        session = self.store.get_auth_session(telegram_user_id)
        if session and session.get("role", "").upper() == "PATIENT" and session.get("access_token"):
            return session
        return {}

    def _build_recent_history(self, telegram_user_id: int) -> str:
        items = self.store.get_recent_short_term_memory(telegram_user_id, limit=6)
        if not items:
            return ""
        ordered = list(reversed(items))
        return "\n".join(f"{item['role']}: {item['content']}" for item in ordered)

    @staticmethod
    def _parse_iso_datetime(value: str) -> str:
        try:
            return datetime.fromisoformat(value).isoformat()
        except ValueError as error:
            raise BackendApiError("Please send date-time in `YYYY-MM-DDTHH:MM` format.") from error
