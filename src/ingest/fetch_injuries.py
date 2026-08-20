"""Fetch current Premier League availability / injuries from the FPL API."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import requests

from src.config import PREDICT_SEASON, get_paths
from src.ingest.fetch_squad_data import load_squad_data

FPL_BOOTSTRAP = "https://fantasy.premierleague.com/api/bootstrap-static/"

# FPL team display name -> football-data / PitchCast canonical
FPL_TO_CANONICAL: dict[str, str] = {
    "Arsenal": "Arsenal",
    "Aston Villa": "Aston Villa",
    "Bournemouth": "Bournemouth",
    "Brentford": "Brentford",
    "Brighton": "Brighton",
    "Chelsea": "Chelsea",
    "Coventry City": "Coventry",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Hull City": "Hull",
    "Ipswich Town": "Ipswich",
    "Leeds": "Leeds",
    "Liverpool": "Liverpool",
    "Man City": "Man City",
    "Man Utd": "Man United",
    "Newcastle": "Newcastle",
    "Nott'm Forest": "Nott'm Forest",
    "Spurs": "Tottenham",
    "Sunderland": "Sunderland",
}


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def health_from_fpl(status: str, chance: int | None) -> float:
    """
    Map FPL availability to simulator health in [0, 1].

    a=available, d=doubtful, i=injured, s=suspended, u=unavailable, n=not available
    """
    status = (status or "a").lower()
    if status == "a":
        return 1.0
    if chance is not None:
        return float(max(0.0, min(1.0, chance / 100.0)))
    if status == "d":
        return 0.75
    if status in {"i", "s", "u", "n"}:
        return 0.0
    return 1.0


def match_squad_player(team_players: list[dict], element: dict) -> dict | None:
    """Best-effort match of an FPL element to a Transfermarkt squad row."""
    web = _norm(element.get("web_name", ""))
    full = _norm(f"{element.get('first_name', '')} {element.get('second_name', '')}")
    last = _norm(element.get("second_name", ""))

    for p in team_players:
        pn = _norm(p.get("name", ""))
        if not pn:
            continue
        if web and (web == pn or web in pn.split() or pn.endswith(web) or web in pn):
            return p
        if full and (full == pn or full in pn or pn in full):
            return p

    if last and len(last) > 3:
        hits = [p for p in team_players if last in _norm(p.get("name", "")).split()]
        if len(hits) == 1:
            return hits[0]
    return None


def fetch_fpl_bootstrap() -> dict:
    r = requests.get(FPL_BOOTSTRAP, timeout=45)
    r.raise_for_status()
    return r.json()


def build_injury_dataset(season: str = PREDICT_SEASON) -> dict:
    bootstrap = fetch_fpl_bootstrap()
    squad = load_squad_data(season)
    team_by_id = {t["id"]: t["name"] for t in bootstrap.get("teams", [])}

    injuries: list[dict] = []
    matched = 0
    unmatched = 0

    for el in bootstrap.get("elements", []):
        status = (el.get("status") or "a").lower()
        if status == "a":
            continue

        fpl_team = team_by_id.get(el["team"], "")
        team = FPL_TO_CANONICAL.get(fpl_team, fpl_team)
        chance = el.get("chance_of_playing_next_round")
        health = health_from_fpl(status, chance if isinstance(chance, int) else None)

        squad_players = (squad.get(team) or {}).get("players", [])
        hit = match_squad_player(squad_players, el) if squad_players else None
        if hit:
            matched += 1
            player_name = hit["name"]
            tm_player_id = hit.get("tm_player_id")
        else:
            unmatched += 1
            player_name = (
                f"{el.get('first_name', '')} {el.get('second_name', '')}".strip()
                or el.get("web_name", "")
            )
            tm_player_id = None

        injuries.append({
            "team": team,
            "player": player_name,
            "fpl_web_name": el.get("web_name"),
            "fpl_id": el.get("id"),
            "tm_player_id": tm_player_id,
            "matched": bool(hit),
            "status": status,
            "chance_of_playing": chance,
            "health": round(health, 3),
            "news": (el.get("news") or "").strip(),
            "market_value_m": float(hit.get("market_value_m", 0) or 0) if hit else 0.0,
        })

    injuries.sort(key=lambda x: (x["team"], -x["market_value_m"], x["player"]))
    return {
        "season": season,
        "source": "fantasy.premierleague.com/api/bootstrap-static",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "injury_count": len(injuries),
        "matched_count": matched,
        "unmatched_count": unmatched,
        "injuries": injuries,
    }


def save_injury_data(season: str = PREDICT_SEASON) -> Path:
    data = build_injury_dataset(season)
    paths = get_paths()
    out = paths.data_dir / "injuries" / f"injuries_{season}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2))
    return out


def load_injury_data(season: str = PREDICT_SEASON) -> dict[str, list[dict]]:
    """Return {team: [injury rows]} for matched squad players only."""
    paths = get_paths()
    path = paths.data_dir / "injuries" / f"injuries_{season}.json"
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    by_team: dict[str, list[dict]] = {}
    for row in raw.get("injuries", []):
        if not row.get("matched"):
            continue
        by_team.setdefault(row["team"], []).append(row)
    return by_team


def load_player_health_map(season: str = PREDICT_SEASON) -> dict[str, float]:
    """Map `team|player` ids -> health for the simulator."""
    by_team = load_injury_data(season)
    out: dict[str, float] = {}
    for team, rows in by_team.items():
        for row in rows:
            out[f"{team}|{row['player']}"] = float(row.get("health", 0.0))
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch PL injuries from the FPL API.")
    p.add_argument("--season", default=PREDICT_SEASON)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    path = save_injury_data(args.season)
    data = json.loads(path.read_text())
    print(
        f"Wrote injuries: {path} "
        f"({data['injury_count']} flagged, {data['matched_count']} matched to squad)"
    )
    by_team: dict[str, int] = {}
    for row in data["injuries"]:
        if row.get("matched") and row.get("health", 1) < 0.8:
            by_team[row["team"]] = by_team.get(row["team"], 0) + 1
    for team, n in sorted(by_team.items(), key=lambda x: -x[1])[:8]:
        print(f"  {team}: {n} unavailable / doubtful")


if __name__ == "__main__":
    main()
