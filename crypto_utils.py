from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Callable

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

PBKDF2_ITERATIONS = 390000
SALT_SIZE = 16
NONCE_SIZE = 12
CHUNK_SIZE = 1024 * 1024
FILE_FORMAT_VERSION = 2
ProgressCallback = Callable[[int, int], None]


class CryptoError(Exception):
    pass


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_file(
    source_path: Path,
    master_password: str,
    vault_dir: Path,
    delete_original: bool = False,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    if not source_path.exists() or not source_path.is_file():
        raise CryptoError("Selected file does not exist.")

    vault_dir.mkdir(parents=True, exist_ok=True)

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(master_password, salt)

    original_name = source_path.name
    total_bytes = source_path.stat().st_size
    processed_bytes = 0
    ciphertext_parts: list[bytes] = []

    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
    encryptor = cipher.encryptor()
    encryptor.authenticate_additional_data(original_name.encode("utf-8"))

    with source_path.open("rb") as handle:
        while True:
            chunk = handle.read(CHUNK_SIZE)
            if not chunk:
                break
            ciphertext_parts.append(encryptor.update(chunk))
            processed_bytes += len(chunk)
            if progress_callback is not None:
                progress_callback(processed_bytes, total_bytes)

    ciphertext_parts.append(encryptor.finalize())
    ciphertext = b"".join(ciphertext_parts)
    if progress_callback is not None:
        progress_callback(total_bytes, total_bytes)

    payload = {
        "v": FILE_FORMAT_VERSION,
        "salt": base64.urlsafe_b64encode(salt).decode("utf-8"),
        "nonce": base64.urlsafe_b64encode(nonce).decode("utf-8"),
        "tag": base64.urlsafe_b64encode(encryptor.tag).decode("utf-8"),
        "name": original_name,
        "data": base64.urlsafe_b64encode(ciphertext).decode("utf-8"),
    }

    destination = vault_dir / f"{source_path.name}.vault"
    destination.write_text(json.dumps(payload), encoding="utf-8")

    if delete_original:
        secure_delete(source_path)

    return destination


def decrypt_file(
    vault_file: Path,
    master_password: str,
    output_path: Path,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    if not vault_file.exists() or not vault_file.is_file():
        raise CryptoError("Encrypted file does not exist.")

    try:
        payload = json.loads(vault_file.read_text(encoding="utf-8"))
        salt = base64.urlsafe_b64decode(payload["salt"])
        nonce = base64.urlsafe_b64decode(payload["nonce"])
        ciphertext = base64.urlsafe_b64decode(payload["data"])
        original_name = str(payload["name"])
        tag = payload.get("tag")
    except Exception as exc:
        raise CryptoError("Invalid encrypted file format.") from exc

    key = derive_key(master_password, salt)
    final_output = output_path
    if output_path.is_dir():
        final_output = output_path / original_name

    final_output.parent.mkdir(parents=True, exist_ok=True)

    if tag:
        try:
            tag_bytes = base64.urlsafe_b64decode(tag)
        except Exception as exc:
            raise CryptoError("Invalid encrypted file format.") from exc

        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag_bytes))
        decryptor = cipher.decryptor()
        decryptor.authenticate_additional_data(original_name.encode("utf-8"))

        processed_bytes = 0
        with final_output.open("wb") as handle:
            for offset in range(0, len(ciphertext), CHUNK_SIZE):
                chunk = ciphertext[offset : offset + CHUNK_SIZE]
                handle.write(decryptor.update(chunk))
                processed_bytes += len(chunk)
                if progress_callback is not None:
                    progress_callback(processed_bytes, len(ciphertext))
            handle.write(decryptor.finalize())
        if progress_callback is not None:
            progress_callback(len(ciphertext), len(ciphertext))
        return final_output

    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, original_name.encode("utf-8"))
    except Exception as exc:
        raise CryptoError("Decryption failed. Incorrect password or corrupted file.") from exc

    if progress_callback is not None:
        progress_callback(len(ciphertext), len(ciphertext))

    final_output.write_bytes(plaintext)
    return final_output


def secure_delete(path: Path) -> None:
    if not path.exists() or not path.is_file():
        return

    size = path.stat().st_size
    with path.open("r+b") as handle:
        handle.write(os.urandom(size))
        handle.flush()
        os.fsync(handle.fileno())
    path.unlink(missing_ok=True)
