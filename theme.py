"""Curated, pick-one customization -- not a full RGB picker or a font
browser. A grid of ready-made palettes and a short list of fonts keeps the
settings screen to two taps, matching the "shouldn't require a lot of
things" brief, while still giving real visual variety.
"""
from __future__ import annotations

from pathlib import Path
from typing import TypedDict

FONTS_DIR = Path(__file__).resolve().parent / "assets" / "fonts"


class Palette(TypedDict):
    name: str
    background: str
    card: str
    accent: str
    text: str
    subtext: str


# Each color is a hex string. `background` is the screen behind the card,
# `card` is the quote card itself, `accent` is used for buttons/highlights,
# `text`/`subtext` are the quote text and the smaller intro/reflection/author
# lines respectively.
PALETTES: list[Palette] = [
    {
        "name": "Sunrise Peach",
        "background": "#FFF3E9",
        "card": "#FFFFFF",
        "accent": "#F4A261",
        "text": "#3D2C21",
        "subtext": "#8C6F5E",
    },
    {
        "name": "Calm Lavender",
        "background": "#F1EEFB",
        "card": "#FFFFFF",
        "accent": "#8E7CC3",
        "text": "#332E4A",
        "subtext": "#7B7396",
    },
    {
        "name": "Sage Green",
        "background": "#EEF3EC",
        "card": "#FFFFFF",
        "accent": "#7A9E7E",
        "text": "#2E3B2F",
        "subtext": "#6E7F70",
    },
    {
        "name": "Ocean Mist",
        "background": "#EAF4F6",
        "card": "#FFFFFF",
        "accent": "#4F98A8",
        "text": "#233A3E",
        "subtext": "#5F7D82",
    },
    {
        "name": "Golden Hour",
        "background": "#FFF8E1",
        "card": "#FFFFFF",
        "accent": "#E6B800",
        "text": "#4A3B00",
        "subtext": "#8A7A3D",
    },
    {
        "name": "Rose Quartz",
        "background": "#FBEEEF",
        "card": "#FFFFFF",
        "accent": "#D98A93",
        "text": "#4A2C2F",
        "subtext": "#8C6E71",
    },
    {
        "name": "Classic Cream",
        "background": "#FAF6EF",
        "card": "#FFFFFF",
        "accent": "#B08968",
        "text": "#3A2E22",
        "subtext": "#7C6A57",
    },
    {
        "name": "Midnight",
        "background": "#1B1B2A",
        "card": "#262639",
        "accent": "#7C9CFF",
        "text": "#EDEDF7",
        "subtext": "#A6A6C1",
    },
]

DEFAULT_PALETTE_NAME = "Sunrise Peach"


class FontOption(TypedDict):
    label: str
    file: str
    feel: str


FONTS: list[FontOption] = [
    {
        "label": "Poppins",
        "file": str(FONTS_DIR / "poppins" / "Poppins-Regular.ttf"),
        "feel": "Clean and modern",
    },
    {
        "label": "Playfair Display",
        "file": str(FONTS_DIR / "playfair" / "PlayfairDisplay.ttf"),
        "feel": "Elegant, classic",
    },
    {
        "label": "Caveat",
        "file": str(FONTS_DIR / "caveat" / "Caveat.ttf"),
        "feel": "Handwritten, personal",
    },
    {
        "label": "Merriweather",
        "file": str(FONTS_DIR / "merriweather" / "Merriweather.ttf"),
        "feel": "Warm and readable",
    },
    {
        "label": "Quicksand",
        "file": str(FONTS_DIR / "quicksand" / "Quicksand.ttf"),
        "feel": "Friendly, rounded",
    },
]

DEFAULT_FONT_LABEL = "Poppins"


def get_palette(name: str) -> Palette:
    for p in PALETTES:
        if p["name"] == name:
            return p
    return next(p for p in PALETTES if p["name"] == DEFAULT_PALETTE_NAME)


def get_font(label: str) -> FontOption:
    for f in FONTS:
        if f["label"] == label:
            return f
    return next(f for f in FONTS if f["label"] == DEFAULT_FONT_LABEL)
