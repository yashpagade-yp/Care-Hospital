from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


@dataclass(slots=True)
class Settings:
    telegram_bot_token: str
    telegram_mode: str
    backend_base_url: str
    backend_timeout_seconds: float
    groq_api_key: str
    groq_model: str
    app_env: str
    log_level: str
    memory_enabled: bool
    state_enabled: bool
    state_backend: str
    sqlite_path: Path


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    sqlite_path = Path(
        os.getenv(
            "HOSPITAL_AGENT_SQLITE_PATH",
            str(BASE_DIR / "local" / "agent_state.db"),
        )
    )
    if not sqlite_path.is_absolute():
        sqlite_path = BASE_DIR / sqlite_path

    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_mode=os.getenv("TELEGRAM_MODE", "polling"),
        backend_base_url=os.getenv("HOSPITAL_BACKEND_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
        backend_timeout_seconds=float(os.getenv("HOSPITAL_API_TIMEOUT_SECONDS", "30")),
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        app_env=os.getenv("HOSPITAL_AGENT_ENV", "development"),
        log_level=os.getenv("HOSPITAL_AGENT_LOG_LEVEL", "INFO"),
        memory_enabled=_get_bool("HOSPITAL_AGENT_MEMORY_ENABLED", True),
        state_enabled=_get_bool("HOSPITAL_AGENT_STATE_ENABLED", True),
        state_backend=os.getenv("HOSPITAL_AGENT_STATE_BACKEND", "sqlite"),
        sqlite_path=sqlite_path,
    )
