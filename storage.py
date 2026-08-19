"""Local persistence for settings (theme/font/API key) and daily state
(shuffle order, streak, today's picked quote).

Deliberately just one small JSON file, not a database -- there's very
little to store, and a human-readable file is easy to inspect/back up/edit
by hand if something needs fixing. Framework-agnostic (no Kivy import) so it
can be unit-tested directly; `main.py` is responsible for pointing it at the
right directory on Android (`App.user_data_dir`) vs. on desktop.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quote_engine import DailyState
from theme import DEFAULT_FONT_LABEL, DEFAULT_PALETTE_NAME

DEFAULT_DATA_DIR = Path.home() / ".quotes_app"
DEFAULT_DATA_PATH = DEFAULT_DATA_DIR / "data.json"


def default_settings() -> dict[str, Any]:
    return {
        "palette_name": DEFAULT_PALETTE_NAME,
        "font_label": DEFAULT_FONT_LABEL,
        "font_size_sp": 26,
        "anthropic_api_key": "",
    }


class Storage:
    def __init__(self, path: Path | str = DEFAULT_DATA_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read_raw(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            # Corrupt or unreadable file -- don't crash the app over a
            # damaged settings file, just start fresh.
            return {}

        if not isinstance(data, dict):
            return {}
        return data

    def _write_raw(self, data: dict[str, Any]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_settings(self) -> dict[str, Any]:
        raw = self._read_raw()
        settings = default_settings()
        saved = raw.get("settings", {})
        if isinstance(saved, dict):
            settings.update(saved)
        return settings

    def save_settings(self, settings: dict[str, Any]) -> None:
        raw = self._read_raw()
        if not isinstance(settings, dict):
            settings = {}
        raw["settings"] = settings
        self._write_raw(raw)

    def load_state(self) -> DailyState:
        raw = self._read_raw()
        saved = raw.get("daily_state", {})
        return DailyState.from_dict(saved if isinstance(saved, dict) else {})

    def save_state(self, state: DailyState) -> None:
        raw = self._read_raw()
        raw["daily_state"] = state.to_dict()
        self._write_raw(raw)
