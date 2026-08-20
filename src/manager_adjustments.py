"""Manager strength adjustments for the predict season.

Applied at prediction time only (not in historical training).
`MANAGER_BOOST` is on roughly a 0.00…0.25 scale (0.10 ≈ +12 Elo).
Skill used by the simulator: clip(0.55 + boost * 1.8, 0.40, 0.96).

Scoring priorities for 2026/27:
1. Proven Premier League tenure / continuity (Arteta, Emery, Hurzeler, …)
2. Major trophies and sustained top-half delivery in England
3. Elite CVs on a *new* club get less weight than established PL projects
4. Brand-new appointments / unproven PL spells stay toward the bottom
"""

from __future__ import annotations

# team -> (manager_name, boost, short rationale)
_MANAGER_TABLE: list[tuple[str, str, float, str]] = [
    # Continuity + silverware first
    ("Arsenal", "Mikel Arteta", 0.24,
     "Longest-serving PL boss; 2025/26 PL title + Manager of the Season; multi-year build"),
    ("Aston Villa", "Unai Emery", 0.17,
     "In post since 2022; CL qualification habit + 5th Europa League (2025/26)"),
    ("Nott'm Forest", "Oliver Glasner", 0.13,
     "New at Forest but elite recent PL record (FA Cup + Conference at Palace)"),
    ("Brighton", "Fabian Hurzeler", 0.12,
     "In post since 2024; back-to-back 8th + European qualification; continuity credit"),
    ("Everton", "David Moyes", 0.12,
     "Second spell since Jan 2025; deep PL experience; stabilised Everton"),
    ("Sunderland", "Regis Le Bris", 0.11,
     "In post since 2024; promotion then shock 7th + Europe — rare continuity success"),
    ("Leeds", "Daniel Farke", 0.11,
     "In post since 2023; Championship title + survival project continuity"),
    ("Brentford", "Keith Andrews", 0.10,
     "Internal promotee since 2025; equalled club-best 9th — process continuity"),
    ("Tottenham", "Roberto De Zerbi", 0.09,
     "In since Mar 2026; strong Brighton/Marseille CV but short Spurs tenure"),

    # Big-six new/recent — strong CVs, *less* credit than Arteta's stay
    ("Chelsea", "Xabi Alonso", 0.08,
     "Leverkusen invincible season; new at Chelsea (Jul 2026) — CV ≠ PL continuity"),
    ("Man City", "Enzo Maresca", 0.07,
     "Conference/CWC + Chelsea CL path; brand-new Pep successor — transition risk"),
    ("Liverpool", "Andoni Iraola", 0.06,
     "Excellent Bournemouth overperformance; brand-new at Liverpool (Jun 2026)"),
    ("Man United", "Michael Carrick", 0.05,
     "Permanent since Jan 2026 after 3rd-place finish; thinner trophy CV as head coach"),

    # New / mixed PL records
    ("Bournemouth", "Marco Rose", 0.04,
     "Solid Bundesliga CV; new at Bournemouth replacing Iraola"),
    ("Newcastle", "Matthias Jaissle", 0.04,
     "Salzburg/Al-Ahli titles; brand-new Howe successor (Aug 2026)"),
    ("Crystal Palace", "Pierre Sage", 0.03,
     "Lens Coupe de France + CL path; new at Palace after Glasner"),
    ("Ipswich", "Gary O'Neil", 0.02,
     "Mixed PL spells (Bournemouth/Wolves); new at Ipswich"),
    ("Fulham", "Alvaro Arbeloa", 0.02,
     "Madrid B / interim only; brand-new PL head coach"),
    ("Coventry", "Frank Lampard", 0.02,
     "Promotion hero; previous PL managerial record mixed"),
    ("Hull", "Sergej Jakirovic", 0.01,
     "Promotion via playoffs; limited top-five-league managerial proof"),
]

MANAGER_NAME: dict[str, str] = {t: n for t, n, _, _ in _MANAGER_TABLE}
MANAGER_BOOST: dict[str, float] = {t: b for t, _, b, _ in _MANAGER_TABLE}
MANAGER_NOTES: dict[str, str] = {t: note for t, _, _, note in _MANAGER_TABLE}


def manager_boost(team: str) -> float:
    return MANAGER_BOOST.get(team, 0.0)


def manager_note(team: str) -> str | None:
    return MANAGER_NOTES.get(team)


def manager_name(team: str) -> str | None:
    return MANAGER_NAME.get(team)


def manager_skill(team: str) -> float:
    """Same transform the simulator uses."""
    return max(0.40, min(0.96, 0.55 + manager_boost(team) * 1.8))


def manager_ranking() -> list[dict]:
    """All 20 managers ranked by boost (then skill)."""
    rows = []
    for team, boost in MANAGER_BOOST.items():
        rows.append({
            "rank": 0,
            "team": team,
            "manager": MANAGER_NAME.get(team, "—"),
            "boost": boost,
            "skill": round(manager_skill(team), 3),
            "note": MANAGER_NOTES.get(team, ""),
        })
    rows.sort(key=lambda r: (-r["boost"], r["team"]))
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    return rows
