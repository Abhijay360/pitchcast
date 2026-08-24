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
  return rgbToHex(
    Math.round(b.r * (1 - weight) + a.r * weight),
    Math.round(b.g * (1 - weight) + a.g * weight),
    Math.round(b.b * (1 - weight) + a.b * weight),
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

  // Leeds: blue base. Fulham/black: charcoal. Everyone else: page IS the club colour.
  const primary = light ? '#1D428A' : dark ? '#111111' : color;
  const primaryRgb = hexToRgb(primary) || rgb;

  const bgTop = light ? mixHex('#1D428A', '#FFFFFF', 0.12) : primary;
  const bgMid = mixHex('#000000', primary, light ? 0.82 : dark ? 0.55 : 0.78);
  const bgDeep = mixHex('#000000', primary, light ? 0.92 : dark ? 0.35 : 0.62);
  const surface = `rgba(${primaryRgb.r}, ${primaryRgb.g}, ${primaryRgb.b}, 0.28)`;
  const surface2 = `rgba(${primaryRgb.r}, ${primaryRgb.g}, ${primaryRgb.b}, 0.38)`;
  const pageGradient = `linear-gradient(180deg, ${bgTop} 0%, ${bgMid} 32%, ${bgDeep} 100%)`;

  document.documentElement.classList.add('team-page-root');
  document.body.classList.add('team-page-body');
  app.classList.add('team-themed');

  const vars = {
    '--team-color': color,
    '--team-primary': primary,
    '--team-soft': `rgba(${primaryRgb.r}, ${primaryRgb.g}, ${primaryRgb.b}, 0.35)`,
    '--team-mid': `rgba(${primaryRgb.r}, ${primaryRgb.g}, ${primaryRgb.b}, 0.55)`,
    '--team-strong': `rgba(${primaryRgb.r}, ${primaryRgb.g}, ${primaryRgb.b}, 0.85)`,
    '--team-border': `rgba(${primaryRgb.r}, ${primaryRgb.g}, ${primaryRgb.b}, 0.65)`,
    '--team-glow': `rgba(${primaryRgb.r}, ${primaryRgb.g}, ${primaryRgb.b}, 0.7)`,
    '--team-gradient': `linear-gradient(135deg, rgba(${primaryRgb.r},${primaryRgb.g},${primaryRgb.b},0.95) 0%, rgba(${primaryRgb.r},${primaryRgb.g},${primaryRgb.b},0.55) 100%)`,
    '--team-page-bg': pageGradient,
    '--bg': bgDeep,
    '--surface': surface,
    '--surface-2': surface2,
    '--border': `rgba(${primaryRgb.r}, ${primaryRgb.g}, ${primaryRgb.b}, 0.5)`,
    '--text': '#f8fafc',
    '--muted': 'rgba(255, 255, 255, 0.68)',
    '--accent': color,
    '--accent-2': light ? '#FFCD00' : mixHex(color, '#ffffff', 0.4),
    '--team-on-color': '#ffffff',
  };

  for (const [key, val] of Object.entries(vars)) {
    document.documentElement.style.setProperty(key, val);
    document.body.style.setProperty(key, val);
    app.style.setProperty(key, val);
  }

  document.body.style.background = pageGradient;
  document.body.style.backgroundAttachment = 'fixed';
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
