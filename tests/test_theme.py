import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from theme import DEFAULT_FONT_LABEL, DEFAULT_PALETTE_NAME, FONTS, PALETTES, get_font, get_palette


def test_default_palette_exists_in_list():
    names = [p["name"] for p in PALETTES]
    assert DEFAULT_PALETTE_NAME in names


def test_default_font_exists_in_list():
    labels = [f["label"] for f in FONTS]
    assert DEFAULT_FONT_LABEL in labels


def test_get_palette_returns_requested_palette():
    p = get_palette("Midnight")
    assert p["name"] == "Midnight"


def test_get_palette_falls_back_to_default_for_unknown_name():
    p = get_palette("Not A Real Palette")
    assert p["name"] == DEFAULT_PALETTE_NAME


def test_get_font_returns_requested_font():
    f = get_font("Caveat")
    assert f["label"] == "Caveat"


def test_get_font_falls_back_to_default_for_unknown_label():
    f = get_font("Not A Real Font")
    assert f["label"] == DEFAULT_FONT_LABEL


def test_all_palettes_have_required_color_keys():
    required = {"name", "background", "card", "accent", "text", "subtext"}
    for p in PALETTES:
        assert required.issubset(p.keys())
        for key in required - {"name"}:
            assert p[key].startswith("#"), f"{p['name']}.{key} isn't a hex color: {p[key]}"


def test_all_font_files_exist_on_disk():
    for f in FONTS:
        path = Path(f["file"])
        assert path.exists(), f"font file missing: {path}"
        assert path.stat().st_size > 1000, f"font file suspiciously small: {path}"
