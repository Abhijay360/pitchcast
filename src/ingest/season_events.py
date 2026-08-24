"""Rebuild player goal/assist totals from season_events match list."""

from __future__ import annotations

import json
from typing import Any

from src.config import PREDICT_SEASON, get_paths


def _player_key(team: str, name: str) -> str:
    return f"{team}|{name}"


def rebuild_player_totals(events: dict[str, Any]) -> dict[str, dict[str, int]]:
    totals: dict[str, dict[str, int]] = {}
    for match in events.get("matches", []):
        for g in match.get("goals", []):
            key = _player_key(g["team"], g["player"])
            totals.setdefault(key, {"goals": 0, "assists": 0})
            totals[key]["goals"] += 1
        for a in match.get("assists", []):
            key = _player_key(a["team"], a["player"])
            totals.setdefault(key, {"goals": 0, "assists": 0})
            totals[key]["assists"] += 1
    return totals


def save_season_events(events: dict[str, Any], season: str = PREDICT_SEASON) -> None:
    events["player_totals"] = rebuild_player_totals(events)
    path = get_paths().data_dir / f"season_events_{season}.json"
    path.write_text(json.dumps(events, indent=2, ensure_ascii=False) + "\n")


def load_season_events(season: str = PREDICT_SEASON) -> dict[str, Any]:
    path = get_paths().data_dir / f"season_events_{season}.json"
    if not path.exists():
        return {"season": season, "matches": [], "player_totals": {}}
    return json.loads(path.read_text())
