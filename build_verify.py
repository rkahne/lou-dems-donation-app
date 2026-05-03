"""Generates verify.html with candidate data baked in."""
import json

with open('candidates.json') as f:
    data = json.load(f)

# Flatten into a list of candidate objects for the UI
candidates = []
for race in data['races']:
    office = race['office']
    district = race.get('district')
    level = race['level']
    label = f"{office}{f' D{district}' if district else ''}"

    for name, links in race.get('candidate_links', {}).items():
        candidates.append({
            'id': f"{race['id']}::{name}",
            'name': name,
            'office': label,
            'level': level,
            'links': {k: v for k, v in links.items() if v}
        })

candidates_json = json.dumps(candidates, indent=2)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JC Dems — Link Verification</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --blue: #1a56db; --blue-light: #e8f0fe; --green: #057a55; --green-light: #def7ec;
    --red: #e02424; --red-light: #fde8e8; --yellow: #9f580a; --yellow-light: #feecdc;
    --gray: #6b7280; --border: #e5e7eb; --bg: #f9fafb;
  }}
  body {{ font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: #111827; height: 100vh; display: flex; flex-direction: column; }}

  /* Header */
  header {{ background: var(--blue); color: white; padding: 12px 20px; display: flex; align-items: center; gap: 16px; flex-shrink: 0; }}
  header h1 {{ font-size: 1.1rem; font-weight: 700; flex: 1; }}
  .progress-wrap {{ display: flex; align-items: center; gap: 8px; font-size: 0.85rem; }}
  .progress-bar {{ width: 200px; height: 8px; background: rgba(255,255,255,0.3); border-radius: 4px; overflow: hidden; }}
  .progress-fill {{ height: 100%; background: #34d399; border-radius: 4px; transition: width 0.3s; }}
  #progress-text {{ white-space: nowrap; }}
  .save-btn {{ background: white; color: var(--blue); border: none; padding: 6px 14px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; cursor: pointer; }}
  .save-btn:hover {{ background: #f0f4ff; }}

  /* Layout */
  .layout {{ display: flex; flex: 1; overflow: hidden; }}

  /* Sidebar */
  aside {{ width: 280px; border-right: 1px solid var(--border); overflow-y: auto; flex-shrink: 0; background: white; }}
  .sidebar-search {{ padding: 10px 12px; border-bottom: 1px solid var(--border); position: sticky; top: 0; background: white; z-index: 1; }}
  .sidebar-search input {{ width: 100%; padding: 6px 10px; border: 1px solid var(--border); border-radius: 6px; font-size: 0.85rem; }}
  .level-group {{ padding: 6px 0; }}
  .level-header {{ padding: 6px 12px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--gray); background: var(--bg); border-bottom: 1px solid var(--border); }}
  .sidebar-item {{ display: flex; align-items: center; gap: 8px; padding: 7px 12px; cursor: pointer; font-size: 0.83rem; border-left: 3px solid transparent; transition: background 0.1s; }}
  .sidebar-item:hover {{ background: var(--blue-light); }}
  .sidebar-item.active {{ background: var(--blue-light); border-left-color: var(--blue); font-weight: 600; }}
  .sidebar-item .name {{ flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .sidebar-item .badge {{ font-size: 0.7rem; padding: 1px 5px; border-radius: 10px; flex-shrink: 0; }}
  .badge-done {{ background: var(--green-light); color: var(--green); }}
  .badge-partial {{ background: var(--yellow-light); color: var(--yellow); }}
  .badge-none {{ background: var(--border); color: var(--gray); }}
  .badge-nolinks {{ background: #f3f4f6; color: #9ca3af; font-style: italic; }}

  /* Main */
  main {{ flex: 1; overflow-y: auto; padding: 24px; }}
  .candidate-card {{ max-width: 700px; }}
  .card-header {{ margin-bottom: 20px; }}
  .card-header h2 {{ font-size: 1.4rem; font-weight: 700; }}
  .card-header .office {{ color: var(--gray); font-size: 0.9rem; margin-top: 2px; }}
  .card-header .level-badge {{ display: inline-block; font-size: 0.7rem; padding: 2px 8px; border-radius: 10px; font-weight: 600; margin-top: 6px; }}
  .level-federal {{ background: #ede9fe; color: #5b21b6; }}
  .level-state {{ background: #dbeafe; color: #1e40af; }}
  .level-county {{ background: #fef3c7; color: #92400e; }}
  .level-metro {{ background: #d1fae5; color: #065f46; }}

  .links-section h3 {{ font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--gray); margin-bottom: 12px; }}
  .no-links {{ color: var(--gray); font-style: italic; font-size: 0.9rem; padding: 12px 0; }}

  .link-row {{ display: flex; align-items: flex-start; gap: 10px; padding: 12px; background: white; border: 1px solid var(--border); border-radius: 8px; margin-bottom: 8px; transition: border-color 0.2s; }}
  .link-row.verified {{ border-color: var(--green); background: var(--green-light); }}
  .link-row.rejected {{ border-color: var(--red); background: var(--red-light); opacity: 0.7; }}
  .link-icon {{ font-size: 1.2rem; flex-shrink: 0; width: 28px; text-align: center; padding-top: 2px; }}
  .link-body {{ flex: 1; min-width: 0; }}
  .link-type {{ font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--gray); margin-bottom: 2px; }}
  .link-url {{ font-size: 0.82rem; color: var(--blue); word-break: break-all; text-decoration: none; }}
  .link-url:hover {{ text-decoration: underline; }}
  .edit-field {{ width: 100%; margin-top: 6px; padding: 5px 8px; border: 1px solid var(--border); border-radius: 5px; font-size: 0.82rem; }}
  .link-actions {{ display: flex; gap: 6px; flex-shrink: 0; align-items: flex-start; padding-top: 2px; }}
  .btn {{ border: none; padding: 5px 10px; border-radius: 5px; font-size: 0.78rem; font-weight: 600; cursor: pointer; white-space: nowrap; }}
  .btn-open {{ background: var(--blue-light); color: var(--blue); }}
  .btn-open:hover {{ background: #c7d9fb; }}
  .btn-ok {{ background: var(--green-light); color: var(--green); }}
  .btn-ok:hover {{ background: #b3e9d8; }}
  .btn-ok.active {{ background: var(--green); color: white; }}
  .btn-bad {{ background: var(--red-light); color: var(--red); }}
  .btn-bad:hover {{ background: #fbc9c9; }}
  .btn-bad.active {{ background: var(--red); color: white; }}

  .add-link-section {{ margin-top: 16px; }}
  .add-link-section h3 {{ font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--gray); margin-bottom: 10px; }}
  .add-link-row {{ display: flex; gap: 8px; margin-bottom: 8px; align-items: center; }}
  .add-link-row select {{ padding: 5px 8px; border: 1px solid var(--border); border-radius: 5px; font-size: 0.82rem; background: white; }}
  .add-link-row input {{ flex: 1; padding: 5px 8px; border: 1px solid var(--border); border-radius: 5px; font-size: 0.82rem; }}
  .btn-add {{ background: var(--blue); color: white; padding: 5px 12px; border-radius: 5px; font-size: 0.82rem; font-weight: 600; border: none; cursor: pointer; }}

  .nav-row {{ display: flex; gap: 10px; margin-top: 28px; padding-top: 20px; border-top: 1px solid var(--border); }}
  .btn-nav {{ padding: 8px 18px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; border: 1px solid var(--border); background: white; cursor: pointer; }}
  .btn-nav:hover {{ background: var(--blue-light); border-color: var(--blue); }}
  .btn-nav:disabled {{ opacity: 0.4; cursor: default; }}

  .empty-state {{ display: flex; align-items: center; justify-content: center; height: 100%; color: var(--gray); font-size: 1rem; }}
</style>
</head>
<body>
<header>
  <h1>JC Dems 2026 — Link Verification</h1>
  <div class="progress-wrap">
    <div class="progress-bar"><div class="progress-fill" id="prog-fill"></div></div>
    <span id="progress-text">0 / 0 verified</span>
  </div>
  <button class="save-btn" onclick="exportJSON()">Export JSON</button>
</header>
<div class="layout">
  <aside>
    <div class="sidebar-search">
      <input type="text" id="search" placeholder="Search candidates..." oninput="filterSidebar(this.value)">
    </div>
    <div id="sidebar-list"></div>
  </aside>
  <main id="main">
    <div class="empty-state">Select a candidate from the sidebar</div>
  </main>
</div>

<script>
const CANDIDATES = {candidates_json};
let state = {{}};  // id -> {{ links: {{ type: {{ status, url }} }} }}

const LINK_TYPES = [
  {{ key: 'actblue_url',  label: 'ActBlue',   icon: '💙' }},
  {{ key: 'website_url',  label: 'Website',   icon: '🌐' }},
  {{ key: 'facebook_url', label: 'Facebook',  icon: '📘' }},
  {{ key: 'twitter_url',  label: 'X/Twitter', icon: '🐦' }},
  {{ key: 'instagram_url',label: 'Instagram', icon: '📸' }},
];

const LEVELS = ['federal','state','county','metro'];
const LEVEL_LABELS = {{ federal:'Federal', state:'State', county:'County', metro:'Metro Louisville' }};

let currentId = null;
let filteredIds = CANDIDATES.map(c => c.id);

// ─── State management ─────────────────────────────────────────────────────────
function loadState() {{
  try {{ state = JSON.parse(localStorage.getItem('jc-verify-state') || '{{}}'); }} catch(e) {{ state = {{}}; }}
}}
function saveState() {{
  localStorage.setItem('jc-verify-state', JSON.stringify(state));
  updateProgress();
  renderSidebar();
}}
function ensureCandidate(id) {{
  if (!state[id]) state[id] = {{ links: {{}} }};
}}
function setLinkStatus(id, key, status, url) {{
  ensureCandidate(id);
  state[id].links[key] = {{ status, url }};
  saveState();
}}
function addLink(id, key, url) {{
  ensureCandidate(id);
  state[id].links[key] = {{ status: 'added', url }};
  saveState();
  renderMain(id);
}}

// ─── Progress ────────────────────────────────────────────────────────────────
function getVerifiedCount() {{
  return Object.values(state).reduce((n, s) =>
    n + Object.values(s.links).filter(l => l.status === 'ok' || l.status === 'bad' || l.status === 'added').length, 0);
}}
function getTotalLinks() {{
  return CANDIDATES.reduce((n, c) => n + Object.keys(c.links).length, 0);
}}
function getCandidateBadge(c) {{
  const s = state[c.id];
  const total = Object.keys(c.links).length;
  if (total === 0) return {{ cls: 'badge-nolinks', text: 'no links' }};
  if (!s || Object.keys(s.links).length === 0) return {{ cls: 'badge-none', text: '0/' + total }};
  const done = Object.values(s.links).filter(l => l.status === 'ok' || l.status === 'bad' || l.status === 'added').length;
  if (done === total) return {{ cls: 'badge-done', text: '✓' }};
  return {{ cls: 'badge-partial', text: done + '/' + total }};
}}
function updateProgress() {{
  const total = getTotalLinks();
  const done = getVerifiedCount();
  const pct = total ? (done / total * 100) : 0;
  document.getElementById('prog-fill').style.width = pct + '%';
  document.getElementById('progress-text').textContent = done + ' / ' + total + ' verified';
}}

// ─── Sidebar ─────────────────────────────────────────────────────────────────
function renderSidebar() {{
  const list = document.getElementById('sidebar-list');
  const query = document.getElementById('search').value.toLowerCase();
  const visible = CANDIDATES.filter(c =>
    filteredIds.includes(c.id) &&
    (c.name.toLowerCase().includes(query) || c.office.toLowerCase().includes(query))
  );

  let html = '';
  for (const level of LEVELS) {{
    const group = visible.filter(c => c.level === level);
    if (!group.length) continue;
    html += `<div class="level-group">
      <div class="level-header">${{LEVEL_LABELS[level]}}</div>`;
    for (const c of group) {{
      const badge = getCandidateBadge(c);
      const active = c.id === currentId ? ' active' : '';
      html += `<div class="sidebar-item${{active}}" onclick="selectCandidate('${{c.id}}')">
        <span class="name">${{c.name}}</span>
        <span class="badge ${{badge.cls}}">${{badge.text}}</span>
      </div>`;
    }}
    html += '</div>';
  }}
  list.innerHTML = html || '<div style="padding:16px;color:var(--gray);font-size:0.85rem">No results</div>';
}}
function filterSidebar(q) {{ renderSidebar(); }}

// ─── Main panel ──────────────────────────────────────────────────────────────
function selectCandidate(id) {{
  currentId = id;
  renderSidebar();
  renderMain(id);
}}

function renderMain(id) {{
  const c = CANDIDATES.find(x => x.id === id);
  if (!c) return;
  const s = state[id] || {{ links: {{}} }};

  // Merge candidate's original links + any added links in state
  const allLinks = {{ ...c.links }};
  for (const [key, ls] of Object.entries(s.links)) {{
    if (ls.status === 'added') allLinks[key] = ls.url;
    if (ls.status === 'ok' && ls.url !== c.links[key]) allLinks[key] = ls.url; // corrected
  }}

  const levelCls = 'level-' + c.level;
  let linksHtml = '';

  if (Object.keys(allLinks).length === 0) {{
    linksHtml = '<p class="no-links">No links found for this candidate.</p>';
  }} else {{
    for (const lt of LINK_TYPES) {{
      let url = allLinks[lt.key];
      // check if state has override
      if (s.links[lt.key] && (s.links[lt.key].status === 'ok' || s.links[lt.key].status === 'added')) {{
        url = s.links[lt.key].url;
      }}
      if (!url) continue;

      const ls = s.links[lt.key] || {{}};
      const rowCls = ls.status === 'ok' ? ' verified' : ls.status === 'bad' ? ' rejected' : '';
      const okActive = ls.status === 'ok' ? ' active' : '';
      const badActive = ls.status === 'bad' ? ' active' : '';

      linksHtml += `
      <div class="link-row${{rowCls}}" id="row-${{lt.key}}">
        <div class="link-icon">${{lt.icon}}</div>
        <div class="link-body">
          <div class="link-type">${{lt.label}}</div>
          <a class="link-url" href="${{url}}" target="_blank" rel="noopener">${{url}}</a>
          ${{ls.status === 'bad' ? `<input class="edit-field" id="edit-${{lt.key}}" placeholder="Enter correct URL..." value="${{ls.correctedUrl || ''}}" onchange="updateCorrection('${{id}}','${{lt.key}}',this.value)">` : ''}}
        </div>
        <div class="link-actions">
          <button class="btn btn-open" onclick="window.open('${{url}}','_blank')">Open ↗</button>
          <button class="btn btn-ok${{okActive}}" onclick="markLink('${{id}}','${{lt.key}}','ok','${{url}}')">✓</button>
          <button class="btn btn-bad${{badActive}}" onclick="markLink('${{id}}','${{lt.key}}','bad','${{url}}')">✗</button>
        </div>
      </div>`;
    }}
  }}

  // Type dropdown for add-link (only types not already present)
  const presentTypes = new Set(Object.keys(allLinks));
  const addOptions = LINK_TYPES.filter(lt => !presentTypes.has(lt.key))
    .map(lt => `<option value="${{lt.key}}">${{lt.label}}</option>`).join('');

  const idx = CANDIDATES.findIndex(x => x.id === id);

  document.getElementById('main').innerHTML = `
  <div class="candidate-card">
    <div class="card-header">
      <h2>${{c.name}}</h2>
      <div class="office">${{c.office}}</div>
      <span class="level-badge ${{levelCls}}">${{LEVEL_LABELS[c.level]}}</span>
    </div>
    <div class="links-section">
      <h3>Found Links</h3>
      ${{linksHtml}}
    </div>
    ${{addOptions ? `
    <div class="add-link-section">
      <h3>Add Missing Link</h3>
      <div class="add-link-row">
        <select id="add-type">${{addOptions}}</select>
        <input id="add-url" type="url" placeholder="https://...">
        <button class="btn-add" onclick="submitAddLink('${{id}}')">Add</button>
      </div>
    </div>` : ''}}
    <div class="nav-row">
      <button class="btn-nav" onclick="navigate(-1)" ${{idx === 0 ? 'disabled' : ''}}>← Previous</button>
      <button class="btn-nav" onclick="navigate(1)" ${{idx === CANDIDATES.length-1 ? 'disabled' : ''}}>Next →</button>
    </div>
  </div>`;
}}

function markLink(id, key, status, url) {{
  const existing = (state[id] && state[id].links[key]) || {{}};
  // Toggle off if clicking same button again
  if (existing.status === status) {{
    ensureCandidate(id);
    delete state[id].links[key];
  }} else {{
    setLinkStatus(id, key, status, url);
  }}
  renderMain(id);
}}

function updateCorrection(id, key, url) {{
  ensureCandidate(id);
  if (state[id].links[key]) state[id].links[key].correctedUrl = url;
  saveState();
}}

function submitAddLink(id) {{
  const key = document.getElementById('add-type').value;
  const url = document.getElementById('add-url').value.trim();
  if (!url) return;
  addLink(id, key, url);
}}

function navigate(dir) {{
  const idx = CANDIDATES.findIndex(x => x.id === currentId);
  const next = CANDIDATES[idx + dir];
  if (next) selectCandidate(next.id);
}}

// ─── Export ──────────────────────────────────────────────────────────────────
function exportJSON() {{
  // Build enriched output: merge original links with verified state
  const output = CANDIDATES.map(c => {{
    const s = state[c.id] || {{ links: {{}} }};
    const mergedLinks = {{ ...c.links }};

    for (const [key, ls] of Object.entries(s.links)) {{
      if (ls.status === 'bad') {{
        if (ls.correctedUrl) mergedLinks[key] = ls.correctedUrl;
        else delete mergedLinks[key];
      }} else if (ls.status === 'added') {{
        mergedLinks[key] = ls.url;
      }} else if (ls.status === 'ok' && ls.url) {{
        mergedLinks[key] = ls.url;
      }}
    }}

    return {{
      id: c.id, name: c.name, office: c.office, level: c.level,
      links: mergedLinks,
      verification: s.links
    }};
  }});

  const blob = new Blob([JSON.stringify(output, null, 2)], {{ type: 'application/json' }});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'verified_links.json';
  a.click();
}}

// ─── Init ────────────────────────────────────────────────────────────────────
loadState();
renderSidebar();
updateProgress();
</script>
</body>
</html>"""

with open('verify.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("verify.html written")
