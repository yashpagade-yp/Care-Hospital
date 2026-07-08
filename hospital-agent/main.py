from __future__ import annotations

import logging

from agent.llm_client import GroqLlmClient
from agent.loop import HospitalAgentLoop
from config import load_settings
from memory.long_term import LongTermMemory
from state.sqlite_store import SQLiteStore
from telegram.bot_app import HospitalTelegramBot
from tools.backend_api import BackendApiClient


def main() -> None:
    settings = load_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    store = SQLiteStore(settings.sqlite_path)
    backend_client = BackendApiClient(
        base_url=settings.backend_base_url,
        timeout_seconds=settings.backend_timeout_seconds,
    )
    long_term_memory = LongTermMemory((settings.sqlite_path.parent.parent / "memory").resolve())
    llm_client = GroqLlmClient(api_key=settings.groq_api_key, model=settings.groq_model)
    agent = HospitalAgentLoop(
        backend_client=backend_client,
        store=store,
        long_term_memory=long_term_memory,
        llm_client=llm_client,
    )
    HospitalTelegramBot(settings, agent=agent).run()


if __name__ == "__main__":
    main()
