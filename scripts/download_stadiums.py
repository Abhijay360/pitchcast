"""Download per-team stadium photos (club / Premier League partner CDNs + Wikimedia fallbacks)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.teams_meta import LOGO_SLUG

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "image/*,*/*",
}

MIN_BYTES = 15_000


def _load_sources(data_dir: Path) -> dict[str, dict[str, str]]:
    path = data_dir / "stadium_image_sources.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing stadium source map: {path}")
    raw = json.loads(path.read_text())
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def download_stadium_photos(
    out_dir: Path,
    *,
    sources: dict[str, dict[str, str]] | None = None,
    force: bool = False,
) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    if sources is None:
        sources = _load_sources(Path(__file__).resolve().parents[1] / "data")

    ok = 0
    for team, slug in LOGO_SLUG.items():
        dest = out_dir / f"{slug}.jpg"
        if not force and dest.exists() and dest.stat().st_size > MIN_BYTES:
            ok += 1
            continue

        entry = sources.get(team)
        if not entry or not entry.get("url"):
            print(f"  ✗ {team} (no source URL)")
            continue

        url = entry["url"]
        source = entry.get("source", "unknown")
        try:
            r = requests.get(url, headers=HEADERS, timeout=60)
            if r.status_code == 200 and len(r.content) >= MIN_BYTES:
                dest.write_bytes(r.content)
                ok += 1
                print(f"  ✓ {team} ({source}, {len(r.content) // 1024} KB)")
            else:
                print(f"  ✗ {team} HTTP {r.status_code} / {len(r.content)} bytes ({source})")
        except Exception as exc:
            print(f"  ✗ {team}: {exc}")
        time.sleep(1.2)

    return ok


def main() -> None:
    p = argparse.ArgumentParser(description="Download stadium photos to web/static/stadiums/")
    p.add_argument("--out", default="web/static/stadiums")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    print("Downloading per-team stadium photos…")
    n = download_stadium_photos(root / args.out, force=args.force)
    print(f"Done: {n}/{len(LOGO_SLUG)} stadium photos ready.")


if __name__ == "__main__":
    main()
