import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from quote_engine import DailyState
from storage import Storage, default_settings


def _tmp_storage() -> Storage:
    tmp_dir = Path(tempfile.mkdtemp())
    return Storage(path=tmp_dir / "data.json")


def test_load_settings_returns_defaults_when_no_file_exists():
    storage = _tmp_storage()
    settings = storage.load_settings()
    assert settings == default_settings()


def test_save_and_load_settings_roundtrip():
    storage = _tmp_storage()
    settings = default_settings()
    settings["palette_name"] = "Midnight"
    settings["font_label"] = "Caveat"
    settings["font_size_sp"] = 30
    storage.save_settings(settings)

    loaded = storage.load_settings()
    assert loaded["palette_name"] == "Midnight"
    assert loaded["font_label"] == "Caveat"
    assert loaded["font_size_sp"] == 30


def test_save_settings_partial_update_fills_in_defaults():
    storage = _tmp_storage()
    storage.save_settings({"palette_name": "Sage Green"})
    loaded = storage.load_settings()
    # missing keys from that save should still resolve via defaults on next load
    assert loaded["palette_name"] == "Sage Green"
    assert "font_label" in loaded


def test_state_roundtrips():
    storage = _tmp_storage()
    state = DailyState(shuffle_order=[2, 0, 1], cursor=1, last_date="2026-01-02", current_quote_index=0, streak=3)
    storage.save_state(state)

    loaded = storage.load_state()
    assert loaded == state


def test_load_state_returns_empty_state_when_no_file_exists():
    storage = _tmp_storage()
    state = storage.load_state()
    assert state.shuffle_order == []
    assert state.last_date is None


def test_settings_and_state_coexist_in_same_file():
    storage = _tmp_storage()
    storage.save_settings({"palette_name": "Ocean Mist"})
    storage.save_state(DailyState(current_quote_index=5, last_date="2026-01-01"))

    # saving one shouldn't wipe out the other
    settings = storage.load_settings()
    state = storage.load_state()
    assert settings["palette_name"] == "Ocean Mist"
    assert state.current_quote_index == 5


def test_corrupt_file_does_not_crash_load():
    storage = _tmp_storage()
    storage.path.write_text("{not valid json::")
    settings = storage.load_settings()
    assert settings == default_settings()
    state = storage.load_state()
    assert state.shuffle_order == []


def test_storage_creates_parent_directory():
    tmp_dir = Path(tempfile.mkdtemp()) / "nested" / "deeper"
    storage = Storage(path=tmp_dir / "data.json")
    storage.save_settings(default_settings())
    assert tmp_dir.exists()


def test_invalid_root_json_is_ignored_and_state_is_safe():
    storage = _tmp_storage()
    storage.path.write_text("[]")
    assert storage.load_settings() == default_settings()
    assert storage.load_state() == DailyState()

    storage.path.write_text('{"settings": ["not-a-dict"], "daily_state": [1, 2, 3]}')
    assert storage.load_settings() == default_settings()
    assert storage.load_state() == DailyState()
