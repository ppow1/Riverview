"""DPAPI-backed PostgreSQL connection boundary.

Version: 0.2.1
"""

from __future__ import annotations

import ctypes
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg

DEFAULT_METADATA = Path(r"A:\Riverview\data\secrets\postgresql\credential-metadata.json")


class DataBlob(ctypes.Structure):
    """Windows DATA_BLOB used by CryptUnprotectData."""

    _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    """Non-secret connection settings plus the recovered application password."""

    host: str
    port: int
    database: str
    user: str
    password: str


def _unprotect_dpapi(ciphertext_hex: str) -> str:
    if os.name != "nt":
        raise RuntimeError("RIV-DB-0003: DPAPI credentials require the provisioning Windows user.")
    encrypted = bytes.fromhex(ciphertext_hex.strip())
    buffer = ctypes.create_string_buffer(encrypted)
    source = DataBlob(len(encrypted), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    destination = DataBlob()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    if not crypt32.CryptUnprotectData(
        ctypes.byref(source), None, None, None, None, 0, ctypes.byref(destination)
    ):
        raise RuntimeError(f"RIV-DB-0003: DPAPI recovery failed with Windows error {ctypes.GetLastError()}.")
    try:
        raw = ctypes.string_at(destination.pbData, destination.cbData)
        return raw.decode("utf-16-le")
    finally:
        kernel32.LocalFree(destination.pbData)


def load_database_config(metadata_path: Path = DEFAULT_METADATA) -> DatabaseConfig:
    """Load metadata and recover the application credential for the current user."""

    try:
        metadata: dict[str, Any] = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        secret_path = Path(metadata["application_secret"])
        password = _unprotect_dpapi(secret_path.read_text(encoding="ascii"))
        return DatabaseConfig(
            host=str(metadata["host"]),
            port=int(metadata["port"]),
            database=str(metadata["database"]),
            user=str(metadata["application_role"]),
            password=password,
        )
    except RuntimeError:
        raise
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"RIV-DB-0002: Credential configuration is invalid: {exc}") from exc


@contextmanager
def connect(config: DatabaseConfig | None = None) -> Iterator[psycopg.Connection[Any]]:
    """Open a transaction-scoped database connection."""

    active = config or load_database_config()
    try:
        with psycopg.connect(
            host=active.host,
            port=active.port,
            dbname=active.database,
            user=active.user,
            password=active.password,
            connect_timeout=5,
        ) as connection:
            yield connection
    except psycopg.Error as exc:
        raise RuntimeError(f"RIV-DB-0004: PostgreSQL connection or transaction failed: {exc}") from exc