#!/usr/bin/env python3
"""Build index.html for the Jefferson County Democrats 2026 donation app."""

import json
import os

# ── Load source data ──────────────────────────────────────────────────────────

with open('candidates.json') as f:
    candidates_data = json.load(f)

with open('verified_links.json') as f:
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
    'metro_all':     load_geojson('data/metro_all.geojson'),  # all 26 MC districts, for address PIP only
}

# ── Build RACES list ──────────────────────────────────────────────────────────

def race_to_dict(race):
    race_id = race['id']
    level   = race['level']
    district = race.get('district')

    if level == 'federal':
        tab = 'federal'
        geo_layer = 'county' if race_id == 'us-senate-ky' else 'congress'
    elif level == 'state':
        tab = 'house' if 'house' in race_id else 'senate'
        geo_layer = 'house' if 'house' in race_id else 'senate'
    elif level == 'county':
        tab, geo_layer = 'county', 'county'
    else:  # metro
        tab = 'metro'
        geo_layer = 'county' if race_id == 'louisville-mayor' else 'metro_council'

    map_district = None if geo_layer == 'county' else district

    # Post-primary: general_election_candidate; nonpartisan: ldp_endorsed
    candidate = race.get('general_election_candidate') or race.get('ldp_endorsed')

    links = {}
    if candidate:
        links = verified_lookup.get(f'{race_id}::{candidate}', {})

    return {
        'id':           race_id,
        'office':       race['office'],
        'district':     district,
        'level':        level,
        'tab':          tab,
        'geo_layer':    geo_layer,
        'map_district': map_district,
        'candidate':    candidate,
        'links':        links,
    }


RACES = [race_to_dict(r) for r in candidates_data['races']]

# ── Inject into template and write ───────────────────────────────────────────

RACES_JSON  = json.dumps(RACES, indent=2)
GEO_JSON    = json.dumps(GEO)

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
      height: 100dvh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      background: #f5f7fa;
    }

    /* ── Header ── */
    header {
      background: #1565c0;
      color: #fff;
      padding: 10px 20px;
      flex-shrink: 0;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    header h1 { font-size: 1.05rem; font-weight: 700; letter-spacing: 0.01em; }

    /* ── Tabs ── */
    #tabs {
      display: flex;
      background: #fff;
      border-bottom: 2px solid #1565c0;
      flex-shrink: 0;
      overflow-x: auto;
    }
    .tab-btn {
      padding: 10px 20px;
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

    /* ── Main ── */
    #main { display: flex; flex: 1; overflow: hidden; }

    /* ── Sidebar ── */
    #sidebar {
      width: 260px;
      background: #fff;
      border-right: 1px solid #e0e0e0;
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
    }
    #sidebar-header {
      padding: 8px 14px;
      font-size: 0.72rem;
      font-weight: 700;
      color: #999;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      border-bottom: 1px solid #f0f0f0;
      flex-shrink: 0;
    }
    #candidate-list { flex: 1; overflow-y: auto; padding: 4px 0; }
    .race-item {
      padding: 8px 14px;
      cursor: pointer;
      border-left: 3px solid transparent;
      transition: background 0.1s;
    }
    .race-item:hover { background: #f0f4ff; }
    .race-item.selected { background: #e8f0fe; border-left-color: #1565c0; }
    .race-item .dist-badge {
      display: inline-block;
      font-size: 0.68rem;
      font-weight: 700;
      color: #1565c0;
      background: #e8f0fe;
      padding: 1px 6px;
      border-radius: 9px;
      margin-bottom: 2px;
    }
    .race-item .cname {
      font-size: 0.88rem;
      font-weight: 600;
      color: #1a1a1a;
      line-height: 1.3;
    }
    .race-item.tbd .cname { color: #bbb; font-style: italic; }
    .race-item .oname { font-size: 0.73rem; color: #888; margin-top: 1px; }

    /* ── Right panel ── */
    #right { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }

    /* ── Map ── */
    #map { flex: 1; z-index: 0; }

    /* ── Detail panel ── */
    #detail {
      flex-shrink: 0;
      border-top: 2px solid #1565c0;
      background: #fff;
      overflow-y: auto;
      max-height: 200px;
      transition: max-height 0.2s;
    }
    #detail.empty { max-height: 0; border-top-width: 0; }
    .detail-inner { padding: 14px 20px; }
    .d-name { font-size: 1.15rem; font-weight: 700; color: #1a1a1a; }
    .d-office { font-size: 0.82rem; color: #666; margin: 3px 0 12px; }
    .d-links { display: flex; flex-wrap: wrap; gap: 8px; }
    .lbtn {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 6px 14px;
      border-radius: 18px;
      font-size: 0.82rem;
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      transition: opacity 0.15s;
      white-space: nowrap;
    }
    .lbtn:hover { opacity: 0.82; }
    .lbtn.donate  { background: #1565c0; color: #fff; padding: 8px 20px; font-size: 0.88rem; }
    .lbtn.social  { background: #e8f0fe; color: #1565c0; }
    .no-links     { color: #aaa; font-size: 0.85rem; padding: 14px 20px; }

    /* ── Address search bar ── */
    #addr-bar {
      background: #e8f0fe;
      border-bottom: 1px solid #c5d8fc;
      padding: 8px 12px;
      flex-shrink: 0;
      display: flex;
      gap: 8px;
      align-items: center;
    }
    #addr-input {
      flex: 1;
      padding: 7px 12px;
      border: 1px solid #aac4f7;
      border-radius: 20px;
      font-size: 0.85rem;
      outline: none;
      background: #fff;
    }
    #addr-input:focus { border-color: #1565c0; box-shadow: 0 0 0 2px #c5d8fc; }
    #addr-btn {
      padding: 7px 16px;
      background: #1565c0;
      color: #fff;
      border: none;
      border-radius: 20px;
      font-size: 0.83rem;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      transition: background 0.15s;
    }
    #addr-btn:hover { background: #0d47a1; }
    #addr-btn:disabled { background: #90a4ae; cursor: default; }
    #addr-status { font-size: 0.78rem; color: #c62828; padding: 2px 4px; display: none; }

    /* ── Results modal ── */
    #addr-modal {
      display: none;
      position: fixed;
      inset: 0;
      z-index: 9999;
      background: rgba(0,0,0,0.45);
      overflow-y: auto;
      padding: 30px 16px;
    }
    #addr-modal.open { display: flex; justify-content: center; align-items: flex-start; }
    #modal-box {
      background: #fff;
      border-radius: 10px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.22);
      width: 100%;
      max-width: 580px;
      overflow: hidden;
    }
    #modal-head {
      background: #1565c0;
      color: #fff;
      padding: 16px 20px;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
    }
    #modal-head h2 { font-size: 1rem; font-weight: 700; margin-bottom: 3px; }
    #modal-matched { font-size: 0.78rem; opacity: 0.85; }
    #modal-close {
      background: none;
      border: none;
      color: #fff;
      font-size: 1.3rem;
      cursor: pointer;
      line-height: 1;
      padding: 0 4px;
      opacity: 0.8;
      flex-shrink: 0;
    }
    #modal-close:hover { opacity: 1; }
    #modal-body { padding: 12px 0; }
    .modal-section-head {
      font-size: 0.7rem;
      font-weight: 700;
      color: #888;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      padding: 8px 20px 4px;
    }
    .modal-race {
      padding: 10px 20px;
      border-bottom: 1px solid #f0f0f0;
      cursor: pointer;
      transition: background 0.1s;
    }
    .modal-race:last-child { border-bottom: none; }
    .modal-race:hover { background: #f5f8ff; }
    .mr-name { font-size: 0.95rem; font-weight: 700; color: #1a1a1a; }
    .mr-office { font-size: 0.78rem; color: #777; margin: 2px 0 8px; }
    .mr-links { display: flex; flex-wrap: wrap; gap: 6px; }
    .mr-lbtn {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 5px 12px;
      border-radius: 14px;
      font-size: 0.78rem;
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      transition: opacity 0.15s;
      white-space: nowrap;
    }
    .mr-lbtn:hover { opacity: 0.82; }
    .mr-lbtn.donate  { background: #1565c0; color: #fff; }
    .mr-lbtn.social  { background: #e8f0fe; color: #1565c0; }
    .mr-view { font-size: 0.75rem; color: #1565c0; text-decoration: underline; cursor: pointer; margin-top: 6px; display: inline-block; }
  </style>
</head>
<body>

<header>
  <h1>&#127455; Jefferson County Democrats &mdash; 2026</h1>
</header>

<div id="tabs">
  <button class="tab-btn" data-tab="federal">Federal</button>
  <button class="tab-btn" data-tab="senate">State Senate</button>
  <button class="tab-btn active" data-tab="house">State House</button>
  <button class="tab-btn" data-tab="county">County</button>
  <button class="tab-btn" data-tab="metro">Metro</button>
</div>

<div id="addr-bar">
  <input id="addr-input" type="text" placeholder="&#128269;  Enter your address to find your candidates&hellip;" autocomplete="street-address">
  <button id="addr-btn" onclick="lookupAddress()">Find</button>
  <span id="addr-status"></span>
</div>

<div id="addr-modal">
  <div id="modal-box">
    <div id="modal-head">
      <div>
        <h2>Your Candidates</h2>
        <div id="modal-matched"></div>
      </div>
      <button id="modal-close" onclick="closeModal()">&#x2715;</button>
    </div>
    <div id="modal-body"></div>
  </div>
</div>

<div id="main">
  <div id="sidebar">
    <div id="sidebar-header"></div>
    <div id="candidate-list"></div>
  </div>
  <div id="right">
    <div id="map"></div>
    <div id="detail" class="empty"></div>
  </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<script>
const RACES = __RACES__;
const GEO   = __GEOJSON__;

// ── Config ────────────────────────────────────────────────────────────────────
const TAB_LAYER = {
  federal: 'congress',
  senate:  'senate',
  house:   'house',
  county:  'county',
  metro:   'metro_council',
};

const LINK_META = [
  { key: 'actblue_url',         label: 'Donate on ActBlue',  icon: '💙', cls: 'donate'  },
  { key: 'campaign_deputy_url', label: 'Donate',             icon: '💵', cls: 'donate'  },
  { key: 'website_url',         label: 'Website',            icon: '🌐', cls: 'social'  },
  { key: 'facebook_url',        label: 'Facebook',           icon: '📘', cls: 'social'  },
  { key: 'twitter_url',         label: 'X / Twitter',        icon: '🐦', cls: 'social'  },
  { key: 'instagram_url',       label: 'Instagram',          icon: '📸', cls: 'social'  },
];

// ── State ─────────────────────────────────────────────────────────────────────
let currentTab     = 'house';
let selectedRaceId = null;

// ── Map ───────────────────────────────────────────────────────────────────────
const map = L.map('map', { zoomControl: true }).setView([38.18, -85.75], 11);
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>',
  maxZoom: 18,
}).addTo(map);

const ST_ACTIVE   = { color: '#1565c0', weight: 1.5, fillColor: '#90caf9', fillOpacity: 0.30 };
const ST_INACTIVE = { color: '#90a4ae', weight: 0.8, fillColor: '#cfd8dc', fillOpacity: 0.18 };
const ST_SELECTED = { color: '#0d47a1', weight: 3,   fillColor: '#1565c0', fillOpacity: 0.55 };
const ST_COUNTY   = { color: '#546e7a', weight: 1.5, fillColor: '#cfd8dc', fillOpacity: 0.20, dashArray: '5 4' };

const geoLayers   = {};
let   countyLayer = null;

function districtHasRace(geoKey, dist) {
  return RACES.some(r => r.geo_layer === geoKey && r.map_district === dist);
}

function buildDistrictLayer(key) {
  return L.geoJSON(GEO[key], {
    style(feature) {
      const dist = feature.properties && feature.properties.district;
      return districtHasRace(key, dist) ? ST_ACTIVE : ST_INACTIVE;
    },
    onEachFeature(feature, layer) {
      const dist = feature.properties && feature.properties.district;
      layer.on('click', () => {
        const race = RACES.find(r => r.tab === currentTab && r.map_district === dist && r.geo_layer === key);
        if (race) selectRace(race.id);
      });
    },
  });
}

function initMap() {
  countyLayer = L.geoJSON(GEO.county, { style: ST_COUNTY });
  for (const key of ['house', 'senate', 'congress', 'metro_council']) {
    geoLayers[key] = buildDistrictLayer(key);
  }
}

function renderMap() {
  if (countyLayer) countyLayer.remove();
  for (const ly of Object.values(geoLayers)) ly.remove();

  countyLayer.addTo(map);

  const layerKey = TAB_LAYER[currentTab];
  if (layerKey === 'county') {
    countyLayer.setStyle(ST_COUNTY);
    return;
  }

  const layer = geoLayers[layerKey];
  layer.addTo(map);

  const sel = selectedRaceId ? RACES.find(r => r.id === selectedRaceId) : null;

  layer.eachLayer(sub => {
    const dist = sub.feature.properties && sub.feature.properties.district;
    const isSelected = sel && sel.map_district === dist;
    sub.setStyle(isSelected ? ST_SELECTED : districtHasRace(layerKey, dist) ? ST_ACTIVE : ST_INACTIVE);
    if (isSelected) sub.bringToFront();
  });

  // Mayor or Senate race that covers county → highlight county boundary
  if (sel && sel.geo_layer === 'county') {
    countyLayer.setStyle({ ...ST_COUNTY, color: '#1565c0', weight: 3 });
  }
}

// ── Sidebar ───────────────────────────────────────────────────────────────────
function distLabel(race) {
  const { tab, district } = race;
  if (!district) return tab === 'metro' ? 'Mayor' : 'Statewide';
  if (tab === 'federal') return `CD-${district}`;
  if (tab === 'senate')  return `SD-${district}`;
  if (tab === 'house')   return `HD-${district}`;
  if (tab === 'metro')   return `MC-${district}`;
  if (tab === 'county')  return `D-${district}`;
  return `${district}`;
}

function renderSidebar() {
  const races = RACES
    .filter(r => r.tab === currentTab)
    .sort((a, b) => {
      if (a.district === null && b.district !== null) return -1;
      if (a.district !== null && b.district === null) return 1;
      if (a.district !== null && b.district !== null) return a.district - b.district;
      return a.office.localeCompare(b.office);
    });

  const ready = races.filter(r => r.candidate).length;
  document.getElementById('sidebar-header').textContent =
    `${ready} of ${races.length} candidates confirmed`;

  const list = document.getElementById('candidate-list');
  list.innerHTML = races.map(race => {
    const safeId = race.id.replace(/"/g, '&quot;');
    const badge  = distLabel(race);
    const active = race.id === selectedRaceId ? ' selected' : '';
    const tbd    = !race.candidate ? ' tbd' : '';
    return `<div class="race-item${active}${tbd}" data-id="${safeId}" onclick="selectRace(this.dataset.id)">
      <div class="dist-badge">${badge}</div>
      <div class="cname">${race.candidate || 'TBD — Primary Pending'}</div>
      <div class="oname">${race.office}</div>
    </div>`;
  }).join('');
}

// ── Detail ────────────────────────────────────────────────────────────────────
function renderDetail() {
  const panel = document.getElementById('detail');
  if (!selectedRaceId) { panel.className = 'empty'; return; }

  const race = RACES.find(r => r.id === selectedRaceId);
  if (!race) { panel.className = 'empty'; return; }

  panel.className = '';

  if (!race.candidate) {
    panel.innerHTML = `<div class="no-links">Primary winner TBD — check back after May 19, 2026.</div>`;
    return;
  }

  const distSuffix = race.district ? ` — District ${race.district}` : '';
  let linksHtml = LINK_META
    .filter(m => race.links[m.key])
    .map(m => `<a class="lbtn ${m.cls}" href="${race.links[m.key]}" target="_blank" rel="noopener">${m.icon} ${m.label}</a>`)
    .join('');
  if (!linksHtml) linksHtml = '<span class="no-links">No links on file yet.</span>';

  panel.innerHTML = `<div class="detail-inner">
    <div class="d-name">${race.candidate}</div>
    <div class="d-office">${race.office}${distSuffix}</div>
    <div class="d-links">${linksHtml}</div>
  </div>`;
}

// ── Actions ───────────────────────────────────────────────────────────────────
function selectTab(tab) {
  currentTab     = tab;
  selectedRaceId = null;
  document.querySelectorAll('.tab-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.tab === tab));
  renderSidebar();
  renderMap();
  renderDetail();
}

function selectRace(id) {
  selectedRaceId = id;
  renderSidebar();
  renderMap();
  renderDetail();

  // Scroll selected item into view
  const el = document.querySelector('.race-item.selected');
  if (el) el.scrollIntoView({ block: 'nearest' });
}

// ── Address lookup ────────────────────────────────────────────────────────────

const addrInput = document.getElementById('addr-input');
addrInput.addEventListener('keydown', e => { if (e.key === 'Enter') lookupAddress(); });

function setAddrStatus(msg, show = true) {
  const el = document.getElementById('addr-status');
  el.textContent = msg;
  el.style.display = show ? 'block' : 'none';
}

async function geocodeAddress(raw) {
  const query = /,\s*(KY|kentucky)/i.test(raw) ? raw : raw + ', Louisville, KY';

  // 1. U.S. Census Bureau geocoder
  try {
    const url = 'https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?' +
      'benchmark=Public_AR_Current&format=json&address=' + encodeURIComponent(query);
    const data = await fetch(url).then(r => r.json());
    const m = data.result?.addressMatches;
    if (m?.length) return { lon: m[0].coordinates.x, lat: m[0].coordinates.y, addr: m[0].matchedAddress };
  } catch {}

  // 2. ArcGIS fallback
  try {
    const url = 'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?' +
      'outFields=Match_addr&maxLocations=1&f=json&SingleLine=' + encodeURIComponent(query);
    const data = await fetch(url).then(r => r.json());
    const c = data.candidates?.[0];
    if (c?.score >= 80) return { lon: c.location.x, lat: c.location.y, addr: c.address };
  } catch {}

  return null;
}

// Ray-casting point-in-polygon
function pipRing(px, py, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    if ((yi > py) !== (yj > py) && px < ((xj - xi) * (py - yi)) / (yj - yi) + xi)
      inside = !inside;
  }
  return inside;
}

function pointInFeature(lon, lat, feature) {
  const g = feature.geometry;
  if (g.type === 'Polygon')      return pipRing(lon, lat, g.coordinates[0]);
  if (g.type === 'MultiPolygon') return g.coordinates.some(p => pipRing(lon, lat, p[0]));
  return false;
}

function findDistrict(lon, lat, geoKey) {
  for (const feat of GEO[geoKey].features)
    if (pointInFeature(lon, lat, feat)) return feat.properties.district;
  return null;
}

let addrMarker = null;

async function lookupAddress() {
  const raw = addrInput.value.trim();
  if (!raw) return;

  const btn = document.getElementById('addr-btn');
  btn.disabled = true;
  btn.textContent = '…';
  setAddrStatus('');

  const result = await geocodeAddress(raw);
  btn.disabled = false;
  btn.textContent = 'Find';

  if (!result) {
    setAddrStatus('Address not found. Try including your full street address and city.');
    return;
  }

  const { lon, lat, addr } = result;

  // Verify within Jefferson County
  const inCounty = GEO.county.features.some(f => pointInFeature(lon, lat, f));
  if (!inCounty) {
    setAddrStatus('That address appears to be outside Jefferson County.');
    return;
  }

  setAddrStatus('');

  // Drop a pin on the map
  if (addrMarker) addrMarker.remove();
  addrMarker = L.marker([lat, lon]).addTo(map).bindPopup(addr).openPopup();
  map.setView([lat, lon], 13);

  // Find districts
  const congDist   = findDistrict(lon, lat, 'congress');
  const senateDist = findDistrict(lon, lat, 'senate');
  const houseDist  = findDistrict(lon, lat, 'house');
  const metroDist  = findDistrict(lon, lat, 'metro_all');

  // Collect matching races (confirmed candidates only)
  const myRaces = RACES.filter(r => {
    if (!r.candidate) return false;
    if (r.tab === 'federal') return r.id === 'us-senate-ky' || r.map_district === congDist;
    if (r.tab === 'senate')  return r.map_district === senateDist;
    if (r.tab === 'house')   return r.map_district === houseDist;
    if (r.tab === 'county')  return true;
    if (r.tab === 'metro')   return r.id === 'louisville-mayor' || r.map_district === metroDist;
    return false;
  });

  showModal(addr, myRaces);
}

const SECTION_LABELS = { federal: 'Federal', senate: 'State Senate', house: 'State House', county: 'County', metro: 'Metro' };

function showModal(addr, races) {
  document.getElementById('modal-matched').textContent = addr;

  const grouped = {};
  for (const r of races) (grouped[r.tab] = grouped[r.tab] || []).push(r);

  const tabOrder = ['federal', 'senate', 'house', 'county', 'metro'];
  let html = '';
  for (const tab of tabOrder) {
    if (!grouped[tab]) continue;
    html += `<div class="modal-section-head">${SECTION_LABELS[tab]}</div>`;
    for (const race of grouped[tab]) {
      const distSuffix = race.district ? ` &mdash; District ${race.district}` : '';
      const links = LINK_META
        .filter(m => race.links[m.key])
        .map(m => `<a class="mr-lbtn ${m.cls}" href="${race.links[m.key]}" target="_blank" rel="noopener">${m.icon} ${m.label}</a>`)
        .join('');
      const safeId = race.id.replace(/"/g, '&quot;');
      html += `<div class="modal-race">
        <div class="mr-name">${race.candidate}</div>
        <div class="mr-office">${race.office}${distSuffix}</div>
        <div class="mr-links">${links || '<span style="color:#aaa;font-size:0.8rem">No links on file yet.</span>'}</div>
        <span class="mr-view" data-id="${safeId}" onclick="viewOnMap(this.dataset.id)">View on map &rarr;</span>
      </div>`;
    }
  }
  if (!html) html = '<div style="padding:20px;color:#aaa">No confirmed Democratic candidates found for this address yet. Check back after the May 19 primary.</div>';

  document.getElementById('modal-body').innerHTML = html;
  document.getElementById('addr-modal').classList.add('open');
}

function closeModal() {
  document.getElementById('addr-modal').classList.remove('open');
}

function viewOnMap(id) {
  closeModal();
  selectRace(id);
}

// Close modal on backdrop click
document.getElementById('addr-modal').addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});

// ── Init ──────────────────────────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn =>
  btn.addEventListener('click', () => selectTab(btn.dataset.tab)));

initMap();
selectTab('house');
</script>
</body>
</html>"""

html = TEMPLATE.replace('__RACES__', RACES_JSON).replace('__GEOJSON__', GEO_JSON)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

size = os.path.getsize('index.html')
print(f'index.html written — {size:,} bytes ({size / 1024:.0f} KB)')
