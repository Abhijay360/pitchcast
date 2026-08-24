"""Sync match results from fixturedownload (+ local overrides) into the fixture CSV."""

from __future__ import annotations

import argparse
import json
from typing import Any

import pandas as pd

from src.config import PREDICT_SEASON, get_paths
from src.ingest.download_official_fixtures import download_official_fixtures


def _load_overrides(season: str) -> dict[str, dict[str, Any]]:
    path = get_paths().data_dir / f"result_overrides_{season}.json"
    if not path.exists():
        return {}
    raw = json.loads(path.read_text())
    return raw.get("matches", raw)


def _match_key(home: str, away: str) -> str:
    return f"{home}|{away}"


def _apply_score(
    df: pd.DataFrame,
    idx: int,
    fthg: int,
    ftag: int,
) -> bool:
    ftr = "H" if fthg > ftag else ("A" if fthg < ftag else "D")
    changed = (
        pd.isna(df.at[idx, "FTHG"])
        or int(df.at[idx, "FTHG"]) != fthg
        or int(df.at[idx, "FTAG"]) != ftag
        or str(df.at[idx, "FTR"]) != ftr
    )
    if changed:
        df.at[idx, "FTHG"] = fthg
        df.at[idx, "FTAG"] = ftag
        df.at[idx, "FTR"] = ftr
    return changed


def sync_season_results(season: str = PREDICT_SEASON) -> dict[str, Any]:
    paths = get_paths()
    fixture_path = paths.raw_dir / f"pl_{season}.csv"
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture file missing: {fixture_path}")

    fixtures = pd.read_csv(fixture_path)
    before_played = int(fixtures["FTR"].notna().sum())

    fetched = download_official_fixtures(season)
    overrides = _load_overrides(season)
    updated = 0

    fetched_lookup: dict[str, pd.Series] = {}
    for _, row in fetched.iterrows():
        if pd.notna(row.get("FTHG")) and pd.notna(row.get("FTAG")):
            fetched_lookup[_match_key(str(row["HomeTeam"]), str(row["AwayTeam"]))] = row

    for idx, row in fixtures.iterrows():
        home, away = str(row["HomeTeam"]), str(row["AwayTeam"])
        key = _match_key(home, away)

        source: dict[str, Any] | None = None
        if key in fetched_lookup:
            fr = fetched_lookup[key]
            source = {"fthg": int(fr["FTHG"]), "ftag": int(fr["FTAG"])}
        elif key in overrides:
            source = overrides[key]

        if source and _apply_score(fixtures, idx, source["fthg"], source["ftag"]):
            updated += 1

    fixtures.to_csv(fixture_path, index=False)
    after_played = int(fixtures["FTR"].notna().sum())

    return {
        "season": season,
        "fixture_path": str(fixture_path),
        "updated_rows": updated,
        "played_before": before_played,
        "played_after": after_played,
        "changed": updated > 0 or after_played > before_played,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sync PL results into fixture CSV.")
    p.add_argument("--season", default=PREDICT_SEASON)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    stats = sync_season_results(args.season)
    print(
        f"Synced {stats['season']}: {stats['played_after']} played "
        f"({stats['updated_rows']} rows updated)"
    )


if __name__ == "__main__":
    main()
