#!/usr/bin/env python3
"""Regression checks for metadata-only card contract and default carried cards."""

import asyncio
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from opinion_mcp.schemas import AnalysisCards
from opinion_mcp.tools.analyze import _build_cards_meta
from opinion_mcp.tools.publish import collect_images_for_publish


class DummyResult:
    def __init__(self, cards, ai_images=None):
        self.cards = cards
        self.ai_images = ai_images or []


def test_cards_meta_exposes_new_default_card_set() -> None:
    result = DummyResult(
        AnalysisCards(
            title_card="/tmp/title.png",
            trend_analysis="/tmp/trend.png",
            debate_timeline="/tmp/debate.png",
            platform_radar="/tmp/radar.png",
        )
    )

    cards_meta = _build_cards_meta(result)

    assert cards_meta is not None
    assert cards_meta["total_ready"] == 4
    assert [item["type"] for item in cards_meta["items"]] == [
        "title_card",
        "debate_timeline",
        "trend_analysis",
        "platform_radar",
    ]
    assert all(item["ready"] for item in cards_meta["items"])


async def test_collect_images_for_publish_prefers_default_card_set() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        title = temp / "title.png"
        debate = temp / "debate.png"
        trend = temp / "trend.png"
        radar = temp / "radar.png"
        for p in [title, debate, trend, radar]:
            p.write_bytes(b"fake")

        result = DummyResult(
            AnalysisCards(
                title_card=str(title),
                trend_analysis=str(trend),
                debate_timeline=str(debate),
                platform_radar=str(radar),
            )
        )

        local_paths, failed = await collect_images_for_publish(result, "ai_and_cards")

        assert local_paths == [str(title), str(debate), str(trend), str(radar)]
        assert failed == []


if __name__ == "__main__":
    test_cards_meta_exposes_new_default_card_set()
    asyncio.run(test_collect_images_for_publish_prefers_default_card_set())
    print("ok")
