async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
  return res.json();
}

function logoImg(src, cls = 'team-logo-lg') {
  const url = src || '/static/logos/default.png';
  return `<img class="${cls}" src="${url}" alt="" onerror="this.onerror=null;this.src='/static/logos/default.png'" />`;
}

function teamUrl(team) {
  return `/team?team=${encodeURIComponent(team)}`;
}

function playerUrl(team, name) {
  return `/player?team=${encodeURIComponent(team)}&name=${encodeURIComponent(name)}`;
}

function matchUrl(m) {
  return `/match?home=${encodeURIComponent(m.HomeTeam)}&away=${encodeURIComponent(m.AwayTeam)}&date=${encodeURIComponent(m.Date || '')}`;
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

function applyTeamTheme(color) {
  const app = document.getElementById('team-app');
  if (!app || !color) return;
  const rgb = hexToRgb(color);
  if (!rgb) return;

  const light = isLightColor(color);
  app.classList.add('team-themed');
  app.style.setProperty('--team-color', color);
  app.style.setProperty('--team-soft', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.14)`);
  app.style.setProperty('--team-border', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${light ? 0.65 : 0.45})`);
  app.style.setProperty('--team-glow', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.35)`);
  app.style.setProperty('--team-heading', light ? color : color);
  app.style.setProperty('--team-stat', light ? color : 'var(--text)');
  app.style.setProperty('--team-on-badge', light ? '#0b0f1a' : color);
  const accent2 = light
    ? color
    : `rgb(${Math.min(rgb.r + 40, 255)}, ${Math.min(rgb.g + 40, 255)}, ${Math.min(rgb.b + 40, 255)})`;
  document.body.style.setProperty('--accent', color);
  document.body.style.setProperty('--accent-2', accent2);
}

function renderTrophies(trophies, recent) {
  const recentBlock = recent
    ? `<div class="highlight-card trophy-highlight">
        <div class="highlight-label">Most recent major honour</div>
        <div class="highlight-value">${recent.label || recent.competition}</div>
        <div class="muted small">${recent.season || recent.most_recent || ''}</div>
      </div>`
    : '';
  const list = trophies?.length
    ? `<div class="trophy-grid">${trophies.map((t) => `
        <div class="trophy-card">
          <div class="trophy-name">${t.competition}</div>
          <div class="trophy-count">${t.count}×</div>
          <div class="trophy-recent muted">Last: ${t.most_recent}</div>
        </div>`).join('')}</div>`
    : '<p class="muted">No trophy data available.</p>';
  return recentBlock + list;
}

function renderHistory(rows) {
  const pl = rows.filter((r) => r.in_pl);
  if (!pl.length) return '<p class="muted">No Premier League history in training data.</p>';
  let html = '<div class="table-wrap"><table class="standings-table"><thead><tr><th>Season</th><th>P</th><th>W</th><th>D</th><th>L</th><th>GF</th><th>GA</th><th>GD</th><th>Pts</th></tr></thead><tbody>';
  for (const r of pl.slice().reverse()) {
    html += `<tr><td>${r.label}</td><td>${r.played}</td><td>${r.won}</td><td>${r.drawn}</td><td>${r.lost}</td><td>${r.gf}</td><td>${r.ga}</td><td>${r.gd > 0 ? '+' : ''}${r.gd}</td><td><strong>${r.points}</strong></td></tr>`;
  }
  html += '</tbody></table></div>';
  return html;
}

function pct1(n) {
  return Number.isFinite(n) ? `${(n * 100).toFixed(0)}%` : '—';
}

function renderFixtures(fixtures, team) {
  const up = fixtures.upcoming || [];
  const played = fixtures.played || [];
  const all = [...played, ...up].sort((a, b) => String(a.Date || '').localeCompare(String(b.Date || '')));

  const card = (m) => {
    const isHome = m.HomeTeam === team;
    const opp = isHome ? m.AwayTeam : m.HomeTeam;
    const venue = isHome ? 'H' : 'A';
    const playedMatch = isPlayedMatch(m);
    const scoreHtml = playedMatch
      ? `<div class="fixture-mini-scores"><span class="score-pred">Pred ${predScoreText(m)}</span><span class="score-actual">Actual ${actualScoreText(m)}</span></div>`
      : `<div class="fixture-mini-score">${predScoreText(m)}</div>`;
    const date = m.Date
      ? new Date(m.Date).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })
      : '—';
    const probs = !playedMatch && m.p_home != null
      ? `<div class="fixture-mini-probs muted">H ${pct1(m.p_home)} · D ${pct1(m.p_draw)} · A ${pct1(m.p_away)}</div>`
      : '';
    const badge = playedMatch ? 'Played' : 'Predicted';
    return `<a class="fixture-mini" href="${matchUrl(m)}">
      <div class="fixture-mini-top">
        <span class="muted">${date}</span>
        <span class="pill small">${venue} · ${badge}</span>
      </div>
      <div class="fixture-mini-main">${isHome ? `<strong>${team}</strong> vs ${opp}` : `${opp} vs <strong>${team}</strong>`}</div>
      ${scoreHtml}
      ${probs}
    </a>`;
  };

  if (!all.length) {
    return '<p class="muted">No fixtures found for this team.</p>';
  }

  return `
    <p class="muted small" style="margin-bottom:0.75rem">
      All ${all.length} matches this season — predicted scorelines and win/draw/away odds. Click any row for full match insights.
    </p>
    <div class="fixture-mini-list fixture-season-list">${all.map(card).join('')}</div>`;
}

function renderSquad(squad, team) {
  const players = squad?.players || [];
  if (!players.length) return '<p class="muted">Squad data unavailable.</p>';
  const sorted = [...players].sort((a, b) => (b.market_value_m || 0) - (a.market_value_m || 0));
  let html = '<div class="squad-list">';
  for (const p of sorted) {
    const face = p.tm_player_id
      ? `<img class="player-face-sm" src="https://tmssl.akamaized.net/images/portrait/header/${p.tm_player_id}.png" alt="" loading="lazy" onerror="this.style.display='none'" />`
      : '';
    html += `<a class="squad-row" href="${playerUrl(team, p.name)}">
      <div class="squad-row-name">${face}<span>${p.name}</span></div>
      <div class="squad-row-meta muted">${p.position || '—'}</div>
      <div class="squad-row-val">${p.market_value_m ? `€${p.market_value_m.toFixed(1)}m` : '—'}</div>
    </a>`;
  }
  html += '</div>';
  return html;
}

async function load() {
  const params = new URLSearchParams(window.location.search);
  const team = params.get('team');
  if (!team) {
    document.getElementById('team-content').innerHTML = '<p class="empty-state">Missing team parameter.</p>';
    return;
  }

  const [profile, squad] = await Promise.all([
    fetchJSON(`/api/teams/${encodeURIComponent(team)}/profile`),
    fetchJSON(`/api/teams/${encodeURIComponent(team)}/squad`).catch(() => ({ players: [] })),
  ]);

  document.title = `${team} · PitchCast`;
  const info = profile.info || {};
  const stadiumImg = info.stadium_image || '';
  const clubColor = info.color || '#7c3aed';
  applyTeamTheme(clubColor);

  document.getElementById('team-hero').innerHTML = `
    <div class="profile-hero-row">
      <a href="${teamUrl(team)}" class="profile-logo-link">${logoImg(info.logo)}</a>
      <div>
        <h1>${team}</h1>
        <div class="team-color-bar" style="background:${clubColor}" aria-hidden="true"></div>
        <p class="hero-sub">${info.stadium || ''}${info.city ? ` · ${info.city}` : ''}${profile.nickname ? ` · ${profile.nickname}` : ''}${profile.founded ? ` · Est. ${profile.founded}` : ''}</p>
        ${profile.most_recent_major ? `<div class="hero-badge">${profile.most_recent_major.label}</div>` : ''}
      </div>
    </div>
    ${stadiumImg ? `<div class="profile-stadium"><img src="${stadiumImg}" alt="" onerror="this.onerror=null;this.src='${stadiumImg.replace('.jpg','.svg')}'" /></div>` : ''}`;

  const cs = profile.current_season || {};
  const stats = `
    <div class="stats-row">
      <div class="stat-card highlight-stat"><div class="stat-label">${profile.predict_season_label} table</div><div class="stat-value">${cs.position ? `#${cs.position}` : '—'} · ${cs.points ?? 0} pts</div></div>
      <div class="stat-card"><div class="stat-label">Record</div><div class="stat-value">${cs.won ?? 0}W-${cs.drawn ?? 0}D-${cs.lost ?? 0}L</div></div>
      <div class="stat-card"><div class="stat-label">Goals</div><div class="stat-value">${cs.gf ?? 0} scored · ${cs.ga ?? 0} conceded</div></div>
      <div class="stat-card"><div class="stat-label">Form</div><div class="stat-value">${cs.form || '—'}</div></div>
    </div>
    <div class="stats-row">
      <div class="stat-card"><div class="stat-label">Top scorer</div><div class="stat-value">${cs.top_scorer ? `${cs.top_scorer} (${cs.top_scorer_goals})` : '—'}</div></div>
      <div class="stat-card"><div class="stat-label">Top assister</div><div class="stat-value">${cs.top_assister ? `${cs.top_assister} (${cs.top_assister_assists})` : '—'}</div></div>
      <div class="stat-card"><div class="stat-label">Squad value</div><div class="stat-value">${squad.market_value_m ? `€${Math.round(squad.market_value_m)}m` : '—'}</div></div>
      <div class="stat-card"><div class="stat-label">Net spend</div><div class="stat-value">${squad.net_spend_m != null ? `€${squad.net_spend_m.toFixed(0)}m` : '—'}</div></div>
    </div>`;

  document.getElementById('team-content').innerHTML = `
    ${stats}
    <div class="card mt"><h2>Honours</h2>${renderTrophies(profile.trophies, profile.most_recent_major)}</div>
    <div class="card mt"><h2>${profile.predict_season_label} — all predictions</h2>${renderFixtures(profile.fixtures, team)}</div>
    <div class="grid-2 mt">
      <div class="card"><h2>PL season history</h2>${renderHistory(profile.season_history || [])}</div>
      <div class="card"><h2>Squad</h2>${renderSquad(squad, team)}</div>
    </div>`;
}

load().catch((err) => {
  document.getElementById('team-content').innerHTML = `<p class="empty-state">Failed to load: ${err.message}</p>`;
});
