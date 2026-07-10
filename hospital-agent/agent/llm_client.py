from __future__ import annotations

import json
from typing import Any

import httpx


class LlmClientError(RuntimeError):
    pass


class GroqLlmClient:
    def __init__(self, *, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1"

    @property
    def enabled(self) -> bool:
        return bool(self.api_key.strip())

    async def classify_intent(self, message: str, *, conversation_history: str = "") -> str:
        if not self.enabled:
            raise LlmClientError("Groq LLM is not configured.")

        prompt = (
            "You are classifying a patient message for a hospital Telegram assistant.\n"
            "Return only one lowercase label from this list:\n"
            "doctor_info, book, register, appointments, availability, cancel, reschedule, prescription, faq, unknown.\n"
            "Use doctor_info when the patient asks for available doctors, present doctors, specialties, or doctor list.\n"
            "Use register when the patient asks to create a patient account, says they are a new user, or asks for patient registration.\n"
            "Use appointments when the patient asks to see their appointments, appointment history, or appointment status.\n"
            "If the message is about medicines or old prescription access, use prescription.\n"
            "If it is a general hospital enquiry, use faq.\n"
            f"Conversation history:\n{conversation_history or '-'}\n\n"
            f"Message: {message}"
        )
        content = await self._chat(
            system_prompt="Classify intent accurately. Return only the label.",
            user_prompt=prompt,
            temperature=0.2,
            max_tokens=20,
        )
        return content.strip().lower()

    async def answer_general_query(
        self,
        *,
        user_message: str,
        memory_hint: str = "",
        conversation_history: str = "",
    ) -> str:
        if not self.enabled:
            raise LlmClientError("Groq LLM is not configured.")

        system_prompt = (
            "You are a hospital assistant for patients on Telegram.\n"
            "Be simple, safe, and patient-friendly.\n"
            "This assistant is only for patient conversations. Do not offer admin or doctor login flows.\n"
            "Do not expose backend IDs, internal fields, commands, schemas, or developer-style instructions unless the user explicitly asks for a technical detail.\n"
            "Do not tell patients to register before booking in Telegram. Telegram appointment booking is allowed without registration.\n"
            "For prescriptions, appointment history, or private data, registration/login in the web app is required.\n"
            "Public doctor lists, specialties, services, and working hours do not require login.\n"
            "You may answer general hospital enquiries and guide the user.\n"
            "Do not diagnose.\n"
            "Do not prescribe or change medicines.\n"
            "Do not provide emergency medical advice.\n"
            "If a request needs private patient data, tell the user to log in first.\n"
            "If the request asks for prescription decisions, refuse and ask them to contact the doctor or hospital.\n"
        )
        if memory_hint:
            system_prompt += f"\nUser preference hint: {memory_hint}"

        return await self._chat(
            system_prompt=system_prompt,
            user_prompt=(
                f"Recent conversation:\n{conversation_history or '-'}\n\n"
                f"User message:\n{user_message}"
            ),
            temperature=0.4,
            max_tokens=220,
        )

    async def _chat(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30) as client:
            response = await client.post("/chat/completions", headers=headers, json=payload)

        try:
            data = response.json()
        except json.JSONDecodeError as error:
            raise LlmClientError("Groq returned a non-JSON response.") from error

        if not response.is_success:
            detail = data.get("error", {}).get("message") or data.get("detail") or "Groq request failed."
            raise LlmClientError(str(detail))

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as error:
            raise LlmClientError("Groq response did not include assistant content.") from error
