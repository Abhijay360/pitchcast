"""Season goal/assist leaderboards from match events + squad profiles."""

from __future__ import annotations

import json
import re
from typing import Any

import pandas as pd

from src.config import PREDICT_SEASON, get_paths
from src.ingest.fetch_squad_data import load_squad_data
from src.ingest.season_events import load_season_events
from src.player_profile import _load_tm_profiles, _norm_name


def _player_key(team: str, name: str) -> str:
    return f"{team}|{name}"


def _pl_row(season_stats: list[dict] | None, team: str) -> dict | None:
    if not season_stats:
        return None
    aliases = {
        team.lower(),
        f"{team} fc".lower(),
        team.replace("Man ", "Manchester ").lower(),
    }
    for row in season_stats:
        if row.get("competition_id") != "GB1" and "premier league" not in str(row.get("competition", "")).lower():
            continue
        club = str(row.get("club", "")).lower()
        if any(a in club or club in a for a in aliases):
            if row.get("season") == "2025-26":
                return row
    return None


def build_player_stats(season: str = PREDICT_SEASON) -> pd.DataFrame:
    """
    All squad players with 2026/27 season goals/assists (from match events)
    plus prior-season PL baseline for projection labels.
    """
    events = load_season_events(season)
    totals: dict[str, dict[str, int]] = {
        k: {"goals": int(v.get("goals", 0)), "assists": int(v.get("assists", 0))}
        for k, v in events.get("player_totals", {}).items()
    }

    squads = load_squad_data(season)
    profiles = _load_tm_profiles(season)
    rows: list[dict[str, Any]] = []

    for team, data in squads.items():
        for p in data.get("players", []):
            name = str(p.get("name", "")).strip()
            if not name:
                continue
            key = _player_key(team, name)
            actual = totals.get(key, {"goals": 0, "assists": 0})

            tm = {}
            tm_id = p.get("tm_player_id")
            if tm_id is not None and str(tm_id) in profiles:
                tm = profiles[str(tm_id)]
            else:
                for row in profiles.values():
                    if _norm_name(row.get("name", "")) == _norm_name(name):
                        tm = row
                        break

            pl_prev = _pl_row(tm.get("season_stats"), team)
            prev_goals = int(pl_prev.get("goals", 0)) if pl_prev else 0
            prev_assists = int(pl_prev.get("assists", 0)) if pl_prev else 0

            rows.append({
                "team": team,
                "player": name,
                "position": p.get("position") or tm.get("position") or "—",
                "goals": actual["goals"],
                "assists": actual["assists"],
                "prev_pl_goals": prev_goals,
                "prev_pl_assists": prev_assists,
                "has_2627_action": actual["goals"] > 0 or actual["assists"] > 0,
            })

    return pd.DataFrame(rows)


def team_leaders(season: str = PREDICT_SEASON) -> dict[str, dict[str, Any]]:
    """Per-team top scorer and top assister (2627 actuals, else 2025-26 PL proxy)."""
    df = build_player_stats(season)
    out: dict[str, dict[str, Any]] = {}

    for team, grp in df.groupby("team"):
        # Prefer players with 2627 involvement; fall back to prior PL season
        active = grp[grp["has_2627_action"]]
        pool_g = active if len(active) else grp
        pool_a = active if len(active) else grp

        top_g = pool_g.sort_values(["goals", "prev_pl_goals", "player"], ascending=[False, False, True]).iloc[0]
        top_a = pool_a.sort_values(["assists", "prev_pl_assists", "player"], ascending=[False, False, True]).iloc[0]

        g_goals = int(top_g["goals"]) if top_g["has_2627_action"] else int(top_g["prev_pl_goals"])
        a_assists = int(top_a["assists"]) if top_a["has_2627_action"] else int(top_a["prev_pl_assists"])

        out[team] = {
            "top_scorer": str(top_g["player"]),
            "top_scorer_goals": g_goals,
            "top_scorer_live": bool(top_g["has_2627_action"] and top_g["goals"] > 0),
            "top_assister": str(top_a["player"]),
            "top_assister_assists": a_assists,
            "top_assister_live": bool(top_a["has_2627_action"] and top_a["assists"] > 0),
        }
    return out


def enrich_standings_with_leaders(table: pd.DataFrame, season: str = PREDICT_SEASON) -> pd.DataFrame:
    leaders = team_leaders(season)
    table = table.copy()
    table["top_scorer"] = table["team"].map(lambda t: leaders.get(t, {}).get("top_scorer"))
    table["top_scorer_goals"] = table["team"].map(lambda t: leaders.get(t, {}).get("top_scorer_goals", 0))
    table["top_scorer_live"] = table["team"].map(lambda t: leaders.get(t, {}).get("top_scorer_live", False))
    table["top_assister"] = table["team"].map(lambda t: leaders.get(t, {}).get("top_assister"))
    table["top_assister_assists"] = table["team"].map(
        lambda t: leaders.get(t, {}).get("top_assister_assists", 0)
    )
    table["top_assister_live"] = table["team"].map(lambda t: leaders.get(t, {}).get("top_assister_live", False))
    return table


def league_leaderboard(season: str = PREDICT_SEASON, sort_by: str = "goals") -> list[dict[str, Any]]:
    """Full player list sorted by goals or assists."""
    df = build_player_stats(season)
    if df.empty:
        return []

    if sort_by == "assists":
        df = df.sort_values(["assists", "goals", "prev_pl_assists", "player"], ascending=[False, False, False, True])
    else:
        df = df.sort_values(["goals", "assists", "prev_pl_goals", "player"], ascending=[False, False, False, True])

    records = []
    for i, r in df.iterrows():
        records.append({
            "rank": len(records) + 1,
            "team": r["team"],
            "player": r["player"],
            "position": r["position"],
            "goals": int(r["goals"]),
            "assists": int(r["assists"]),
            "prev_pl_goals": int(r["prev_pl_goals"]),
            "prev_pl_assists": int(r["prev_pl_assists"]),
            "live": bool(r["has_2627_action"]),
        })
    return records
