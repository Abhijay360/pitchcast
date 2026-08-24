"""Run after each matchday: sync results, rebuild features, retrain, re-simulate."""

from __future__ import annotations

import argparse
import subprocess
import sys

from src.config import PREDICT_SEASON, TRAIN_SEASONS, get_paths
from src.ingest.season_events import load_season_events, rebuild_player_totals, save_season_events
from src.ingest.sync_season_results import sync_season_results


def _run(cmd: list[str]) -> None:
    print(f"\n>>> {' '.join(cmd)}\n")
    subprocess.run(cmd, check=True)


def refresh_season(
    season: str = PREDICT_SEASON,
    *,
    sync_results: bool = True,
    rebuild_events: bool = True,
    fetch_injuries: bool = True,
    simulations: int = 5_000,
) -> dict:
    py = sys.executable
    stats: dict = {"season": season}

    if sync_results:
        stats["sync"] = sync_season_results(season)

    if rebuild_events:
        events = load_season_events(season)
        save_season_events(events, season)
        stats["event_players"] = len(events.get("player_totals", {}))

    all_seasons = [*TRAIN_SEASONS, season]
    _run([py, "-m", "src.features.build_features", "--seasons", *all_seasons])
    _run([
        py, "-m", "src.train.train_model",
        "--predict-season", season,
        "--last-n-seasons", "10",
    ])

    if fetch_injuries:
        try:
            _run([py, "-m", "src.ingest.fetch_injuries", "--season", season])
        except subprocess.CalledProcessError as exc:
            print(f"Injury fetch skipped: {exc}")

    _run([
        py, "-m", "src.predict.simulate_season",
        "--season", season,
        "--simulations", str(simulations),
    ])

    stats["done"] = True
    return stats


def maybe_refresh(season: str = PREDICT_SEASON) -> dict | None:
    """Sync results; run full refresh only when new scores landed."""
    sync_stats = sync_season_results(season)
    if not sync_stats.get("changed"):
        print("No new results — skipping pipeline refresh.")
        return None
    return refresh_season(season, sync_results=False)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Refresh predictions after new match results.")
    p.add_argument("--season", default=PREDICT_SEASON)
    p.add_argument("--check-only", action="store_true", help="Sync results only; refresh if changed.")
    p.add_argument("--simulations", type=int, default=5_000)
    p.add_argument("--no-injuries", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.check_only:
        stats = maybe_refresh(args.season)
        if stats:
            print(f"Refreshed after new results: {stats}")
        return

    stats = refresh_season(
        args.season,
        simulations=args.simulations,
        fetch_injuries=not args.no_injuries,
    )
    print(f"\nMatchday refresh complete: {stats}")


if __name__ == "__main__":
    main()
