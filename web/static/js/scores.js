/** Shared helpers for predicted vs actual score display. */

function isPlayedMatch(m) {
  return !!(m?.played || (m?.FTHG != null && m?.FTAG != null && m?.FTR));
}

function predScoreText(m) {
  if (m?.pred_score) return m.pred_score;
  const h = m?.pred_home_goals;
  const a = m?.pred_away_goals;
  if (h != null && a != null) return `${h}–${a}`;
  return '—';
}

function actualScoreText(m) {
  if (m?.actual_score) return m.actual_score;
  if (m?.FTHG != null && m?.FTAG != null) return `${parseInt(m.FTHG, 10)}–${parseInt(m.FTAG, 10)}`;
  return '—';
}

/** Inline: "2–0 → 3–0" or predicted only for upcoming. */
function scoreCompareInline(m) {
  if (!isPlayedMatch(m)) return predScoreText(m);
  return `${predScoreText(m)} → ${actualScoreText(m)}`;
}

/** Block layout for fixture cards and match hero. */
function renderScoreCompare(m, { size = 'lg' } = {}) {
  if (!isPlayedMatch(m)) {
    return `
      <div class="score-center">
        <div class="pred-score score-${size}">${predScoreText(m)}</div>
        <div class="score-label">Predicted score</div>
      </div>`;
  }
  const outcomeOk = m.pred_ftr === m.FTR;
  const scoreOk = m.score_correct || (
    m.pred_home_goals != null
    && m.pred_away_goals != null
    && parseInt(m.FTHG, 10) === m.pred_home_goals
    && parseInt(m.FTAG, 10) === m.pred_away_goals
  );
  return `
    <div class="score-center score-compare score-${size}">
      <div class="score-compare-row">
        <div class="score-compare-col ${scoreOk ? 'correct' : 'incorrect'}">
          <div class="score-compare-value">${predScoreText(m)}</div>
          <div class="score-label">Predicted</div>
        </div>
        <div class="score-compare-vs">vs</div>
        <div class="score-compare-col actual">
          <div class="score-compare-value">${actualScoreText(m)}</div>
          <div class="score-label">Actual</div>
        </div>
      </div>
      <div class="score-compare-meta ${outcomeOk ? 'correct' : 'incorrect'}">${outcomeOk ? 'Outcome ✓' : 'Outcome ✗'}</div>
    </div>`;
}
