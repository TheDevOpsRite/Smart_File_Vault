from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config import ConfigData, ConfigManager


class AuthenticationError(Exception):
    pass


AUTH_VERIFIER_ITERATIONS = 390000
RECOVERY_CODE_COUNT = 3
RECOVERY_FIELD_PREFIX = "SFVREC"
RECOVERY_KEY_SIZE = 32
RECOVERY_NONCE_SIZE = 12
RECOVERY_AAD = b"Smart File Vault recovery"
GF257 = 257


@dataclass(frozen=True)
class RecoveryShare:
    x: int
    values: bytes


class AuthManager:
    def __init__(self, config_manager: ConfigManager) -> None:
        self._config_manager = config_manager

    def is_initialized(self) -> bool:
        return self._config_manager.is_initialized()

    def setup_master_passwords(self, password_one: str, password_two: str) -> list[str]:
        if password_one == password_two:
            raise AuthenticationError("Password 1 and Password 2 must be different.")

        self._validate_password_strength(password_one, "Password 1")
        self._validate_password_strength(password_two, "Password 2")

        combined_secret = self.combine_passwords(password_one, password_two)
        salt = os.urandom(16)
        password_hash = self._hash_password(combined_secret, salt)

        recovery_secret = os.urandom(RECOVERY_KEY_SIZE)
        recovery_codes = self._generate_recovery_codes(recovery_secret)
        recovery_nonce = os.urandom(RECOVERY_NONCE_SIZE)
        wrapped_secret = AESGCM(recovery_secret).encrypt(
            recovery_nonce,
            combined_secret.encode("utf-8"),
            RECOVERY_AAD,
        )

        config = ConfigData(
            password_hash=base64.urlsafe_b64encode(password_hash).decode("utf-8"),
            auth_salt=base64.urlsafe_b64encode(salt).decode("utf-8"),
            failed_attempts=0,
            recovery_nonce=base64.urlsafe_b64encode(recovery_nonce).decode("utf-8"),
            recovery_wrapped_secret=base64.urlsafe_b64encode(wrapped_secret).decode("utf-8"),
        )
        self._config_manager.save(config)
        return recovery_codes

    def unlock_master_secret(self, password_one: str, password_two: str) -> str:
        if password_one == password_two:
            raise AuthenticationError("Password 1 and Password 2 must be different.")

        config = self._config_manager.load()
        if not config.password_hash or not config.auth_salt:
            raise AuthenticationError("Vault is not initialized.")

        combined_secret = self.combine_passwords(password_one, password_two)
        if self._verify_master_secret(combined_secret, config):
            config.failed_attempts = 0
            self._config_manager.save(config)
            return combined_secret

        if config.recovery_nonce and config.recovery_wrapped_secret:
            try:
                recovered_secret = self._recover_master_secret(password_one, password_two, config)
                config.failed_attempts = 0
                self._config_manager.save(config)
                return recovered_secret
            except AuthenticationError:
                pass

        config.failed_attempts = min(config.failed_attempts + 1, 10)
        self._config_manager.save(config)

        delay_seconds = min(2 ** config.failed_attempts, 30)
        time.sleep(delay_seconds)
        raise AuthenticationError("Invalid password or recovery codes.")

    def verify_passwords(self, password_one: str, password_two: str) -> bool:
        self.unlock_master_secret(password_one, password_two)
        return True

    def export_recovery_codes(self, recovery_codes: list[str]) -> Path:
        self._config_manager.ensure_directories()
        recovery_file = self._config_manager.config_dir / "recovery-codes.txt"
        contents = "\n".join(
            [
                "Smart File Vault recovery codes",
                "",
                "Store these codes safely. Any two codes can recover the vault.",
                "",
            ]
            + recovery_codes
            + [""]
        )
        recovery_file.write_text(contents, encoding="utf-8")
        return recovery_file

    @staticmethod
    def combine_passwords(password_one: str, password_two: str) -> str:
        return f"{len(password_one)}:{password_one}|{len(password_two)}:{password_two}"

    @staticmethod
    def _validate_password_strength(password: str, label: str) -> None:
        if len(password) < 8:
            raise AuthenticationError(f"{label} must be at least 8 characters.")
        if not re.search(r"[A-Z]", password):
            raise AuthenticationError(f"{label} must include at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            raise AuthenticationError(f"{label} must include at least one lowercase letter.")
        if not re.search(r"\d", password):
            raise AuthenticationError(f"{label} must include at least one number.")
        if not re.search(r"[^A-Za-z0-9]", password):
            raise AuthenticationError(f"{label} must include at least one special character.")

    @staticmethod
    def _hash_password(password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            AUTH_VERIFIER_ITERATIONS,
            dklen=32,
        )

    @staticmethod
    def _legacy_hash_password(password: str, salt: bytes) -> bytes:
        hasher = hashlib.sha256()
        hasher.update(salt)
        hasher.update(password.encode("utf-8"))
        return hasher.digest()

    def _verify_master_secret(self, combined_secret: str, config: ConfigData) -> bool:
        try:
            stored_hash = base64.urlsafe_b64decode(config.password_hash.encode("utf-8"))
            salt = base64.urlsafe_b64decode(config.auth_salt.encode("utf-8"))
        except Exception as exc:
            raise AuthenticationError("Invalid authentication data.") from exc

        candidate_hash = self._hash_password(combined_secret, salt)
        if hmac.compare_digest(stored_hash, candidate_hash):
            return True

        legacy_hash = self._legacy_hash_password(combined_secret, salt)
        if hmac.compare_digest(stored_hash, legacy_hash):
            config.password_hash = base64.urlsafe_b64encode(candidate_hash).decode("utf-8")
            self._config_manager.save(config)
            return True

        return False

    @staticmethod
    def _generate_recovery_codes(recovery_secret: bytes) -> list[str]:
        if len(recovery_secret) != RECOVERY_KEY_SIZE:
            raise AuthenticationError("Invalid recovery secret length.")

        coefficients = [os.urandom(2) for _ in range(len(recovery_secret))]
        recovery_codes: list[str] = []

        for x_value in range(1, RECOVERY_CODE_COUNT + 1):
            share_bytes = bytearray()
            for index, secret_byte in enumerate(recovery_secret):
                coefficient = int.from_bytes(coefficients[index], "big") % GF257
                share_value = (secret_byte + coefficient * x_value) % GF257
                share_bytes.extend(share_value.to_bytes(2, "big"))
            encoded_share = base64.urlsafe_b64encode(bytes(share_bytes)).decode("utf-8")
            recovery_codes.append(f"{RECOVERY_FIELD_PREFIX}-{x_value}-{encoded_share}")

        return recovery_codes

    @staticmethod
    def _decode_recovery_share(code: str) -> RecoveryShare:
        parts = code.strip().split("-", 2)
        if len(parts) != 3 or parts[0] != RECOVERY_FIELD_PREFIX:
            raise AuthenticationError("Invalid recovery code format.")

        try:
            x_value = int(parts[1])
        except ValueError as exc:
            raise AuthenticationError("Invalid recovery code format.") from exc

        if x_value < 1 or x_value > RECOVERY_CODE_COUNT:
            raise AuthenticationError("Invalid recovery code format.")

        try:
            share_blob = base64.urlsafe_b64decode(parts[2].encode("utf-8"))
        except Exception as exc:
            raise AuthenticationError("Invalid recovery code format.") from exc

        if len(share_blob) % 2 != 0:
            raise AuthenticationError("Invalid recovery code format.")

        values = bytes(
            int.from_bytes(share_blob[index : index + 2], "big")
            for index in range(0, len(share_blob), 2)
        )
        return RecoveryShare(x=x_value, values=values)

    @staticmethod
    def _reconstruct_recovery_secret(share_one: RecoveryShare, share_two: RecoveryShare) -> bytes:
        if share_one.x == share_two.x:
            raise AuthenticationError("Recovery codes must be different.")
        if len(share_one.values) != len(share_two.values):
            raise AuthenticationError("Invalid recovery code format.")

        denominator = (share_two.x - share_one.x) % GF257
        try:
            denominator_inverse = pow(denominator, -1, GF257)
        except ValueError as exc:
            raise AuthenticationError("Invalid recovery codes.") from exc

        secret = bytearray()
        for value_one, value_two in zip(share_one.values, share_two.values):
            recovered = ((share_two.x * value_one) - (share_one.x * value_two)) * denominator_inverse
            secret.append(recovered % GF257)
        return bytes(secret)

    def _recover_master_secret(self, password_one: str, password_two: str, config: ConfigData) -> str:
        share_one = self._decode_recovery_share(password_one)
        share_two = self._decode_recovery_share(password_two)
        recovery_secret = self._reconstruct_recovery_secret(share_one, share_two)

        try:
            nonce = base64.urlsafe_b64decode(config.recovery_nonce.encode("utf-8"))
            wrapped_secret = base64.urlsafe_b64decode(config.recovery_wrapped_secret.encode("utf-8"))
        except Exception as exc:
            raise AuthenticationError("Recovery data is invalid.") from exc

        try:
            recovered_secret = AESGCM(recovery_secret).decrypt(nonce, wrapped_secret, RECOVERY_AAD)
        except Exception as exc:
            raise AuthenticationError("Invalid recovery codes.") from exc

        return recovered_secret.decode("utf-8")
