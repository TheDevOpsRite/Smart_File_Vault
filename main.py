from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from auth import AuthManager
from config import ConfigManager
from vault_ui import LoginWindow, VaultWindow


class SmartFileVaultApp:
    def __init__(self) -> None:
        self.qt_app = QApplication(sys.argv)
        self.config_manager = ConfigManager()
        self.config_manager.ensure_directories()
        self.auth_manager = AuthManager(self.config_manager)

        self.login_window = LoginWindow(self.auth_manager)
        self.login_window.authenticated.connect(self._on_authenticated)

        self.vault_window: VaultWindow | None = None

    def _on_authenticated(self, combined_secret: str) -> None:
        self.login_window.hide()
        self.vault_window = VaultWindow(self.config_manager, combined_secret)
        self.vault_window.lock_requested.connect(self._lock_vault)
        self.vault_window.show()

    def _lock_vault(self) -> None:
        if self.vault_window is not None:
            self.vault_window.close()
            self.vault_window = None
        self.login_window.reset_mode()
        self.login_window.show()
        self.login_window.raise_()
        self.login_window.activateWindow()

    def run(self) -> int:
        self.login_window.show()
        return self.qt_app.exec()


def main() -> int:
    app = SmartFileVaultApp()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
