import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from quote_engine import DailyState, compose_daily_message, get_daily_quote, load_quotes


def _quotes():
    return load_quotes()


def test_quotes_file_loads_and_has_required_fields():
    quotes = _quotes()
    assert len(quotes) >= 50, f"expected a healthy-sized bank, got {len(quotes)}"
    for q in quotes:
        assert q["text"].strip()
        assert q["author"].strip()
        assert q["tag"].strip()


def test_same_day_returns_same_quote():
    quotes = _quotes()
    state = DailyState()
    today = date(2026, 8, 18)

    q1, state = get_daily_quote(quotes, state, today=today)
    q2, state2 = get_daily_quote(quotes, state, today=today)

    assert q1 == q2
    assert state2.current_quote_index == state.current_quote_index


def test_consecutive_days_give_different_quotes_until_cycle_completes():
    quotes = _quotes()
    state = DailyState()
    today = date(2026, 1, 1)

    seen_indices = []
    for i in range(len(quotes)):
        q, state = get_daily_quote(quotes, state, today=today + timedelta(days=i))
        seen_indices.append(state.current_quote_index)

    # Every quote in the bank should have been shown exactly once across one
    # full cycle -- this is the "doesn't feel mechanical/repetitive" guarantee.
    assert sorted(seen_indices) == list(range(len(quotes)))


def test_no_immediate_repeat_across_a_cycle_boundary():
    quotes = _quotes()
    state = DailyState()
    today = date(2026, 1, 1)

    last_index = None
    for i in range(len(quotes) * 2 + 5):  # push past at least one full reshuffle
        q, state = get_daily_quote(quotes, state, today=today + timedelta(days=i))
        if last_index is not None:
            assert state.current_quote_index != last_index, f"day {i} repeated the previous day's quote"
        last_index = state.current_quote_index


def test_streak_increments_on_consecutive_days():
    quotes = _quotes()
    state = DailyState()
    today = date(2026, 3, 1)

    _, state = get_daily_quote(quotes, state, today=today)
    assert state.streak == 1

    _, state = get_daily_quote(quotes, state, today=today + timedelta(days=1))
    assert state.streak == 2

    _, state = get_daily_quote(quotes, state, today=today + timedelta(days=2))
    assert state.streak == 3


def test_streak_resets_after_a_gap():
    quotes = _quotes()
    state = DailyState()
    today = date(2026, 3, 1)

    _, state = get_daily_quote(quotes, state, today=today)
    _, state = get_daily_quote(quotes, state, today=today + timedelta(days=1))
    assert state.streak == 2

    # skip three days
    _, state = get_daily_quote(quotes, state, today=today + timedelta(days=5))
    assert state.streak == 1


def test_streak_unchanged_on_same_day_reopen():
    quotes = _quotes()
    state = DailyState()
    today = date(2026, 3, 1)

    _, state = get_daily_quote(quotes, state, today=today)
    _, state = get_daily_quote(quotes, state, today=today + timedelta(days=1))
    assert state.streak == 2

    _, state = get_daily_quote(quotes, state, today=today + timedelta(days=1))
    assert state.streak == 2  # reopening the same day doesn't double-increment


def test_state_roundtrips_through_dict():
    state = DailyState(shuffle_order=[3, 1, 2, 0], cursor=1, last_date="2026-01-01", current_quote_index=1, streak=4)
    restored = DailyState.from_dict(state.to_dict())
    assert restored == state


def test_compose_daily_message_is_deterministic_per_day():
    quote = {"text": "Test quote.", "author": "Test Author", "tag": "growth"}
    today = date(2026, 5, 1)

    msg1 = compose_daily_message(quote, today=today)
    msg2 = compose_daily_message(quote, today=today)
    assert msg1 == msg2


def test_compose_daily_message_varies_across_days():
    quote = {"text": "Test quote.", "author": "Test Author", "tag": "growth"}
    intros_seen = set()
    reflections_seen = set()
    for i in range(20):
        msg = compose_daily_message(quote, today=date(2026, 1, 1) + timedelta(days=i))
        intros_seen.add(msg["intro"])
        reflections_seen.add(msg["reflection"])
    # with 20 samples across a pool of 10 intros, we should see meaningful variety
    assert len(intros_seen) >= 4, f"intros barely varied: {intros_seen}"
    assert len(reflections_seen) >= 2, f"reflections barely varied: {reflections_seen}"


def test_compose_daily_message_falls_back_for_unknown_tag():
    quote = {"text": "Test quote.", "author": "Test Author", "tag": "some_unmapped_tag"}
    msg = compose_daily_message(quote, today=date(2026, 1, 1))
    assert msg["reflection"]  # should still get a reflection, not crash


def test_get_daily_quote_raises_on_empty_bank():
    try:
        get_daily_quote([], DailyState(), today=date(2026, 1, 1))
        assert False, "expected ValueError on empty quote bank"
    except ValueError:
        pass
