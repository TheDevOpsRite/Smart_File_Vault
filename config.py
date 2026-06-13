from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

APP_NAME = "SmartFileVault"
APP_VERSION = "1.0"
CONFIG_FILENAME = "config.json"
VAULT_DIRNAME = "vault_data"
FREE_ENCRYPTED_FILE_LIMIT = 5


@dataclass
class ConfigData:
    password_hash: str = ""
    auth_salt: str = ""
    failed_attempts: int = 0
    recovery_nonce: str = ""
    recovery_wrapped_secret: str = ""


class ConfigManager:
    def __init__(self) -> None:
        self._config_dir = self._resolve_config_dir()
        self._vault_dir = self._config_dir / VAULT_DIRNAME
        self._config_file = self._config_dir / CONFIG_FILENAME

    @property
    def config_dir(self) -> Path:
        return self._config_dir

    @property
    def vault_dir(self) -> Path:
        return self._vault_dir

    @property
    def config_file(self) -> Path:
        return self._config_file

    def ensure_directories(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._vault_dir.mkdir(parents=True, exist_ok=True)

    def is_initialized(self) -> bool:
        if not self._config_file.exists():
            return False
        data = self.load()
        return bool(data.password_hash and data.auth_salt)

    def load(self) -> ConfigData:
        self.ensure_directories()
        if not self._config_file.exists():
            return ConfigData()

        try:
            raw = json.loads(self._config_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return ConfigData()

        return ConfigData(
            password_hash=str(raw.get("password_hash", "")),
            auth_salt=str(raw.get("auth_salt", "")),
            failed_attempts=int(raw.get("failed_attempts", 0)),
            recovery_nonce=str(raw.get("recovery_nonce", "")),
            recovery_wrapped_secret=str(raw.get("recovery_wrapped_secret", "")),
        )

    def save(self, config: ConfigData) -> None:
        self.ensure_directories()
        payload: dict[str, Any] = {
            "password_hash": config.password_hash,
            "auth_salt": config.auth_salt,
            "failed_attempts": config.failed_attempts,
            "recovery_nonce": config.recovery_nonce,
            "recovery_wrapped_secret": config.recovery_wrapped_secret,
        }
        self._config_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _resolve_config_dir() -> Path:
        if os.name == "nt":
            appdata = os.getenv("APPDATA")
            if appdata:
                return Path(appdata) / APP_NAME
            return Path.home() / "AppData" / "Roaming" / APP_NAME
        return Path.home() / ".config" / APP_NAME
