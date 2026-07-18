"""SQLite memoization layer for expensive CEA/Cantera calls.

Default database path: ``~/.propwrap/cache.db``.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

DEFAULT_CACHE_PATH = Path.home() / ".propwrap" / "cache.db"


def default_cache_path() -> Path:
    return DEFAULT_CACHE_PATH


class ResultCache:
    """Transparent SQLite cache for pydantic model payloads."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else default_cache_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path))
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS results (
                    cache_key TEXT PRIMARY KEY,
                    model_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.commit()

    @staticmethod
    def make_key(
        fuel: str,
        oxidizer: str,
        of_ratio: float,
        pc_bar: float,
        eps: float,
        fuel_temp_k: float | None,
        ox_temp_k: float | None,
        method: str,
        **extra: Any,
    ) -> str:
        """Build a stable SHA-256 cache key from call parameters."""
        payload = {
            "fuel": fuel,
            "oxidizer": oxidizer,
            "of_ratio": round(float(of_ratio), 10),
            "pc_bar": round(float(pc_bar), 10),
            "eps": round(float(eps), 10),
            "fuel_temp_k": None if fuel_temp_k is None else round(float(fuel_temp_k), 6),
            "ox_temp_k": None if ox_temp_k is None else round(float(ox_temp_k), 6),
            "method": method,
            **extra,
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def get(self, key: str, model_cls: type[T]) -> T | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM results WHERE cache_key = ?", (key,)
            ).fetchone()
        if row is None:
            return None
        return model_cls.model_validate_json(row[0])

    def set(self, key: str, value: BaseModel) -> None:
        payload = value.model_dump_json()
        model_type = type(value).__name__
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO results (cache_key, model_type, payload, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (key, model_type, payload, time.time()),
            )
            conn.commit()

    def clear(self) -> int:
        """Delete all cache entries. Returns number of rows removed."""
        with self._connect() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM results")
            n = int(cur.fetchone()[0])
            conn.execute("DELETE FROM results")
            conn.commit()
        return n


# Process-wide default instance (lazy)
_default_cache: ResultCache | None = None


def get_default_cache() -> ResultCache:
    global _default_cache
    if _default_cache is None:
        _default_cache = ResultCache()
    return _default_cache


def clear_default_cache() -> int:
    """Clear the default cache database. Returns rows deleted."""
    return get_default_cache().clear()
