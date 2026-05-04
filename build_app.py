#!/usr/bin/env python3
"""Build index.html for the Jefferson County Democrats 2026 donation app."""

import json
import os
import re

# ── Load source data ──────────────────────────────────────────────────────────

with open('candidates.json', encoding='utf-8') as f:
    candidates_data = json.load(f)

with open('verified_links.json', encoding='utf-8') as f:
    verified_raw = json.load(f)

verified_lookup = {e['id']: e.get('links', {}) for e in verified_raw}


def load_geojson(path):
    with open(path) as f:
        return json.load(f)


GEO = {
    'house':         load_geojson('data/house.geojson'),
    'senate':        load_geojson('data/senate.geojson'),
    'congress':      load_geojson('data/congress.geojson'),
    'metro_council': load_geojson('data/metro_council.geojson'),
    'county':        load_geojson('data/county.geojson'),
    'metro_all':     load_geojson('data/metro_all.geojson'),
}

# ── Image path lookup ─────────────────────────────────────────────────────────

PHOTO_OVERRIDES = {
    'Al Gentry':              'alvin-gentry',
    'William "Woody" Zorn':   'woody-zorn',
    'Rosalind "Roz" Welch':   'roz-welch',
    'Jennifer Chappell':      'jennifer-chapppell',   # triple-p typo in filename
    'Melina Hettiaratchi':    'melina-hettiarachi',   # typo in filename
}

def candidate_slug(name):
    if name in PHOTO_OVERRIDES:
        return PHOTO_OVERRIDES[name]
    clean = re.sub(r'["“”][^"“”]*["“”]', '', name)
    clean = clean.lower().strip()
    clean = re.sub(r'[^a-z0-9]+', '-', clean).strip('-')
    return clean

def get_image(name):
    slug = candidate_slug(name)
    path = f'img/processed/{slug}.png'
    return path if os.path.exists(path) else None

# ── Build ENTRIES list ────────────────────────────────────────────────────────
# One entry per candidate (multiple per race for contested primaries).

def geo_for_race(race_id, level, district):
    if level == 'federal':
        return ('county', None) if race_id == 'us-senate-ky' else ('congress', district)
    if level == 'state':
        return ('house', district) if 'house' in race_id else ('senate', district)
    if level == 'county':
        return ('county', None)
    # metro
    return ('county', None) if race_id == 'louisville-mayor' else ('metro_council', district)

def tab_for_race(race_id, level):
    if level == 'federal': return 'federal'
    if level == 'state':   return 'house' if 'house' in race_id else 'senate'
    if level == 'county':  return 'county'
    return 'metro'

ENTRIES = []
for race in candidates_data['races']:
    race_id  = race['id']
    level    = race['level']
    district = race.get('district')
    tab      = tab_for_race(race_id, level)
    geo_layer, map_district = geo_for_race(race_id, level, district)

    confirmed = race.get('general_election_candidate') or race.get('ldp_endorsed')
    candidates = [confirmed] if confirmed else race.get('democratic_primary_candidates', [])
    is_primary = not bool(confirmed)

    for cand in candidates:
        links = verified_lookup.get(f'{race_id}::{cand}', {})
        ENTRIES.append({
            'id':           f'{race_id}::{cand}',
            'race_id':      race_id,
            'office':       race['office'],
            'district':     district,
            'level':        level,
            'tab':          tab,
            'geo_layer':    geo_layer,
            'map_district': map_district,
            'candidate':    cand,
            'is_primary':   is_primary,
            'image':        get_image(cand),
            'links':        links,
        })

# ── Generate HTML ─────────────────────────────────────────────────────────────

ENTRIES_JSON = json.dumps(ENTRIES, indent=2)
GEO_JSON     = json.dumps(GEO)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Jefferson County Democrats 2026</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: #f0f4fa;
      min-height: 100dvh;
      display: flex;
      flex-direction: column;
    }

    /* ── Header ── */
    header {
      background: #1565c0;
      color: #fff;
      padding: 10px 20px;
      display: flex;
      align-items: center;
      gap: 16px;
      flex-shrink: 0;
      flex-wrap: wrap;
    }
    header h1 { font-size: 1.05rem; font-weight: 700; flex: 1; white-space: nowrap; }
    #addr-wrap { display: flex; gap: 6px; align-items: center; }
    #addr-input {
      padding: 6px 14px;
      border: none;
      border-radius: 20px;
      font-size: 0.83rem;
      width: 280px;
      outline: none;
      background: rgba(255,255,255,0.15);
      color: #fff;
    }
    #addr-input::placeholder { color: rgba(255,255,255,0.65); }
    #addr-input:focus { background: rgba(255,255,255,0.25); }
    #addr-btn {
      padding: 6px 16px;
      background: rgba(255,255,255,0.2);
      color: #fff;
      border: 1px solid rgba(255,255,255,0.4);
      border-radius: 20px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      transition: background 0.15s;
    }
    #addr-btn:hover { background: rgba(255,255,255,0.3); }
    #addr-btn:disabled { opacity: 0.5; cursor: default; }
    #addr-err { font-size: 0.78rem; color: #ffcdd2; display: none; width: 100%; }

    /* ── Tabs ── */
    #tabs {
      background: #fff;
      border-bottom: 2px solid #1565c0;
      display: flex;
      overflow-x: auto;
      flex-shrink: 0;
    }
    .tab-btn {
      padding: 10px 22px;
      font-size: 0.87rem;
      font-weight: 600;
      color: #666;
      border: none;
      background: none;
      cursor: pointer;
      white-space: nowrap;
      border-bottom: 3px solid transparent;
      margin-bottom: -2px;
      transition: color 0.15s;
    }
    .tab-btn:hover { color: #1565c0; }
    .tab-btn.active { color: #1565c0; border-bottom-color: #1565c0; }

    /* ── Card grid ── */
    #grid-wrap { flex: 1; overflow-y: auto; padding: 24px 20px; }
    #card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
      gap: 20px;
      max-width: 1400px;
      margin: 0 auto;
    }

    /* ── Candidate card ── */
    .ccard {
      background: #fff;
      border-radius: 14px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.07);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 20px 16px 16px;
      text-align: center;
      transition: box-shadow 0.18s, transform 0.12s;
    }
    .ccard:hover { box-shadow: 0 6px 20px rgba(21,101,192,0.13); transform: translateY(-2px); }
    .ccard.is-primary { opacity: 0.82; }

    .cphoto-wrap {
      width: 130px; height: 130px;
      border-radius: 50%;
      background: #dce8fb;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 14px;
      flex-shrink: 0;
    }
    .cphoto { width: 100%; height: 100%; object-fit: cover; }
    .cphoto-placeholder { font-size: 3rem; color: #90b4e8; }

    .cbadges { display: flex; gap: 5px; justify-content: center; flex-wrap: wrap; margin-bottom: 6px; }
    .dist-badge {
      font-size: 0.68rem; font-weight: 700;
      color: #1565c0; background: #e3eefb;
      padding: 2px 8px; border-radius: 10px;
    }
    .primary-badge {
      font-size: 0.66rem; font-weight: 600;
      color: #c77800; background: #fff3cd;
      padding: 2px 8px; border-radius: 10px;
    }

    .cname {
      font-size: 1rem; font-weight: 700;
      color: #1a1a1a; line-height: 1.25;
      margin-bottom: 3px;
    }
    .coffice {
      font-size: 0.75rem; color: #777;
      margin-bottom: 14px; line-height: 1.3;
    }

    .clinks { width: 100%; display: flex; flex-direction: column; gap: 7px; }
    .btn-donate {
      display: block;
      background: #1565c0;
      color: #fff;
      text-decoration: none;
      font-size: 0.82rem;
      font-weight: 700;
      padding: 8px 0;
      border-radius: 20px;
      transition: background 0.15s;
      width: 100%;
    }
    .btn-donate:hover { background: #0d47a1; }
    .btn-donate.cd { background: #2e7d32; }
    .btn-donate.cd:hover { background: #1b5e20; }
    .social-row {
      display: flex; justify-content: center; gap: 8px;
    }
    .social-btn {
      font-size: 1.1rem; text-decoration: none;
      transition: transform 0.1s;
      display: inline-block;
    }
    .social-btn:hover { transform: scale(1.2); }

    .view-map-link {
      display: inline-block;
      margin-top: 10px;
      font-size: 0.73rem;
      color: #1565c0;
      text-decoration: underline;
      cursor: pointer;
    }
    .view-map-link:hover { color: #0d47a1; }

    .grid-empty {
      grid-column: 1 / -1;
      text-align: center;
      padding: 60px 20px;
      color: #aaa;
      font-size: 1rem;
    }

    /* ── Map modal ── */
    .modal-overlay {
      display: none;
      position: fixed; inset: 0;
      background: rgba(0,0,0,0.5);
      z-index: 9998;
      align-items: flex-start;
      justify-content: center;
      padding: 40px 16px;
      overflow-y: auto;
    }
    .modal-overlay.open { display: flex; }
    .modal-box {
      background: #fff;
      border-radius: 12px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.22);
      width: 100%; max-width: 640px;
      overflow: hidden;
    }
    .modal-head {
      background: #1565c0; color: #fff;
      padding: 14px 20px;
      display: flex; align-items: center; justify-content: space-between; gap: 12px;
    }
    .modal-head h2 { font-size: 0.97rem; font-weight: 700; }
    .modal-head p  { font-size: 0.78rem; opacity: 0.82; margin-top: 2px; }
    .modal-close {
      background: none; border: none; color: #fff;
      font-size: 1.3rem; cursor: pointer; opacity: 0.8; padding: 0 4px;
    }
    .modal-close:hover { opacity: 1; }

    /* Map modal map */
    #map-modal-map { height: 380px; }

    /* Address results modal */
    #addr-modal-body { padding: 6px 0; }
    .modal-section-head {
      font-size: 0.7rem; font-weight: 700; color: #999;
      text-transform: uppercase; letter-spacing: 0.06em;
      padding: 10px 20px 4px;
    }
    .modal-entry {
      padding: 10px 20px;
      border-bottom: 1px solid #f2f2f2;
    }
    .modal-entry:last-child { border-bottom: none; }
    .me-photo-wrap {
      width: 52px; height: 52px; border-radius: 50%;
      background: #dce8fb; overflow: hidden;
      flex-shrink: 0; display: flex; align-items: center; justify-content: center;
    }
    .me-photo { width: 100%; height: 100%; object-fit: cover; }
    .me-placeholder { font-size: 1.5rem; color: #90b4e8; }
    .me-info { flex: 1; }
    .me-row { display: flex; align-items: center; gap: 12px; }
    .me-name  { font-size: 0.92rem; font-weight: 700; color: #1a1a1a; }
    .me-office { font-size: 0.74rem; color: #777; margin: 1px 0 7px; }
    .me-links { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
    .me-donate { background: #1565c0; color: #fff; padding: 5px 12px; border-radius: 14px; font-size: 0.78rem; font-weight: 700; text-decoration: none; }
    .me-donate.cd { background: #2e7d32; }
    .me-social { background: #e3eefb; color: #1565c0; padding: 5px 10px; border-radius: 14px; font-size: 0.78rem; font-weight: 600; text-decoration: none; }
    .me-view { font-size: 0.73rem; color: #1565c0; text-decoration: underline; cursor: pointer; margin-top: 6px; display: inline-block; }
    .addr-none { padding: 24px 20px; color: #aaa; font-size: 0.88rem; text-align: center; }
  </style>
</head>
<body>

<header>
  <h1>&#127455; Jefferson County Democrats &mdash; 2026</h1>
  <div id="addr-wrap">
    <input id="addr-input" type="text" placeholder="&#128269; Enter your address to find your candidates" autocomplete="street-address">
    <button id="addr-btn" onclick="lookupAddress()">Find</button>
  </div>
  <span id="addr-err"></span>
</header>

<div id="tabs">
  <button class="tab-btn active" data-tab="federal">Federal</button>
  <button class="tab-btn" data-tab="senate">State Senate</button>
  <button class="tab-btn" data-tab="house">State House</button>
  <button class="tab-btn" data-tab="county">County</button>
  <button class="tab-btn" data-tab="metro">Metro</button>
</div>

<div id="grid-wrap">
  <div id="card-grid"></div>
</div>

<!-- District map modal -->
<div class="modal-overlay" id="map-modal">
  <div class="modal-box">
    <div class="modal-head">
      <div>
        <h2 id="map-modal-title"></h2>
        <p id="map-modal-sub"></p>
      </div>
      <button class="modal-close" onclick="closeMapModal()">&#x2715;</button>
    </div>
    <div id="map-modal-map"></div>
  </div>
</div>

<!-- Address results modal -->
<div class="modal-overlay" id="addr-modal">
  <div class="modal-box">
    <div class="modal-head">
      <div>
        <h2>Your Candidates</h2>
        <p id="addr-modal-matched"></p>
      </div>
      <button class="modal-close" onclick="closeAddrModal()">&#x2715;</button>
    </div>
    <div id="addr-modal-body"></div>
  </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<script>
const ENTRIES = __ENTRIES__;
const GEO     = __GEOJSON__;

// ── State ─────────────────────────────────────────────────────────────────────
let currentTab = 'federal';

// ── Helpers ───────────────────────────────────────────────────────────────────
function distLabel(e) {
  const { tab, district } = e;
  if (!district) return tab === 'metro' ? 'Mayor' : 'Statewide';
  if (tab === 'federal') return `CD-${district}`;
  if (tab === 'senate')  return `SD-${district}`;
  if (tab === 'house')   return `HD-${district}`;
  if (tab === 'metro')   return `MC-${district}`;
  if (tab === 'county')  return `D-${district}`;
  return `${district}`;
}

// ── Card rendering ────────────────────────────────────────────────────────────
function renderCards() {
  const entries = ENTRIES
    .filter(e => e.tab === currentTab)
    .sort((a, b) => {
      // confirmed before primary
      if (a.is_primary !== b.is_primary) return a.is_primary ? 1 : -1;
      if (a.district === null && b.district !== null) return -1;
      if (a.district !== null && b.district === null) return 1;
      if (a.district !== b.district) return (a.district || 0) - (b.district || 0);
      return a.candidate.localeCompare(b.candidate);
    });

  const grid = document.getElementById('card-grid');
  if (!entries.length) {
    grid.innerHTML = '<div class="grid-empty">No candidates in this category yet.</div>';
    return;
  }

  grid.innerHTML = entries.map(e => cardHtml(e)).join('');
}

function cardHtml(e) {
  const imgHtml = e.image
    ? `<img class="cphoto" src="${e.image}" alt="${e.candidate}" loading="lazy">`
    : `<span class="cphoto-placeholder">&#128100;</span>`;

  const badge = distLabel(e);
  const badgeHtml = `<span class="dist-badge">${badge}</span>` +
    (e.is_primary ? '<span class="primary-badge">Primary Pending</span>' : '');

  const donateUrl = e.links.actblue_url || e.links.campaign_deputy_url;
  const donateLabel = e.links.actblue_url ? '&#128153; Donate on ActBlue' : '&#128181; Donate';
  const donateCls   = e.links.campaign_deputy_url && !e.links.actblue_url ? ' cd' : '';
  const donateHtml  = donateUrl
    ? `<a class="btn-donate${donateCls}" href="${donateUrl}" target="_blank" rel="noopener">${donateLabel}</a>`
    : '';

  const socials = [
    ['website_url', '&#127760;', 'Website'],
    ['facebook_url', '&#128216;', 'Facebook'],
    ['twitter_url', '&#128038;', 'X/Twitter'],
    ['instagram_url', '&#128247;', 'Instagram'],
  ].filter(([k]) => e.links[k])
   .map(([k, icon, label]) => `<a class="social-btn" href="${e.links[k]}" target="_blank" rel="noopener" title="${label}">${icon}</a>`)
   .join('');

  const safeId = e.id.replace(/"/g, '&quot;');
  const viewMap = e.geo_layer !== 'county'
    ? `<span class="view-map-link" data-id="${safeId}" onclick="openMapModal(this.dataset.id)">View district &rarr;</span>`
    : '';

  return `<div class="ccard${e.is_primary ? ' is-primary' : ''}">
    <div class="cphoto-wrap">${imgHtml}</div>
    <div class="cbadges">${badgeHtml}</div>
    <div class="cname">${e.candidate}</div>
    <div class="coffice">${e.office}</div>
    <div class="clinks">
      ${donateHtml}
      ${socials ? `<div class="social-row">${socials}</div>` : ''}
    </div>
    ${viewMap}
  </div>`;
}

// ── Tab switching ─────────────────────────────────────────────────────────────
function selectTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
  renderCards();
}

document.querySelectorAll('.tab-btn').forEach(btn =>
  btn.addEventListener('click', () => selectTab(btn.dataset.tab)));

// ── District map modal ────────────────────────────────────────────────────────
let leafMap = null;
const mapLayers = {};

function openMapModal(entryId) {
  const e = ENTRIES.find(x => x.id === entryId);
  if (!e) return;

  document.getElementById('map-modal-title').textContent = e.candidate;
  document.getElementById('map-modal-sub').textContent = e.office + (e.district ? ` — District ${e.district}` : '');
  document.getElementById('map-modal').classList.add('open');

  // Init map once
  if (!leafMap) {
    leafMap = L.map('map-modal-map').setView([38.18, -85.75], 11);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
      maxZoom: 18,
    }).addTo(leafMap);
  }

  setTimeout(() => {
    leafMap.invalidateSize();
    for (const ly of Object.values(mapLayers)) ly.remove();

    // County outline always shown
    mapLayers.county = L.geoJSON(GEO.county, {
      style: { color: '#546e7a', weight: 1.5, fill: false, dashArray: '5 4' }
    }).addTo(leafMap);

    if (e.geo_layer === 'county') {
      mapLayers.fill = L.geoJSON(GEO.county, {
        style: { fillColor: '#1565c0', fillOpacity: 0.45, color: '#0d47a1', weight: 2 }
      }).addTo(leafMap);
      leafMap.fitBounds(mapLayers.fill.getBounds(), { padding: [20, 20] });
      return;
    }

    const layer = GEO[e.geo_layer];
    const target = layer.features.find(f => f.properties.district === e.map_district);

    // All districts in layer (gray background)
    mapLayers.all = L.geoJSON(layer, {
      style: { color: '#90a4ae', weight: 0.8, fillColor: '#cfd8dc', fillOpacity: 0.18 }
    }).addTo(leafMap);

    if (target) {
      mapLayers.sel = L.geoJSON({ type: 'FeatureCollection', features: [target] }, {
        style: { color: '#0d47a1', weight: 2.5, fillColor: '#1565c0', fillOpacity: 0.55 }
      }).addTo(leafMap);
      leafMap.fitBounds(mapLayers.sel.getBounds(), { padding: [30, 30] });
    }
  }, 80);
}

function closeMapModal() {
  document.getElementById('map-modal').classList.remove('open');
}

document.getElementById('map-modal').addEventListener('click', function(e) {
  if (e.target === this) closeMapModal();
});

// ── Address lookup ────────────────────────────────────────────────────────────
document.getElementById('addr-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') lookupAddress();
});

function setAddrErr(msg) {
  const el = document.getElementById('addr-err');
  el.textContent = msg;
  el.style.display = msg ? 'block' : 'none';
}

async function geocodeAddress(raw) {
  const query = /,\s*(KY|kentucky)/i.test(raw) ? raw : raw + ', Louisville, KY';

  try {
    const url = 'https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?' +
      'benchmark=Public_AR_Current&format=json&address=' + encodeURIComponent(query);
    const data = await fetch(url).then(r => r.json());
    const m = data.result?.addressMatches;
    if (m?.length) return { lon: m[0].coordinates.x, lat: m[0].coordinates.y, addr: m[0].matchedAddress };
  } catch {}

  try {
    const url = 'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?' +
      'outFields=Match_addr&maxLocations=1&f=json&SingleLine=' + encodeURIComponent(query);
    const data = await fetch(url).then(r => r.json());
    const c = data.candidates?.[0];
    if (c?.score >= 80) return { lon: c.location.x, lat: c.location.y, addr: c.address };
  } catch {}

  return null;
}

function pipRing(px, py, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    if ((yi > py) !== (yj > py) && px < ((xj - xi) * (py - yi)) / (yj - yi) + xi)
      inside = !inside;
  }
  return inside;
}

function pip(lon, lat, feat) {
  const g = feat.geometry;
  if (g.type === 'Polygon')      return pipRing(lon, lat, g.coordinates[0]);
  if (g.type === 'MultiPolygon') return g.coordinates.some(p => pipRing(lon, lat, p[0]));
  return false;
}

function findDistrict(lon, lat, key) {
  for (const f of GEO[key].features) if (pip(lon, lat, f)) return f.properties.district;
  return null;
}

async function lookupAddress() {
  const raw = document.getElementById('addr-input').value.trim();
  if (!raw) return;
  const btn = document.getElementById('addr-btn');
  btn.disabled = true; btn.textContent = '...';
  setAddrErr('');

  const result = await geocodeAddress(raw);
  btn.disabled = false; btn.textContent = 'Find';

  if (!result) return setAddrErr('Address not found. Try including city and state.');

  const { lon, lat, addr } = result;
  if (!GEO.county.features.some(f => pip(lon, lat, f)))
    return setAddrErr('That address appears to be outside Jefferson County.');

  const cong   = findDistrict(lon, lat, 'congress');
  const senate = findDistrict(lon, lat, 'senate');
  const house  = findDistrict(lon, lat, 'house');
  const metro  = findDistrict(lon, lat, 'metro_all');

  const matches = ENTRIES.filter(e => {
    if (e.tab === 'federal') return e.id.startsWith('us-senate') || e.map_district === cong;
    if (e.tab === 'senate')  return e.map_district === senate;
    if (e.tab === 'house')   return e.map_district === house;
    if (e.tab === 'county')  return !e.district;
    if (e.tab === 'metro')   return e.id.startsWith('louisville-mayor') || e.map_district === metro;
    return false;
  });

  showAddrModal(addr, matches);
}

const TAB_LABELS = { federal: 'Federal', senate: 'State Senate', house: 'State House', county: 'County', metro: 'Metro' };

function showAddrModal(addr, entries) {
  document.getElementById('addr-modal-matched').textContent = addr;
  const grouped = {};
  for (const e of entries) (grouped[e.tab] = grouped[e.tab] || []).push(e);

  let html = '';
  for (const tab of ['federal', 'senate', 'house', 'county', 'metro']) {
    if (!grouped[tab]) continue;
    html += `<div class="modal-section-head">${TAB_LABELS[tab]}</div>`;
    for (const e of grouped[tab]) {
      const imgHtml = e.image
        ? `<img class="me-photo" src="${e.image}" alt="${e.candidate}">`
        : `<span class="me-placeholder">&#128100;</span>`;
      const donateUrl = e.links.actblue_url || e.links.campaign_deputy_url;
      const donateCls = e.links.campaign_deputy_url && !e.links.actblue_url ? ' cd' : '';
      const donateHtml = donateUrl
        ? `<a class="me-donate${donateCls}" href="${donateUrl}" target="_blank" rel="noopener">${e.links.actblue_url ? '&#128153; ActBlue' : '&#128181; Donate'}</a>` : '';
      const socials = [['website_url','&#127760;'],['facebook_url','&#128216;'],['twitter_url','&#128038;'],['instagram_url','&#128247;']]
        .filter(([k]) => e.links[k])
        .map(([k, icon]) => `<a class="me-social" href="${e.links[k]}" target="_blank" rel="noopener">${icon}</a>`)
        .join('');
      const safeId = e.id.replace(/"/g, '&quot;');
      const viewMap = e.geo_layer !== 'county'
        ? `<span class="me-view" data-id="${safeId}" onclick="closeAddrModal();openMapModal(this.dataset.id)">View district &rarr;</span>` : '';
      html += `<div class="modal-entry">
        <div class="me-row">
          <div class="me-photo-wrap">${imgHtml}</div>
          <div class="me-info">
            <div class="me-name">${e.candidate}${e.is_primary ? ' <span class="primary-badge">Primary</span>' : ''}</div>
            <div class="me-office">${e.office}${e.district ? ` — District ${e.district}` : ''}</div>
            <div class="me-links">${donateHtml}${socials}</div>
            ${viewMap}
          </div>
        </div>
      </div>`;
    }
  }
  if (!html) html = '<div class="addr-none">No confirmed Democratic candidates found yet. Check back after May 19.</div>';

  document.getElementById('addr-modal-body').innerHTML = html;
  document.getElementById('addr-modal').classList.add('open');
}

function closeAddrModal() {
  document.getElementById('addr-modal').classList.remove('open');
}

document.getElementById('addr-modal').addEventListener('click', function(e) {
  if (e.target === this) closeAddrModal();
});

// ── Init ──────────────────────────────────────────────────────────────────────
selectTab('federal');
</script>
</body>
</html>"""

html = TEMPLATE.replace('__ENTRIES__', ENTRIES_JSON).replace('__GEOJSON__', GEO_JSON)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

size = os.path.getsize('index.html')
print(f'index.html written ({size:,} bytes / {size // 1024} KB)')
print(f'{len(ENTRIES)} total candidate entries across all tabs')
for tab in ['federal', 'senate', 'house', 'county', 'metro']:
    n = sum(1 for e in ENTRIES if e['tab'] == tab)
    imgs = sum(1 for e in ENTRIES if e['tab'] == tab and e['image'])
    print(f'  {tab}: {n} entries, {imgs} with photos')
