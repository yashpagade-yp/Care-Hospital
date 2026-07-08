from __future__ import annotations

from pathlib import Path


class LongTermMemory:
    def __init__(self, memory_dir: Path) -> None:
        self.memory_dir = memory_dir
        self.memory_file = memory_dir / "MEMORY.md"
        self.user_file = memory_dir / "USER.md"

    def read_system_memory(self) -> str:
        return self._read_file(self.memory_file)

    def read_user_profile(self) -> str:
        return self._read_file(self.user_file)

    def build_context(self) -> str:
        parts = [
            self.read_system_memory(),
            self.read_user_profile(),
        ]
        return "\n\n".join(part for part in parts if part).strip()

    @staticmethod
    def _read_file(path: Path) -> str:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8").strip()
