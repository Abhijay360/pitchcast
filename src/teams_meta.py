"""Local logo paths and team display metadata."""

from __future__ import annotations

import json

from src.config import get_paths

LOGO_SLUG: dict[str, str] = {
    "Arsenal": "arsenal",
    "Aston Villa": "aston-villa",
    "Bournemouth": "bournemouth",
    "Brentford": "brentford",
    "Brighton": "brighton",
    "Chelsea": "chelsea",
    "Crystal Palace": "crystal-palace",
    "Everton": "everton",
    "Fulham": "fulham",
    "Leeds": "leeds",
    "Liverpool": "liverpool",
    "Man City": "man-city",
    "Man United": "man-united",
    "Newcastle": "newcastle",
    "Nott'm Forest": "nottm-forest",
    "Sunderland": "sunderland",
    "Tottenham": "tottenham",
    "West Ham": "west-ham",
    "Wolves": "wolves",
    "Coventry": "coventry",
    "Hull": "hull",
    "Ipswich": "ipswich",
}

# Official PL names from user palette -> canonical app names
_OFFICIAL_TO_CANONICAL: dict[str, str] = {
    "Coventry City": "Coventry",
    "Hull City": "Hull",
    "Ipswich Town": "Ipswich",
    "Leeds United": "Leeds",
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Tottenham Hotspur": "Tottenham",
}


def _load_official_colors() -> dict[str, str]:
    path = get_paths().data_dir / "team_colors.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _build_team_colors() -> dict[str, str]:
    official = _load_official_colors()
    colors: dict[str, str] = {}
    for name, hex_code in official.items():
        canonical = _OFFICIAL_TO_CANONICAL.get(name, name)
        colors[canonical] = hex_code.upper()
    return colors


TEAM_COLORS: dict[str, str] = _build_team_colors()

STADIUM_META: dict[str, dict[str, str]] = {
    "Arsenal": {"stadium": "Emirates Stadium", "city": "London", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Emirates_Stadium_-_East_side_-_Composite.jpg/640px-Emirates_Stadium_-_East_side_-_Composite.jpg"},
    "Aston Villa": {"stadium": "Villa Park", "city": "Birmingham", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Villa_Park_aerial.jpg/640px-Villa_Park_aerial.jpg"},
    "Bournemouth": {"stadium": "Vitality Stadium", "city": "Bournemouth", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Vitality_Stadium%2C_2017.jpg/640px-Vitality_Stadium%2C_2017.jpg"},
    "Brentford": {"stadium": "Gtech Community Stadium", "city": "London", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Brentford_Community_Stadium%2C_January_2022.jpg/640px-Brentford_Community_Stadium%2C_January_2022.jpg"},
    "Brighton": {"stadium": "Amex Stadium", "city": "Brighton", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Falmer_Stadium_2013.jpg/640px-Falmer_Stadium_2013.jpg"},
    "Chelsea": {"stadium": "Stamford Bridge", "city": "London", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Stamford_Bridge_2013.jpg/640px-Stamford_Bridge_2013.jpg"},
    "Crystal Palace": {"stadium": "Selhurst Park", "city": "London", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Selhurst_Park_2013.jpg/640px-Selhurst_Park_2013.jpg"},
    "Everton": {"stadium": "Hill Dickinson Stadium", "city": "Liverpool", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Goodison_Park_2013.jpg/640px-Goodison_Park_2013.jpg"},
    "Fulham": {"stadium": "Craven Cottage", "city": "London", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Craven_Cottage_Football_Ground_-_geograph.org.uk_-_632495.jpg/640px-Craven_Cottage_Football_Ground_-_geograph.org.uk_-_632495.jpg"},
    "Leeds": {"stadium": "Elland Road", "city": "Leeds", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Elland_Road_2013.jpg/640px-Elland_Road_2013.jpg"},
    "Liverpool": {"stadium": "Anfield", "city": "Liverpool", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Anfield_from_the_air_2013.jpg/640px-Anfield_from_the_air_2013.jpg"},
    "Man City": {"stadium": "Etihad Stadium", "city": "Manchester", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Etihad_Stadium%2C_Manchester%2C_England.jpg/640px-Etihad_Stadium%2C_Manchester%2C_England.jpg"},
    "Man United": {"stadium": "Old Trafford", "city": "Manchester", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Old_Trafford_2013.jpg/640px-Old_Trafford_2013.jpg"},
    "Newcastle": {"stadium": "St James' Park", "city": "Newcastle", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/St_James%27_Park%2C_Newcastle.jpg/640px-St_James%27_Park%2C_Newcastle.jpg"},
    "Nott'm Forest": {"stadium": "City Ground", "city": "Nottingham", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/City_Ground%2C_Nottingham.jpg/640px-City_Ground%2C_Nottingham.jpg"},
    "Sunderland": {"stadium": "Stadium of Light", "city": "Sunderland", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Stadium_of_Light_2013.jpg/640px-Stadium_of_Light_2013.jpg"},
    "Tottenham": {"stadium": "Tottenham Hotspur Stadium", "city": "London", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Tottenham_Hotspur_Stadium%2C_November_2019.jpg/640px-Tottenham_Hotspur_Stadium%2C_November_2019.jpg"},
    "West Ham": {"stadium": "London Stadium", "city": "London", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/London_Stadium_2013.jpg/640px-London_Stadium_2013.jpg"},
    "Wolves": {"stadium": "Molineux Stadium", "city": "Wolverhampton", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Molineux_Stadium%2C_Wolverhampton.jpg/640px-Molineux_Stadium%2C_Wolverhampton.jpg"},
    "Coventry": {"stadium": "Coventry Building Society Arena", "city": "Coventry", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Ricoh_Arena%2C_Coventry.jpg/640px-Ricoh_Arena%2C_Coventry.jpg"},
    "Hull": {"stadium": "MKM Stadium", "city": "Hull", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/KC_Stadium%2C_Hull.jpg/640px-KC_Stadium%2C_Hull.jpg"},
    "Ipswich": {"stadium": "Portman Road", "city": "Ipswich", "stadium_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Portman_Road%2C_Ipswich.jpg/640px-Portman_Road%2C_Ipswich.jpg"},
}


TEAM_META: list[str] = sorted(LOGO_SLUG.keys())


def team_logo(team: str) -> str:
    slug = LOGO_SLUG.get(team)
    if slug:
        return f"/static/logos/{slug}.png"
    return "/static/logos/default.png"


def team_stadium(team: str) -> str:
    return STADIUM_META.get(team, {}).get("stadium", "Home Ground")


def team_stadium_image(team: str) -> str:
    slug = LOGO_SLUG.get(team)
    if slug:
        return f"/static/stadiums/{slug}.jpg?v=7"
    return ""


def team_color(team: str) -> str:
    return TEAM_COLORS.get(team, "#7c3aed")


def team_info(team: str) -> dict[str, str]:
    meta = STADIUM_META.get(team, {})
    color = team_color(team)
    return {
        "name": team,
        "logo": team_logo(team),
        "slug": LOGO_SLUG.get(team, ""),
        "stadium": meta.get("stadium", "Home Ground"),
        "city": meta.get("city", ""),
        "stadium_image": team_stadium_image(team),
        "color": color,
    }
