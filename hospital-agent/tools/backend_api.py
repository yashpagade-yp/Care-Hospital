from __future__ import annotations

from typing import Any

import httpx


class BackendApiError(RuntimeError):
    pass


class BackendApiClient:
    def __init__(self, *, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds

    async def start_login(self, *, email: str, password: str) -> dict[str, Any]:
        return await self._request("POST", "/v1/auth/login", json={"email": email, "password": password})

    async def verify_login_otp(self, *, email: str, otp: str) -> dict[str, Any]:
        return await self._request("POST", "/v1/auth/verify-login-otp", json={"email": email, "otp": otp})

    async def register_patient(self, *, name: str, phone: str, email: str, password: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/v1/patients/register",
            json={"name": name, "phone": phone, "email": email, "password": password},
        )

    async def verify_patient_registration_otp(self, *, email: str, otp: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/v1/patients/verify-otp",
            json={"email": email, "otp": otp},
        )

    async def list_doctors(self, access_token: str) -> dict[str, Any]:
        return await self._request("GET", "/v1/doctors", access_token=access_token)

    async def list_public_doctors(self) -> dict[str, Any]:
        return await self._request("GET", "/v1/public/doctors")

    async def get_doctor_availability(self, access_token: str, doctor_id: str) -> Any:
        return await self._request("GET", f"/v1/doctors/{doctor_id}/availability", access_token=access_token)

    async def get_public_doctor_availability(self, doctor_id: str) -> Any:
        return await self._request("GET", f"/v1/public/doctors/{doctor_id}/availability")

    async def get_doctor_booked_slots(self, access_token: str, doctor_id: str) -> Any:
        return await self._request("GET", f"/v1/doctors/{doctor_id}/booked-slots", access_token=access_token)

    async def create_slot_hold(self, access_token: str, doctor_id: str, date_time: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/v1/appointments/slot-holds",
            access_token=access_token,
            json={"doctor_id": doctor_id, "date_time": date_time},
        )

    async def confirm_appointment(self, access_token: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/v1/appointments/confirm",
            access_token=access_token,
            json=payload,
        )

    async def list_patient_appointments(self, access_token: str, patient_id: str) -> dict[str, Any]:
        return await self._request(
            "GET",
            f"/v1/patients/{patient_id}/appointments",
            access_token=access_token,
        )

    async def cancel_appointment(self, access_token: str, appointment_id: str, cancel_reason: str) -> dict[str, Any]:
        return await self._request(
            "PATCH",
            f"/v1/appointments/{appointment_id}/cancel",
            access_token=access_token,
            json={"cancel_reason": cancel_reason},
        )

    async def reschedule_appointment(
        self,
        access_token: str,
        appointment_id: str,
        new_date_time: str,
        reason: str | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"new_date_time": new_date_time}
        if reason:
            payload["reason"] = reason
        return await self._request(
            "PATCH",
            f"/v1/appointments/{appointment_id}/reschedule",
            access_token=access_token,
            json=payload,
        )

    async def list_patient_prescriptions(self, access_token: str, patient_id: str) -> dict[str, Any]:
        return await self._request(
            "GET",
            f"/v1/patients/{patient_id}/prescriptions",
            access_token=access_token,
        )

    async def get_prescription_by_appointment(self, access_token: str, appointment_id: str) -> dict[str, Any]:
        return await self._request(
            "GET",
            f"/v1/appointments/{appointment_id}/prescription",
            access_token=access_token,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        access_token: str | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        headers: dict[str, str] = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.request(method, path, headers=headers, json=json)

        try:
            payload = response.json()
        except ValueError:
            payload = {"detail": response.text or "Unknown backend response"}

        if response.is_success:
            return payload

        detail = payload.get("detail") or payload.get("message") or f"Backend request failed with {response.status_code}"
        raise BackendApiError(str(detail))
