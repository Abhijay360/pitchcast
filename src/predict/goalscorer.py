"""Anytime / first goalscorer probabilities from Transfermarkt data + team xG.

Purely data-driven:
- Team expected goals from Dixon–Coles λ/μ (`pred_home_xg` / `pred_away_xg`)
- Player scoring involvement from recent Premier League (or club) stats:
  shots, shots on target, goals, assists, minutes, starts, position
- Allocates team xG across the squad, then P(score ≥ 1) = 1 − exp(−λ_player)

Transfermarkt does not expose dribbles; shot volume (`scoringAttempts`) is the
best available proxy for attacking involvement.
"""

from __future__ import annotations

import math
import re
from typing import Any

from src.config import PREDICT_SEASON
from src.ingest.fetch_squad_data import load_squad_data
from src.player_profile import _load_tm_profiles, _norm_name

# Position prior for involvement when shot/goal history is thin
_POSITION_WEIGHT: dict[str, float] = {
    "centre-forward": 1.35,
    "second striker": 1.25,
    "left winger": 1.15,
    "right winger": 1.15,
    "attacking midfield": 1.1,
    "central midfield": 0.75,
    "defensive midfield": 0.45,
    "left midfield": 0.85,
    "right midfield": 0.85,
    "left-back": 0.35,
    "right-back": 0.35,
    "centre-back": 0.25,
    "sweeper": 0.2,
    "goalkeeper": 0.02,
}


def _pos_weight(position: str | None) -> float:
    if not position:
        return 0.7
    key = position.strip().lower()
    if key in _POSITION_WEIGHT:
        return _POSITION_WEIGHT[key]
    for needle, w in _POSITION_WEIGHT.items():
        if needle in key:
            return w
    if "forward" in key or "striker" in key or "winger" in key:
        return 1.2
    if "midfield" in key:
        return 0.8
    if "back" in key or "defence" in key or "defense" in key:
        return 0.3
    if "goal" in key:
        return 0.02
    return 0.7


def _season_rank(season: str) -> int:
    m = re.match(r"(\d{4})", season or "")
    return int(m.group(1)) if m else 0


def _club_aliases(team: str) -> set[str]:
    aliases = {
        team,
        team.replace("Man ", "Manchester "),
        team.replace("Nott'm ", "Nottingham "),
    }
    # TM often uses "Chelsea FC", "Arsenal FC", etc.
    aliases.add(f"{team} FC")
    aliases.add(team.replace(" United", ""))
    return {a.lower() for a in aliases if a}


def _relevant_rows(season_stats: list[dict], team: str) -> list[dict]:
    """Prefer recent Premier League rows for this club; fall back to recent club comps."""
    aliases = _club_aliases(team)
    pl = [
        r for r in season_stats
        if str(r.get("competition_id") or "") == "GB1"
        and str(r.get("club") or "").lower() in aliases
    ]
    if not pl:
        pl = [r for r in season_stats if str(r.get("competition_id") or "") == "GB1"]
    if not pl:
        pl = [
            r for r in season_stats
            if str(r.get("club") or "").lower() in aliases
        ]
    if not pl:
        pl = list(season_stats)
    # Keep last ~2 seasons of relevant rows
    ranked = sorted(pl, key=lambda r: _season_rank(str(r.get("season") or "")), reverse=True)
    cutoff = _season_rank(str(ranked[0].get("season") or "")) - 1 if ranked else 0
    return [r for r in ranked if _season_rank(str(r.get("season") or "")) >= cutoff][:6]


def _player_rates(player: dict, profile: dict, team: str) -> dict[str, float]:
    rows = _relevant_rows(profile.get("season_stats") or [], team)
    goals = shots = shots_ot = assists = minutes = apps = starts = 0
    for r in rows:
        goals += int(r.get("goals") or 0)
        shots += int(r.get("shots") or 0)
        shots_ot += int(r.get("shots_on_target") or 0)
        assists += int(r.get("assists") or 0)
        minutes += int(r.get("minutes") or 0)
        apps += int(r.get("apps") or 0)
        starts += int(r.get("starts") or 0)

    # Fallback to career totals if no recent rows
    if minutes <= 0:
        tot = profile.get("career_totals") or {}
        goals = int(tot.get("goals") or 0)
        shots = int(tot.get("shots") or 0)
        shots_ot = int(tot.get("shots_on_target") or 0)
        assists = int(tot.get("assists") or 0)
        minutes = int(tot.get("minutes") or 0)
        apps = int(tot.get("apps") or 0)
        starts = int(tot.get("starts") or 0)

    minutes = max(minutes, 1)
    # Dampen tiny samples so a 2-game hot streak doesn't dominate
    sample_factor = min(1.0, minutes / 900.0)  # full weight from ~10 full matches
    per90 = 90.0 / minutes
    return {
        "goals": float(goals),
        "shots": float(shots),
        "shots_on_target": float(shots_ot),
        "assists": float(assists),
        "minutes": float(minutes),
        "apps": float(apps),
        "starts": float(starts),
        "goals_per90": goals * per90 * sample_factor,
        "shots_per90": shots * per90 * sample_factor,
        "sot_per90": shots_ot * per90 * sample_factor,
        "start_rate": (starts / apps) if apps else 0.55,
        "position_weight": _pos_weight(player.get("position") or profile.get("position")),
        "sample_factor": sample_factor,
    }


def _involvement_score(rates: dict[str, float], market_value_m: float, league_max_mv: float) -> float:
    """Relative attacking involvement used to share team xG."""
    # Prefer shots when present; blend goals + SoT + assists + value + position
    shot_component = rates["shots_per90"] * 1.0 + rates["sot_per90"] * 1.4
    goal_component = rates["goals_per90"] * 3.0 + rates["assists"] / max(rates["minutes"] / 90.0, 1.0) * 0.6
    if rates["shots"] <= 0 and rates["goals"] <= 0:
        # Thin history: position + market value only
        value_norm = math.sqrt(max(market_value_m, 0) / max(league_max_mv, 1.0))
        return max(0.02, rates["position_weight"] * (0.35 + 0.65 * value_norm) * max(rates["start_rate"], 0.25))

    raw = 0.55 * shot_component + 0.45 * goal_component
    if rates["shots"] <= 0:
        raw = goal_component
    raw *= rates["position_weight"]
    raw *= 0.55 + 0.45 * max(rates["start_rate"], 0.2)
    # Mild market-value tie-break for similar rates
    value_norm = math.sqrt(max(market_value_m, 0) / max(league_max_mv, 1.0))
    raw *= 0.85 + 0.15 * value_norm
    return max(raw, 0.01)


def _allocate_team(
    team: str,
    team_xg: float,
    *,
    profiles: dict[str, dict],
    top_n: int = 8,
) -> list[dict[str, Any]]:
    squad = load_squad_data(PREDICT_SEASON).get(team, {})
    players = squad.get("players") or []
    if not players or team_xg <= 0:
        return []

    league_max_mv = max((float(p.get("market_value_m") or 0) for p in players), default=1.0) or 1.0
    scored: list[dict[str, Any]] = []

    for p in players:
        name = p.get("name") or ""
        if not name:
            continue
        tm_id = p.get("tm_player_id")
        profile = {}
        if tm_id is not None and str(tm_id) in profiles:
            profile = profiles[str(tm_id)]
        else:
            target = _norm_name(name)
            for row in profiles.values():
                if _norm_name(row.get("name", "")) == target:
                    profile = row
                    break

        rates = _player_rates(p, profile, team)
        # Keepers almost never score from open play
        if rates["position_weight"] <= 0.05 and rates["goals"] <= 0:
            continue

        inv = _involvement_score(rates, float(p.get("market_value_m") or 0), league_max_mv)
        scored.append({
            "name": name,
            "team": team,
            "position": p.get("position") or profile.get("position") or "—",
            "photo_url": profile.get("photo_url") or (
                f"https://tmssl.akamaized.net/images/portrait/header/{tm_id}.png" if tm_id else None
            ),
            "tm_player_id": tm_id,
            "market_value_m": p.get("market_value_m"),
            "involvement": inv,
            "goals": int(rates["goals"]),
            "assists": int(rates["assists"]),
            "shots": int(rates["shots"]),
            "shots_on_target": int(rates["shots_on_target"]),
            "minutes": int(rates["minutes"]),
            "goals_per90": round(rates["goals_per90"], 3),
            "shots_per90": round(rates["shots_per90"], 3),
            "start_rate": round(rates["start_rate"], 3),
        })

    if not scored:
        return []

    total_inv = sum(r["involvement"] for r in scored) or 1.0
    # Concentrate xG on the most involved ~14 outfielders (typical matchday squad)
    scored.sort(key=lambda r: r["involvement"], reverse=True)
    active = scored[:16]
    total_inv = sum(r["involvement"] for r in active) or 1.0

    out: list[dict[str, Any]] = []
    for r in active:
        share = r["involvement"] / total_inv
        lam = team_xg * share
        p_anytime = 1.0 - math.exp(-lam)
        # First goalscorer approx among team scorers, later renormalized across both teams
        out.append({
            **{k: v for k, v in r.items() if k != "involvement"},
            "xg_share": round(share, 4),
            "player_xg": round(lam, 3),
            "p_anytime": round(p_anytime, 4),
            "_lam": lam,
        })

    out.sort(key=lambda r: r["p_anytime"], reverse=True)
    return out[:top_n]


def fixture_goalscorers(
    home: str,
    away: str,
    home_xg: float,
    away_xg: float,
    *,
    top_n: int = 6,
) -> dict[str, Any]:
    """Build anytime (+ approximate first) goalscorer tables for a fixture."""
    profiles = _load_tm_profiles(PREDICT_SEASON)
    home_rows = _allocate_team(home, float(home_xg or 0), profiles=profiles, top_n=top_n)
    away_rows = _allocate_team(away, float(away_xg or 0), profiles=profiles, top_n=top_n)

    # First goalscorer: among all listed players, weight by λ / sum(λ) * P(match has ≥1 goal)
    all_rows = home_rows + away_rows
    sum_lam = sum(r["_lam"] for r in all_rows) or 1.0
    p_any_goal = 1.0 - math.exp(-(float(home_xg or 0) + float(away_xg or 0)))
    for r in all_rows:
        r["p_first"] = round((r["_lam"] / sum_lam) * p_any_goal, 4)
        del r["_lam"]

    home_rows = sorted(home_rows, key=lambda r: r["p_anytime"], reverse=True)
    away_rows = sorted(away_rows, key=lambda r: r["p_anytime"], reverse=True)
    combined = sorted(all_rows, key=lambda r: r["p_anytime"], reverse=True)

    has_shots = any((r.get("shots") or 0) > 0 for r in combined)
    return {
        "home": home,
        "away": away,
        "home_xg": round(float(home_xg or 0), 3),
        "away_xg": round(float(away_xg or 0), 3),
        "home_scorers": home_rows,
        "away_scorers": away_rows,
        "top_anytime": combined[:10],
        "method": {
            "summary": (
                "Team xG from Dixon–Coles rates is shared across the squad using "
                "Transfermarkt shot volume, goals, minutes, start rate, position, "
                "and market value. Anytime = 1 − exp(−player_xG)."
            ),
            "uses_shots": has_shots,
            "notes": (
                None if has_shots
                else "Shot totals still refreshing for some players — using goals/minutes/position until then."
            ),
        },
    }
