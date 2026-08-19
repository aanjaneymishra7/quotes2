"""Picks and dresses up the quote of the day.

Two things happen here, and they're kept deliberately separate:

1. **Selection** (`get_daily_quote`) -- which quote is "today's quote".
   Deterministic per day (opening the app twice in one day shows the same
   quote), cycles through the whole bank via a shuffled order before any
   quote repeats, and reshuffles without letting the last quote of one cycle
   immediately repeat as the first of the next.

2. **Humanizing** (`compose_daily_message`) -- wrapping the raw quote with a
   short, warm intro line and a one-sentence reflection, both picked from
   pools that vary by the quote's `tag` and by the date, so the same quote
   shown on two different days (a full cycle apart) doesn't read identically
   and the app never sounds like it's reciting from a database.

No file/network/Kivy access happens in this module -- it's pure functions
over plain dicts, so it's fully unit-testable without a phone, a display, or
an internet connection.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from datetime import date as date_cls
from pathlib import Path
from typing import Any, Optional

QUOTES_PATH = Path(__file__).resolve().parent / "data" / "quotes.json"

INTROS = [
    "Here's something to carry with you today.",
    "A little something for today:",
    "Someone once put it well:",
    "Worth sitting with for a moment:",
    "For whatever today brings, this might help:",
    "A small nudge to start the day:",
    "Today's thought, for what it's worth:",
    "Carry this one with you:",
    "Here's a good one for today.",
    "Something worth remembering:",
]

REFLECTIONS: dict[str, list[str]] = {
    "perseverance": [
        "Not every day feels easy -- and that's alright, keep going anyway.",
        "Small, steady steps still get you there.",
        "Whatever pace you're moving at today is still progress.",
    ],
    "resilience": [
        "Bad days don't cancel out good ones. You're allowed to start over as many times as you need.",
        "Whatever knocked you down doesn't get the final word.",
        "You've made it through every hard day so far. That's worth noticing.",
    ],
    "self_belief": [
        "You know more than you give yourself credit for.",
        "Trust the part of you that got you this far.",
        "You don't need to have it all figured out to move forward.",
    ],
    "growth": [
        "Today doesn't have to be perfect to count.",
        "Every version of you got you here -- even the messy drafts.",
        "Growth rarely looks the way we expect it to.",
    ],
    "courage": [
        "It's okay if the first step feels shaky. Take it anyway.",
        "Brave doesn't mean fearless -- it means going anyway.",
        "You don't need permission to try.",
    ],
    "gratitude": [
        "Something small today is probably worth noticing.",
        "Even an ordinary day usually has one good moment hiding in it.",
        "It's okay to slow down long enough to appreciate today.",
    ],
    "kindness": [
        "A small kindness today costs little and travels far.",
        "Someone nearby could probably use exactly what you have to offer.",
        "Gentleness is still strength.",
    ],
    "new_beginnings": [
        "It's never too late for a fresh page.",
        "Today counts as a new start if you want it to.",
        "You don't need a perfect moment to begin -- just this one.",
    ],
    "calm": [
        "It's okay to slow down today.",
        "Not everything needs to be solved right now.",
        "A quiet moment today is not wasted time.",
    ],
    "purpose": [
        "Whatever you're building, today is one more brick.",
        "Small, purposeful choices add up more than they seem to.",
        "You don't need the whole plan -- just today's next right step.",
    ],
}

DEFAULT_REFLECTIONS = [
    "Take today one step at a time.",
    "Hope this finds you exactly when you need it.",
    "However today goes, you've got this.",
]


@dataclass
class DailyState:
    """Persisted, per-user state -- see storage.py for how this is saved."""

    shuffle_order: list[int] = field(default_factory=list)
    cursor: int = -1
    last_date: Optional[str] = None
    current_quote_index: Optional[int] = None
    streak: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "DailyState":
        if not isinstance(data, dict):
            return cls()

        shuffle_order = data.get("shuffle_order", [])
        if not isinstance(shuffle_order, list):
            shuffle_order = []

        cursor = data.get("cursor", -1)
        if not isinstance(cursor, int):
            cursor = -1

        last_date = data.get("last_date")
        if not isinstance(last_date, str) or not last_date:
            last_date = None

        current_quote_index = data.get("current_quote_index")
        if not isinstance(current_quote_index, int):
            current_quote_index = None

        streak = data.get("streak", 0)
        if not isinstance(streak, int):
            streak = 0

        return cls(
            shuffle_order=[int(value) for value in shuffle_order if isinstance(value, (int, float))],
            cursor=cursor,
            last_date=last_date,
            current_quote_index=current_quote_index,
            streak=streak,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "shuffle_order": self.shuffle_order,
            "cursor": self.cursor,
            "last_date": self.last_date,
            "current_quote_index": self.current_quote_index,
            "streak": self.streak,
        }


def load_quotes(path: Path = QUOTES_PATH) -> list[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            quotes = json.load(f)
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not load quotes from {path}") from exc

    if not isinstance(quotes, list):
        raise ValueError(f"Quotes file at {path} did not contain a JSON list")
    return quotes


def _reshuffle(quotes: list[dict], avoid_first_index: Optional[int] = None) -> list[int]:
    order = list(range(len(quotes)))
    random.shuffle(order)
    if avoid_first_index is not None and order and order[0] == avoid_first_index and len(order) > 1:
        # Don't let the new cycle's first pick be the same as the last
        # quote the person just saw -- swap it with something else.
        order[0], order[1] = order[1], order[0]
    return order


def get_daily_quote(
    quotes: list[dict],
    state: DailyState,
    today: Optional[date_cls] = None,
) -> tuple[dict, DailyState]:
    """Returns (today's quote, updated state). Pure function -- caller is
    responsible for persisting the returned state (see storage.py)."""
    if not quotes:
        raise ValueError("quotes list is empty")

    today = today or date_cls.today()
    today_str = today.isoformat()

    if state.last_date == today_str and state.current_quote_index is not None:
        # Already picked today's quote -- return the same one.
        return quotes[state.current_quote_index], state

    if not state.shuffle_order or state.cursor >= len(state.shuffle_order) - 1:
        last_index = (
            state.shuffle_order[state.cursor]
            if state.shuffle_order and 0 <= state.cursor < len(state.shuffle_order)
            else None
        )
        new_order = _reshuffle(quotes, avoid_first_index=last_index)
        cursor = 0
    else:
        new_order = state.shuffle_order
        cursor = state.cursor + 1

    new_index = new_order[cursor]

    # Streak: consecutive calendar days the app has been opened.
    if state.last_date:
        try:
            last = date_cls.fromisoformat(state.last_date)
            gap_days = (today - last).days
        except ValueError:
            gap_days = None
        if gap_days == 1:
            streak = state.streak + 1
        elif gap_days == 0:
            streak = state.streak or 1
        else:
            streak = 1
    else:
        streak = 1

    new_state = DailyState(
        shuffle_order=new_order,
        cursor=cursor,
        last_date=today_str,
        current_quote_index=new_index,
        streak=streak,
    )
    return quotes[new_index], new_state


def compose_daily_message(quote: dict, today: Optional[date_cls] = None) -> dict:
    """Wraps a raw {text, author, tag} quote with a warm intro + reflection,
    chosen deterministically from `today` so the same day always shows the
    same wrapper text, but different days vary."""
    today = today or date_cls.today()
    rng = random.Random(f"{today.isoformat()}::{quote['text']}")

    intro = rng.choice(INTROS)
    pool = REFLECTIONS.get(quote.get("tag", ""), DEFAULT_REFLECTIONS)
    reflection = rng.choice(pool)

    return {
        "intro": intro,
        "text": quote["text"],
        "author": quote.get("author", "Unknown"),
        "reflection": reflection,
    }
