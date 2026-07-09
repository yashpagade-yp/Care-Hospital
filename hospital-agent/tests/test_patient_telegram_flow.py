from __future__ import annotations

import asyncio
import unittest

from agent.intents import Intent, detect_intent
from agent.loop import HospitalAgentLoop
from tools.backend_api import BackendApiError


class FakeBackend:
    async def verify_login_otp(self, *, email: str, otp: str) -> dict:
        return {
            "access_token": "token",
            "token_type": "bearer",
            "role": "ADMIN",
            "user": {"id": "admin-1", "name": "Admin User", "role": "ADMIN"},
        }


class FakeStore:
    def __init__(self) -> None:
        self.auth_cleared = False
        self.flow_cleared = False
        self.upserted = False

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


class PatientTelegramFlowTests(unittest.TestCase):
    def test_detects_patient_intents_separately(self) -> None:
        self.assertEqual(detect_intent("show my appointments"), Intent.APPOINTMENTS)
        self.assertEqual(detect_intent("book appointment"), Intent.BOOK)
        self.assertEqual(detect_intent("show doctors"), Intent.DOCTOR_INFO)
        self.assertEqual(detect_intent("tell me available doctors"), Intent.DOCTOR_INFO)
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


if __name__ == "__main__":
    unittest.main()
