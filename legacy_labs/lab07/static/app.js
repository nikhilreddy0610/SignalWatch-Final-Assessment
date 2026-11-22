const reportList = document.querySelector('#report-list');
const searchInput = document.querySelector('#search-input');
const categoryFilter = document.querySelector('#category-filter');
let searchTimer;

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[character]);
}

function safeExternalUrl(value) {
  try {
    const url = new URL(value);
    return ['https:', 'http:'].includes(url.protocol) ? url.href : '#';
  } catch {
    return '#';
  }
}

async function getJson(url, options) {
  const response = await fetch(url, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
  return body;
}

function prettyDate(date) {
  if (!date) return 'Date unavailable';
  const parsed = new Date(date);
  return Number.isNaN(parsed.valueOf()) ? 'Date unavailable' : parsed.toLocaleDateString();
}

async function loadReports() {
  reportList.innerHTML = '<div class="empty-state">Loading reports…</div>';
  const params = new URLSearchParams({
    q: searchInput.value.trim(),
    category: categoryFilter.value,
  });
  try {
    const data = await getJson(`/api/reports?${params}`);
    document.querySelector('#result-count').textContent = `${data.total} REPORT${data.total === 1 ? '' : 'S'}`;
    if (!data.items.length) {
      reportList.innerHTML = '<div class="empty-state">No reports match these filters.</div>';
      return;
    }
    reportList.innerHTML = data.items.map((report) => {
      const url = safeExternalUrl(report.url);
      return `<article class="report">
        <div class="report-meta">
          <span class="source-name">${escapeHtml(report.sourceName)}</span>
          <span class="category-badge ${escapeHtml(report.category)}">${escapeHtml(report.category)}</span>
          <span class="confidence">${escapeHtml(report.confidence)} confidence</span>
        </div>
        <h3 class="report-title"><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(report.title)}</a></h3>
        <p class="report-summary">${escapeHtml(report.summary)}</p>
        <div class="report-footer"><span>${escapeHtml(prettyDate(report.publishedAt))}</span><span>${report.indicatorCount} LINKED INDICATOR${report.indicatorCount === 1 ? '' : 'S'}</span></div>
      </article>`;
    }).join('');
  } catch (error) {
    reportList.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function loadStats() {
  try {
    const stats = await getJson('/api/stats');
    document.querySelector('#stat-reports').textContent = stats.reports.toLocaleString();
    document.querySelector('#stat-sources').textContent = stats.sources.toLocaleString();
    document.querySelector('#stat-indicators').textContent = stats.indicators.toLocaleString();
    document.querySelector('#stat-categories').textContent = stats.categories.toLocaleString();
    document.querySelector('#mode-label').textContent = stats.mode === 'mongodb' ? 'MONGODB CONNECTED' : 'DEMO MODE';
    document.querySelector('#last-updated').textContent = stats.mode === 'demo' ? 'SAMPLE DATA' : 'DATABASE CONNECTED';
  } catch (error) {
    document.querySelector('#mode-label').textContent = 'API UNAVAILABLE';
    console.error(error);
  }
}

async function loadSchemaStats() {
  try {
    const data = await getJson('/api/lab/schema');
    document.querySelector('#schema-mode').textContent = data.mode.toUpperCase();
    document.querySelector('#average-size').textContent = `${data.averageBytes.toLocaleString()} B`;
    document.querySelector('#maximum-size').textContent = `${data.maximumBytes.toLocaleString()} B`;
    document.querySelector('#schema-table').innerHTML = Object.entries(data.collections).map(([name, stats]) =>
      `<tr><td>${escapeHtml(name)}</td><td>${stats.count.toLocaleString()}</td><td>${stats.averageBytes.toLocaleString()} B</td><td>${stats.maximumBytes.toLocaleString()} B</td></tr>`
    ).join('');
    const verdict = document.querySelector('#size-verdict');
    if (data.maximumBytes < data.limitBytes * 0.75) {
      verdict.textContent = `PASS · Largest document is ${(data.maximumBytes / data.limitBytes * 100).toFixed(3)}% of the 16 MiB limit. No measured document approaches the limit.`;
      verdict.style.color = 'var(--green)';
    } else {
      verdict.textContent = 'WARNING · A measured document is near the MongoDB document limit.';
      verdict.style.color = 'var(--red)';
    }
  } catch (error) {
    document.querySelector('#size-verdict').textContent = error.message;
  }
}

document.querySelectorAll('.tab').forEach((tab) => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach((item) => item.classList.toggle('active', item === tab));
    document.querySelectorAll('.page').forEach((page) => page.classList.toggle('active', page.id === tab.dataset.page));
  });
});

searchInput.addEventListener('input', () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadReports, 220);
});
categoryFilter.addEventListener('change', loadReports);

document.querySelector('#classifier-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const target = document.querySelector('#classification-result');
  const text = document.querySelector('#classifier-text').value;
  target.innerHTML = '<span class="muted small">Analyzing…</span>';
  try {
    const result = await getJson('/api/classify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    target.innerHTML = `<span class="result-category">${escapeHtml(result.category)}</span>
      <p class="result-signals">${result.signals.length ? `Signals: ${escapeHtml(result.signals.join(', '))}` : 'No matching keyword signals.'} · ${escapeHtml(result.confidence)} confidence</p>`;
  } catch (error) {
    target.innerHTML = `<span class="small" style="color:var(--red)">${escapeHtml(error.message)}</span>`;
  }
});

document.querySelector('#refresh-button').addEventListener('click', async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  button.textContent = '↻ Refreshing…';
  try {
    const result = await getJson('/api/refresh', { method: 'POST' });
    const suffix = result.errors.length ? ` (${result.errors.length} feed warning${result.errors.length === 1 ? '' : 's'})` : '';
    document.querySelector('#last-updated').textContent = `${result.inserted} NEW REPORT${result.inserted === 1 ? '' : 'S'}${suffix}`;
    await Promise.all([loadReports(), loadStats(), loadSchemaStats()]);
  } catch (error) {
    document.querySelector('#last-updated').textContent = `REFRESH FAILED · ${error.message}`;
  } finally {
    button.disabled = false;
    button.textContent = '↻ Refresh feeds';
  }
});

Promise.all([loadReports(), loadStats(), loadSchemaStats()]);
