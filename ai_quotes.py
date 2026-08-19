"""Optional AI upgrade. If the person adds an Anthropic API key in Settings,
today's message is generated fresh by Claude instead of pulled from the
offline bank. If there's no key, no internet, or anything goes wrong with
the API call, this silently returns None and the caller falls back to
`quote_engine.compose_daily_message` -- the app should never show an error
screen over a missing/failed AI call, just quietly use the offline quote.

The offline daily-selection logic (quote_engine.get_daily_quote) still runs
every day regardless of whether AI is enabled, so streaks and the
no-repeat-until-a-full-cycle guarantee keep working the same way either way
-- AI mode only replaces *what's displayed*, not the underlying state
tracking.
"""
from __future__ import annotations

import json
from typing import Optional

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """You write a short "quote of the day" message for a motivational \
quotes app. The person opening the app wants something that feels like it was \
written by someone who's actually thought about their day, not a generic \
motivational-poster line.

Write ONE original short quote (a single sentence, plain language, no \
metaphors about mountains/journeys/sunrises unless it feels genuinely fresh), \
plus a one-sentence reflection that sounds like a thoughtful friend, not a \
life coach. Avoid cliches like "unleash your potential", "in today's fast-paced \
world", "the only limit is you". Vary the tone -- not everything needs to be \
high-energy; calm, quiet encouragement is welcome too.

Return ONLY a JSON object with these exact keys, no markdown fences, no other text:
{"intro": "<a few warm words introducing the quote, under 8 words>",
 "text": "<the original quote itself, one sentence>",
 "author": "Unknown",
 "reflection": "<one warm, specific sentence, not generic>"}
"""


def generate_ai_message(api_key: str, model: str = MODEL) -> Optional[dict]:
    if not api_key:
        return None

    try:
        import anthropic
    except ImportError:
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=300,
            temperature=1.0,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": "Write today's quote and reflection."}],
        )
        raw_text = "".join(block.text for block in response.content if block.type == "text").strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            if raw_text.lower().startswith("json"):
                raw_text = raw_text[4:].strip()

        data = json.loads(raw_text)
        if not data.get("text") or not data.get("reflection"):
            return None

        return {
            "intro": data.get("intro", "Here's something for today."),
            "text": data["text"],
            "author": data.get("author") or "Unknown",
            "reflection": data["reflection"],
        }
    except Exception:
        # Any failure (bad key, no network, rate limit, malformed JSON, ...)
        # -- caller falls back to the offline engine. Never raise from here.
        return None
