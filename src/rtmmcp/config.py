from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


def _load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


@dataclass(slots=True)
class Settings:
    api_key: str
    shared_secret: str
    auth_token: str | None
    auth_state_file: Path

    @classmethod
    def load(cls, base_dir: Path | None = None) -> "Settings":
        root = base_dir or Path.cwd()
        _load_dotenv(root / ".env")

        api_key = os.getenv("RTM_API_KEY", "").strip()
        shared_secret = os.getenv("RTM_SHARED_SECRET", "").strip()
        auth_token = os.getenv("RTM_AUTH_TOKEN", "").strip() or None
        state_name = os.getenv("RTM_AUTH_STATE_FILE", ".rtm_auth.json").strip() or ".rtm_auth.json"

        if not api_key or not shared_secret:
            raise RuntimeError(
                "Missing RTM_API_KEY or RTM_SHARED_SECRET. Set them in the environment or .env file."
            )

        return cls(
            api_key=api_key,
            shared_secret=shared_secret,
            auth_token=auth_token,
            auth_state_file=root / state_name,
        )
