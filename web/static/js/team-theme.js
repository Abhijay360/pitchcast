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

function rgbToHex(r, g, b) {
  return `#${[r, g, b].map((v) => Math.max(0, Math.min(255, v)).toString(16).padStart(2, '0')).join('')}`;
}

function mixHex(base, accent, weight) {
  const b = hexToRgb(base);
  const a = hexToRgb(accent);
  if (!b || !a) return base;
  const w = weight;
  return rgbToHex(
    Math.round(b.r * (1 - w) + a.r * w),
    Math.round(b.g * (1 - w) + a.g * w),
    Math.round(b.b * (1 - w) + a.b * w),
  );
}

function luminance(rgb) {
  return (0.2126 * rgb.r + 0.7152 * rgb.g + 0.0722 * rgb.b) / 255;
}

function isLightColor(hex) {
  const c = hexToRgb(hex);
  return c ? luminance(c) > 0.72 : false;
}

function isDarkColor(hex) {
  const c = hexToRgb(hex);
  return c ? luminance(c) < 0.12 : false;
}

function applyTeamTheme(color, rootEl) {
  const app = rootEl || document.getElementById('team-app') || document.querySelector('.app');
  if (!app || !color) return;
  const rgb = hexToRgb(color);
  if (!rgb) return;

  const light = isLightColor(color);
  const dark = isDarkColor(color);
  document.body.classList.add('team-page-body');
  app.classList.add('team-themed');

  const bgTint = light
    ? mixHex('#0a0e17', '#1D428A', 0.28)
    : dark
      ? mixHex('#0a0e17', '#ffffff', 0.05)
      : mixHex('#0a0e17', color, 0.32);
  const surface = light
    ? mixHex('#12182a', '#1D428A', 0.22)
    : mixHex('#12182a', color, 0.24);
  const surface2 = light
    ? mixHex('#1a2238', '#1D428A', 0.18)
    : mixHex('#1a2238', color, 0.2);

  app.style.setProperty('--team-color', color);
  app.style.setProperty('--team-soft', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${light ? 0.14 : 0.22})`);
  app.style.setProperty('--team-mid', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${light ? 0.35 : 0.45})`);
  app.style.setProperty('--team-strong', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${light ? 0.55 : 0.65})`);
  app.style.setProperty('--team-border', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${light ? 0.7 : 0.5})`);
  app.style.setProperty('--team-glow', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.55)`);
  app.style.setProperty('--team-gradient', `linear-gradient(135deg, rgba(${rgb.r},${rgb.g},${rgb.b},0.72) 0%, rgba(${rgb.r},${rgb.g},${rgb.b},0.28) 42%, rgba(${rgb.r},${rgb.g},${rgb.b},0.08) 100%)`);
  app.style.setProperty('--team-gradient-soft', `linear-gradient(180deg, rgba(${rgb.r},${rgb.g},${rgb.b},0.35) 0%, transparent 70%)`);
  app.style.setProperty('--team-heading', color);
  app.style.setProperty('--team-on-color', light || dark ? '#f8fafc' : '#ffffff');
  app.style.setProperty('--team-on-badge', light ? '#0b0f1a' : color);
  app.style.setProperty('--bg', bgTint);
  app.style.setProperty('--surface', surface);
  app.style.setProperty('--surface-2', surface2);
  app.style.setProperty('--border', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.35)`);

  const bodyVars = ['--team-color', '--team-soft', '--team-mid', '--team-strong', '--team-border', '--team-glow', '--team-gradient', '--bg', '--surface', '--surface-2', '--border'];
  document.body.classList.add('team-page-body');
  for (const key of bodyVars) {
    const val = app.style.getPropertyValue(key);
    if (val) document.body.style.setProperty(key, val);
  }
  document.body.style.setProperty('--accent', color);
  document.body.style.setProperty('--accent-2', light ? color : mixHex(color, '#ffffff', 0.35));
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
