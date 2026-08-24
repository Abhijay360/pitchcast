/** Club primary colours — exact hex codes, keyed by canonical app team name. */
const TEAM_COLORS = {
  Arsenal: '#EF0107',
  'Aston Villa': '#670E36',
  Bournemouth: '#DA291C',
  Brentford: '#E30613',
  Brighton: '#0057B8',
  Chelsea: '#034694',
  Coventry: '#69B3E7',
  'Crystal Palace': '#1B458F',
  Everton: '#003399',
  Fulham: '#000000',
  Hull: '#F58220',
  Ipswich: '#003B94',
  Leeds: '#FFFFFF',
  Liverpool: '#C8102E',
  'Man City': '#6CABDD',
  'Man United': '#DA291C',
  Newcastle: '#241F20',
  "Nott'm Forest": '#DD0000',
  Sunderland: '#EB172B',
  Tottenham: '#132257',
};

function getTeamColor(team, fallback) {
  if (!team) return fallback || '#7c3aed';
  if (TEAM_COLORS[team]) return TEAM_COLORS[team];
  if (typeof TEAMS !== 'undefined' && TEAMS[team]?.color) return TEAMS[team].color;
  return fallback || '#7c3aed';
}

function hexToRgb(hex) {
  const h = (hex || '').replace('#', '');
  if (h.length !== 6) return null;
  return {
    r: parseInt(h.slice(0, 2), 16),
    g: parseInt(h.slice(2, 4), 16),
    b: parseInt(h.slice(4, 6), 16),
  };
}

function isLightColor(hex) {
  const c = hexToRgb(hex);
  if (!c) return false;
  const lum = (0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b) / 255;
  return lum > 0.72;
}

function applyTeamTheme(color, rootEl) {
  const app = rootEl || document.getElementById('team-app') || document.querySelector('.app');
  if (!app || !color) return;
  const rgb = hexToRgb(color);
  if (!rgb) return;

  const light = isLightColor(color);
  app.classList.add('team-themed');
  app.style.setProperty('--team-color', color);
  app.style.setProperty('--team-soft', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.18)`);
  app.style.setProperty('--team-border', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${light ? 0.75 : 0.55})`);
  app.style.setProperty('--team-glow', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.45)`);
  app.style.setProperty('--team-heading', color);
  app.style.setProperty('--team-stat', light ? color : 'var(--text)');
  app.style.setProperty('--team-on-badge', light ? '#0b0f1a' : color);
  const accent2 = light
    ? color
    : `rgb(${Math.min(rgb.r + 40, 255)}, ${Math.min(rgb.g + 40, 255)}, ${Math.min(rgb.b + 40, 255)})`;
  document.body.style.setProperty('--accent', color);
  document.body.style.setProperty('--accent-2', accent2);
}

function initTeamPageTheme() {
  const params = new URLSearchParams(window.location.search);
  const team = params.get('team');
  if (team) applyTeamTheme(getTeamColor(team));
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initTeamPageTheme);
} else {
  initTeamPageTheme();
}
