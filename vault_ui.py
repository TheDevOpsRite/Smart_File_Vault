from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QProgressBar,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from auth import AuthManager, AuthenticationError
from config import APP_VERSION, FREE_ENCRYPTED_FILE_LIMIT, ConfigManager
from crypto_utils import CryptoError, decrypt_file, encrypt_file


class RecoveryCodeDialog(QDialog):
    def __init__(self, recovery_codes: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._recovery_codes = recovery_codes
        self._saved = False

        self.setWindowTitle("Save Recovery Codes")
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setMinimumHeight(420)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        title = QLabel("Recovery codes are required to complete setup")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")

        tip = QLabel(
            "TIP: Save these recovery codes somewhere safe. You can use any two of them later if you forget your passwords."
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #8be9fd; font-weight: 600;")

        instructions = QLabel(
            "This step is mandatory. Click Save to download the recovery file to your Downloads folder."
        )
        instructions.setWordWrap(True)

        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlainText("\n".join(recovery_codes))

        self.save_button = QPushButton("Save Recovery Codes")
        self.save_button.clicked.connect(self._save_recovery_codes)

        layout.addWidget(title)
        layout.addWidget(tip)
        layout.addWidget(instructions)
        layout.addWidget(self.preview)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

    def _default_download_path(self) -> Path:
        downloads_dir = Path.home() / "Downloads"
        if not downloads_dir.exists():
            downloads_dir = Path.home()
        return downloads_dir / "SmartFileVault-Recovery-Codes.txt"

    def _save_recovery_codes(self) -> None:
        target_path = self._default_download_path()
        contents = "\n".join(
            [
                "Smart File Vault recovery codes",
                "",
                "Store these codes safely. Any two codes can recover the vault.",
                "",
            ]
            + self._recovery_codes
            + [""]
        )
        target_path.write_text(contents, encoding="utf-8")
        self._saved = True
        QMessageBox.information(self, "Recovery Codes Saved", f"Saved to:\n{target_path}")
        self.accept()

    def reject(self) -> None:  # type: ignore[override]
        if self._saved:
            super().reject()

    def closeEvent(self, event):  # type: ignore[override]
        if self._saved:
            super().closeEvent(event)
        else:
            event.ignore()


class LoginWindow(QWidget):
    authenticated = Signal(str)

    def __init__(self, auth_manager: AuthManager) -> None:
        super().__init__()
        self._auth_manager = auth_manager
        self._is_first_run = not self._auth_manager.is_initialized()

        self.setWindowTitle(f"Smart File Vault v{APP_VERSION} - Login")
        self.setMinimumWidth(500)
        self._build_ui()
        self._apply_dark_theme()

    def _build_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setSpacing(12)

        title = QLabel(f"Smart File Vault v{APP_VERSION}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: 600;")

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = Path(__file__).parent / "appLogo.png"
        if logo_path.exists():
            logo_pixmap = QPixmap(str(logo_path))
            if not logo_pixmap.isNull():
                self.logo_label.setPixmap(
                    logo_pixmap.scaled(
                        150,
                        150,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )

        subtitle_text = "Create your two vault passwords" if self._is_first_run else "Enter both vault passwords"
        self.subtitle_label = QLabel(subtitle_text)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        warning_text = (
            "WARNING: If you forget Password 1 + Password 2 combination, recovery is impossible. "
            "Encrypted files cannot be decrypted without the exact combination."
        )
        self.warning_label = QLabel(warning_text)
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet("color: #ff5f56; font-weight: 600;")
        self.warning_label.setVisible(self._is_first_run)

        self.unrecoverable_ack_checkbox = QCheckBox("I understand this is unrecoverable")
        self.unrecoverable_ack_checkbox.setVisible(self._is_first_run)

        self.password_one_input = QLineEdit()
        self.password_one_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_one_input.setPlaceholderText("Password 1")

        self.password_two_input = QLineEdit()
        self.password_two_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_two_input.setPlaceholderText("Password 2")

        self.confirm_one_input = QLineEdit()
        self.confirm_one_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_one_input.setPlaceholderText("Confirm Password 1")
        self.confirm_one_input.setVisible(self._is_first_run)

        self.confirm_two_input = QLineEdit()
        self.confirm_two_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_two_input.setPlaceholderText("Confirm Password 2")
        self.confirm_two_input.setVisible(self._is_first_run)

        self.show_password = QCheckBox("Show password")
        self.show_password.stateChanged.connect(self._toggle_password_visibility)

        self.submit_button = QPushButton("Create Vault" if self._is_first_run else "Unlock Vault")
        self.submit_button.clicked.connect(self._on_submit)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.logo_label)
        layout.addWidget(title)
        layout.addWidget(self.subtitle_label)
        layout.addWidget(self.warning_label)
        layout.addWidget(self.unrecoverable_ack_checkbox)
        layout.addWidget(self.password_one_input)
        layout.addWidget(self.password_two_input)
        layout.addWidget(self.confirm_one_input)
        layout.addWidget(self.confirm_two_input)
        layout.addWidget(self.show_password)
        layout.addWidget(self.submit_button)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def _toggle_password_visibility(self) -> None:
        mode = QLineEdit.EchoMode.Normal if self.show_password.isChecked() else QLineEdit.EchoMode.Password
        self.password_one_input.setEchoMode(mode)
        self.password_two_input.setEchoMode(mode)
        self.confirm_one_input.setEchoMode(mode)
        self.confirm_two_input.setEchoMode(mode)

    def _on_submit(self) -> None:
        password_one = self.password_one_input.text()
        password_two = self.password_two_input.text()
        if not password_one or not password_two:
            self._set_status("Both passwords are required.", is_error=True)
            return

        if password_one == password_two:
            self._set_status("Password 1 and Password 2 must be different.", is_error=True)
            return

        if self._is_first_run:
            if not self.unrecoverable_ack_checkbox.isChecked():
                self._set_status("Please confirm the unrecoverable warning to continue.", is_error=True)
                return

            confirm_one = self.confirm_one_input.text()
            confirm_two = self.confirm_two_input.text()

            if password_one != confirm_one:
                self._set_status("Password 1 does not match confirmation.", is_error=True)
                return
            if password_two != confirm_two:
                self._set_status("Password 2 does not match confirmation.", is_error=True)
                return
            try:
                recovery_codes = self._auth_manager.setup_master_passwords(password_one, password_two)
                dialog = RecoveryCodeDialog(recovery_codes, self)
                dialog.exec()
                self._set_status("Recovery codes saved successfully.", is_error=False)
                self.authenticated.emit(self._auth_manager.combine_passwords(password_one, password_two))
                self._clear_fields()
            except AuthenticationError as exc:
                self._set_status(str(exc), is_error=True)
            return

        try:
            combined_secret = self._auth_manager.unlock_master_secret(password_one, password_two)
        except AuthenticationError as exc:
            self._set_status(str(exc), is_error=True)
            return

        self.authenticated.emit(combined_secret)
        self._clear_fields()

    def _set_status(self, message: str, is_error: bool) -> None:
        color = "#ff5f56" if is_error else "#8be9fd"
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color};")

    def _clear_fields(self) -> None:
        self.password_one_input.clear()
        self.password_two_input.clear()
        self.confirm_one_input.clear()
        self.confirm_two_input.clear()
        self.unrecoverable_ack_checkbox.setChecked(False)
        self.status_label.clear()

    def reset_mode(self) -> None:
        self._is_first_run = not self._auth_manager.is_initialized()
        self.confirm_one_input.setVisible(self._is_first_run)
        self.confirm_two_input.setVisible(self._is_first_run)
        self.submit_button.setText("Create Vault" if self._is_first_run else "Unlock Vault")
        subtitle_text = "Create your two vault passwords" if self._is_first_run else "Enter both vault passwords"
        self.subtitle_label.setText(subtitle_text)
        self.warning_label.setVisible(self._is_first_run)
        self.unrecoverable_ack_checkbox.setVisible(self._is_first_run)
        self._clear_fields()

    def _apply_dark_theme(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background-color: #121417;
                color: #e6edf3;
                font-size: 13px;
            }
            QLineEdit {
                background-color: #1f242d;
                border: 1px solid #2d333b;
                border-radius: 6px;
                padding: 8px;
                color: #e6edf3;
            }
            QPushButton {
                background-color: #238636;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2ea043;
            }
            """
        )


class VaultWindow(QMainWindow):
    lock_requested = Signal()

    def __init__(self, config_manager: ConfigManager, master_password: str) -> None:
        super().__init__()
        self._config_manager = config_manager
        self._master_password = master_password
        self._last_activity = time.monotonic()
        self._timeout_seconds = 120

        self.setWindowTitle(f"Smart File Vault v{APP_VERSION} (Free)")
        self.resize(760, 500)
        self.setAcceptDrops(True)

        self._build_ui()
        self._apply_dark_theme()
        self.refresh_vault_files()
        self._start_inactivity_monitor()

    def _build_ui(self) -> None:
        container = QWidget()
        root = QVBoxLayout()

        logo_row = QHBoxLayout()
        logo_row.addStretch()
        self.logo_label = QLabel()
        logo_path = Path(__file__).parent / "appLogo.png"
        if logo_path.exists():
            logo_pixmap = QPixmap(str(logo_path))
            if not logo_pixmap.isNull():
                self.logo_label.setPixmap(
                    logo_pixmap.scaled(
                        200,
                        200,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_row.addWidget(self.logo_label)
        logo_row.addStretch()

        top_row = QHBoxLayout()
        self.encrypt_btn = QPushButton("Encrypt File")
        self.decrypt_btn = QPushButton("Decrypt File")
        self.lock_btn = QPushButton("Lock Vault")
        self.about_btn = QPushButton("About")
        self.delete_original_checkbox = QCheckBox("Delete original after encryption")
        self.capacity_label = QLabel("")
        self.capacity_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)

        self.encrypt_btn.clicked.connect(self._encrypt_from_dialog)
        self.decrypt_btn.clicked.connect(self._decrypt_selected)
        self.lock_btn.clicked.connect(self.lock_requested.emit)
        self.about_btn.clicked.connect(self._show_about_popup)

        top_row.addWidget(self.encrypt_btn)
        top_row.addWidget(self.decrypt_btn)
        top_row.addWidget(self.lock_btn)
        top_row.addWidget(self.about_btn)
        top_row.addStretch()
        top_row.addWidget(self.capacity_label)
        top_row.addWidget(self.delete_original_checkbox)

        self.vault_list = QListWidget()
        self.vault_list.itemDoubleClicked.connect(self._decrypt_selected)

        self.status_label = QLabel("Drag and drop files into this window to encrypt.")

        root.addLayout(logo_row)
        root.addLayout(top_row)
        root.addWidget(self.vault_list)
        root.addWidget(self.progress_bar)
        root.addWidget(self.status_label)

        container.setLayout(root)
        self.setCentralWidget(container)

    def _start_inactivity_monitor(self) -> None:
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_inactivity)
        self._timer.start(5000)

    def _check_inactivity(self) -> None:
        if time.monotonic() - self._last_activity >= self._timeout_seconds:
            self._set_status("Vault locked due to inactivity.", is_error=False)
            self.lock_requested.emit()

    def eventFilter(self, watched, event):  # type: ignore[override]
        if event.type() in {
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.KeyPress,
            QEvent.Type.Wheel,
        }:
            self._touch_activity()
        return super().eventFilter(watched, event)

    def _touch_activity(self) -> None:
        self._last_activity = time.monotonic()

    def dragEnterEvent(self, event):  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):  # type: ignore[override]
        paths: list[Path] = []
        for url in event.mimeData().urls():
            file_path = Path(url.toLocalFile())
            if file_path.is_file():
                paths.append(file_path)

        if not paths:
            self._set_status("No valid files dropped.", is_error=True)
            return

        self._encrypt_files(paths)

    def _encrypt_from_dialog(self) -> None:
        self._touch_activity()
        files, _ = QFileDialog.getOpenFileNames(self, "Select files to encrypt")
        if not files:
            return
        self._encrypt_files([Path(item) for item in files])

    def _encrypt_files(self, files: list[Path]) -> None:
        self._touch_activity()
        current_vault_files = list(self._config_manager.vault_dir.glob("*.vault"))
        remaining_slots = FREE_ENCRYPTED_FILE_LIMIT - len(current_vault_files)

        if remaining_slots <= 0:
            self._set_status(
                f"Free version limit reached: maximum {FREE_ENCRYPTED_FILE_LIMIT} encrypted files.",
                is_error=True,
            )
            return

        queued_files = files[:remaining_slots]
        skipped_count = max(0, len(files) - len(queued_files))

        encrypted_count = 0
        errors: list[str] = []
        total_bytes = sum(file_path.stat().st_size for file_path in queued_files)
        total_bytes = max(total_bytes, 1)

        self._set_busy(True)
        self._start_progress(total_bytes, "Encrypting files")

        try:
            processed_bytes = 0
            for file_path in queued_files:
                file_size = file_path.stat().st_size
                self._set_status(f"Encrypting {file_path.name}...", is_error=False)
                try:
                    encrypt_file(
                        source_path=file_path,
                        master_password=self._master_password,
                        vault_dir=self._config_manager.vault_dir,
                        delete_original=self.delete_original_checkbox.isChecked(),
                        progress_callback=lambda done, _total, base=processed_bytes: self._update_progress(
                            min(base + done, total_bytes)
                        ),
                    )
                    encrypted_count += 1
                    processed_bytes += file_size
                    self._update_progress(min(processed_bytes, total_bytes))
                except CryptoError as exc:
                    errors.append(f"{file_path.name}: {exc}")
                except Exception as exc:
                    errors.append(f"{file_path.name}: {exc}")
        finally:
            self._finish_progress()
            self._set_busy(False)

        self.refresh_vault_files()

        if errors:
            message = f"Encrypted {encrypted_count} file(s), {len(errors)} failed."
            if skipped_count:
                message += f" {skipped_count} skipped due to free limit ({FREE_ENCRYPTED_FILE_LIMIT})."
            self._set_status(message, is_error=True)
            QMessageBox.warning(self, "Encryption Issues", "\n".join(errors[:8]))
        else:
            message = f"Encrypted {encrypted_count} file(s)."
            if skipped_count:
                message += f" {skipped_count} skipped due to free limit ({FREE_ENCRYPTED_FILE_LIMIT})."
            self._set_status(message, is_error=False)

    def _decrypt_selected(self, *_args) -> None:
        self._touch_activity()
        item = self.vault_list.currentItem()
        if item is None:
            self._set_status("Select a vault file to decrypt.", is_error=True)
            return

        vault_path = Path(item.data(Qt.ItemDataRole.UserRole))
        output_dir = QFileDialog.getExistingDirectory(self, "Select output folder")
        if not output_dir:
            return

        try:
            vault_size = max(vault_path.stat().st_size, 1)
            self._set_busy(True)
            self._start_progress(vault_size, f"Decrypting {vault_path.name}")
            output_file = decrypt_file(
                vault_path,
                self._master_password,
                Path(output_dir),
                progress_callback=lambda done, _total: self._update_progress(min(done, vault_size)),
            )
            self._set_status(f"Decrypted to: {output_file}", is_error=False)
        except CryptoError as exc:
            self._set_status(str(exc), is_error=True)
        except Exception as exc:
            self._set_status(f"Decryption failed: {exc}", is_error=True)
        finally:
            self._finish_progress()
            self._set_busy(False)

    def _show_about_popup(self) -> None:
        about = QMessageBox(self)
        about.setWindowTitle("About Smart File Vault")
        about.setIcon(QMessageBox.Icon.Information)
        about.setText(
            (
                f"Smart File Vault v{APP_VERSION}\n"
                f"Free version limit: up to {FREE_ENCRYPTED_FILE_LIMIT} encrypted files.\n\n"
                "Upgrade to Pro for unlimited encryption capacity.\n"
                "Feedback: https://devopsrite.vercel.app/"
            )
        )
        open_feedback_btn = about.addButton("Open Feedback", QMessageBox.ButtonRole.ActionRole)
        about.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        about.exec()

        if about.clickedButton() == open_feedback_btn:
            QDesktopServices.openUrl(QUrl("https://devopsrite.vercel.app/"))

    def refresh_vault_files(self) -> None:
        self.vault_list.clear()
        self._config_manager.vault_dir.mkdir(parents=True, exist_ok=True)

        vault_files = sorted(self._config_manager.vault_dir.glob("*.vault"))
        for file_path in vault_files:
            item = QListWidgetItem(file_path.name)
            item.setData(Qt.ItemDataRole.UserRole, str(file_path))
            self.vault_list.addItem(item)

        used_count = len(vault_files)
        self.capacity_label.setText(f"{used_count}/{FREE_ENCRYPTED_FILE_LIMIT} used")

    def _set_status(self, message: str, is_error: bool) -> None:
        color = "#ff5f56" if is_error else "#8be9fd"
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color};")

    def _set_busy(self, busy: bool) -> None:
        widgets = [
            self.encrypt_btn,
            self.decrypt_btn,
            self.lock_btn,
            self.about_btn,
            self.delete_original_checkbox,
        ]
        for widget in widgets:
            widget.setEnabled(not busy)

    def _start_progress(self, total_units: int, label: str) -> None:
        self.progress_bar.setRange(0, max(total_units, 1))
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(f"{label} %p%")
        self.progress_bar.setVisible(True)
        QApplication.processEvents()

    def _update_progress(self, value: int) -> None:
        self.progress_bar.setValue(value)
        QApplication.processEvents()

    def _finish_progress(self) -> None:
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.progress_bar.setVisible(False)
        QApplication.processEvents()

    def _apply_dark_theme(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background-color: #0d1117;
                color: #e6edf3;
                font-size: 13px;
            }
            QListWidget {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 4px;
            }
            QPushButton {
                background-color: #1f6feb;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #388bfd;
            }
            QCheckBox {
                color: #e6edf3;
            }
            """
        )

    def closeEvent(self, event):  # type: ignore[override]
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        super().closeEvent(event)
