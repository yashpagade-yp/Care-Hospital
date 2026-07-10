from __future__ import annotations

import asyncio
import unittest

from agent.intents import Intent, detect_intent
from agent.loop import HospitalAgentLoop
from tools.backend_api import BackendApiError


class FakeBackend:
    def __init__(self) -> None:
        self.private_doctors_called = False

    async def verify_login_otp(self, *, email: str, otp: str) -> dict:
        return {
            "access_token": "token",
            "token_type": "bearer",
            "role": "ADMIN",
            "user": {"id": "admin-1", "name": "Admin User", "role": "ADMIN"},
        }

    async def list_doctors(self, access_token: str) -> dict:
        self.private_doctors_called = True
        raise BackendApiError("Invalid authentication credentials")

    async def list_public_doctors(self) -> dict:
        return {"items": [{"id": "doctor-1", "name": "Public Doctor"}]}


class FakeLlm:
    enabled = True

    async def classify_intent(self, message: str, *, conversation_history: str = "") -> str:
        return "appointments"


class FakeStore:
    def __init__(self) -> None:
        self.auth_cleared = False
        self.flow_cleared = False
        self.upserted = False
        self.flow_state = {}

    def get_auth_session(self, telegram_user_id: int) -> dict:
        return {"pending_email": "admin@example.com"}

    def get_flow_state(self, telegram_user_id: int) -> dict:
        return {}

    def clear_auth_session(self, telegram_user_id: int) -> None:
        self.auth_cleared = True

    def clear_flow_state(self, telegram_user_id: int) -> None:
        self.flow_cleared = True

    def upsert_auth_session(self, **kwargs) -> None:
        self.upserted = True

    def set_flow_state(self, telegram_user_id: int, *, active_intent: str, step: str, payload: dict) -> None:
        self.flow_state = {"active_intent": active_intent, "step": step, "payload": payload}

    def get_recent_short_term_memory(self, telegram_user_id: int, limit: int = 6) -> list:
        return []


class PatientTelegramFlowTests(unittest.TestCase):
    def test_detects_patient_intents_separately(self) -> None:
        self.assertEqual(detect_intent("show my appointments"), Intent.APPOINTMENTS)
        self.assertEqual(detect_intent("book appointment"), Intent.BOOK)
        self.assertEqual(detect_intent("show doctors"), Intent.DOCTOR_INFO)
        self.assertEqual(detect_intent("tell me available doctors"), Intent.DOCTOR_INFO)
        self.assertEqual(
            detect_intent("Show me available doctors and their timings because I want to book an appointment"),
            Intent.DOCTOR_INFO,
        )
        self.assertEqual(detect_intent("I am a new user. I don't have any past record"), Intent.REGISTER)
        self.assertEqual(detect_intent("doctor working hours"), Intent.AVAILABILITY)

    def test_doctor_list_hides_backend_id(self) -> None:
        loop = HospitalAgentLoop(
            backend_client=None,
            store=None,
            long_term_memory=None,
            llm_client=None,
        )
        output = loop._format_doctor_options(
            [
                {
                    "id": "6a4f9240a9aa182aa5b4649a",
                    "name": "Yash Pagade",
                    "specialty": "General Medicine",
                    "qualification": "MBBS, MD",
                    "experience_years": 8,
                }
            ]
        )

        self.assertIn("Yash Pagade", output)
        self.assertIn("General Medicine", output)
        self.assertNotIn("6a4f9240a9aa182aa5b4649a", output)

    def test_doctor_list_does_not_stop_at_ten(self) -> None:
        loop = HospitalAgentLoop(
            backend_client=None,
            store=None,
            long_term_memory=None,
            llm_client=None,
        )
        doctors = [
            {
                "id": f"doctor-{index}",
                "name": f"Doctor {index}",
                "specialty": "General Medicine",
                "qualification": "MBBS",
                "experience_years": index,
            }
            for index in range(1, 16)
        ]

        output = loop._format_doctor_options(doctors)

        self.assertIn("15. Doctor 15", output)

    def test_resolves_doctor_from_natural_sentence(self) -> None:
        loop = HospitalAgentLoop(
            backend_client=None,
            store=None,
            long_term_memory=None,
            llm_client=None,
        )

        doctor, matches = loop._resolve_doctor(
            "I want to choose Doctor Yash Pagade for appointment",
            [
                {
                    "id": "doctor-1",
                    "name": "Yash Pagade",
                    "specialty": "General Medicine",
                    "qualification": "MBBS, MD",
                    "services": ["General consultation"],
                }
            ],
        )

        self.assertEqual(doctor["id"], "doctor-1")
        self.assertEqual(matches, [])

    def test_parses_patient_friendly_datetime(self) -> None:
        loop = HospitalAgentLoop(
            backend_client=None,
            store=None,
            long_term_memory=None,
            llm_client=None,
        )

        self.assertEqual(loop._parse_patient_datetime("13 July 2026 10 AM"), "2026-07-13T10:00:00")
        self.assertEqual(loop._parse_patient_datetime("2026-07-13 10:00 AM"), "2026-07-13T10:00:00")
        self.assertEqual(
            loop._parse_patient_datetime("10 AM", base_date="2026-07-13"),
            "2026-07-13T10:00:00",
        )

    def test_date_without_time_asks_for_time(self) -> None:
        loop = HospitalAgentLoop(
            backend_client=None,
            store=None,
            long_term_memory=None,
            llm_client=None,
        )

        with self.assertRaisesRegex(BackendApiError, "missing_time"):
            loop._parse_patient_datetime("Date is 13th of July 2026")

    def test_verify_rejects_non_patient_accounts(self) -> None:
        store = FakeStore()
        loop = HospitalAgentLoop(
            backend_client=FakeBackend(),
            store=store,
            long_term_memory=None,
            llm_client=None,
        )

        reply = asyncio.run(loop.handle_verify(telegram_user_id=10, otp="123456"))

        self.assertIn("only for patients", reply)
        self.assertTrue(store.auth_cleared)
        self.assertTrue(store.flow_cleared)
        self.assertFalse(store.upserted)

    def test_public_doctor_list_does_not_use_stale_login_session(self) -> None:
        backend = FakeBackend()
        loop = HospitalAgentLoop(
            backend_client=backend,
            store=FakeStore(),
            long_term_memory=None,
            llm_client=None,
        )

        doctors = asyncio.run(loop._load_doctors(telegram_user_id=10))

        self.assertEqual(doctors[0]["name"], "Public Doctor")
        self.assertFalse(backend.private_doctors_called)

    def test_stale_login_booking_step_resets_to_guest_booking(self) -> None:
        store = FakeStore()
        loop = HospitalAgentLoop(
            backend_client=FakeBackend(),
            store=store,
            long_term_memory=None,
            llm_client=FakeLlm(),
        )

        reply = asyncio.run(
            loop._continue_flow(
                10,
                "patient@example.com",
                {"active_intent": Intent.BOOK.value, "step": "login_email", "payload": {}},
            )
        )

        self.assertIn("no registration is needed", reply.lower())
        self.assertEqual(store.flow_state["step"], "doctor_choice")


if __name__ == "__main__":
    unittest.main()
