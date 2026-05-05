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
    }
    header h1 { font-size: 1.05rem; font-weight: 700; }

    /* ── Targeted races strip ── */
    #targeted-strip {
      background: #fff;
      border-bottom: 1px solid #e0e4ea;
      padding: 14px 20px;
      flex-shrink: 0;
    }
    #targeted-inner {
      max-width: 780px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      gap: 14px;
      flex-wrap: wrap;
    }
    #targeted-inner .t-label { flex: 1; min-width: 180px; }
    #targeted-inner .t-label strong {
      display: block;
      font-size: 0.93rem;
      font-weight: 700;
      color: #1a1a1a;
      margin-bottom: 2px;
    }
    #targeted-inner .t-label span { font-size: 0.76rem; color: #777; line-height: 1.4; }
    #targeted-btn {
      padding: 9px 20px;
      background: #1565c0;
      color: #fff;
      border: none;
      border-radius: 20px;
      font-size: 0.85rem;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
      transition: background 0.15s;
      flex-shrink: 0;
    }
    #targeted-btn:hover { background: #0d47a1; }

    /* ── Targeted races modal ── */
    #targeted-modal .modal-box {
      display: flex;
      flex-direction: column;
      max-height: 88vh;
      max-width: 500px;
    }
    #targeted-modal-body { flex: 1; overflow-y: auto; }
    .t-select-row {
      padding: 8px 20px 4px;
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .t-select-row span { font-size: 0.7rem; font-weight: 700; color: #999; text-transform: uppercase; letter-spacing: 0.06em; flex: 1; }
    .t-selall {
      font-size: 0.73rem;
      color: #1565c0;
      background: none;
      border: none;
      cursor: pointer;
      padding: 0;
      text-decoration: underline;
    }
    .t-selall:hover { color: #0d47a1; }
    .targeted-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 9px 20px;
      border-bottom: 1px solid #f2f2f2;
      cursor: pointer;
      transition: background 0.1s;
      user-select: none;
    }
    .targeted-item:hover { background: #f8f9ff; }
    .targeted-item:last-child { border-bottom: none; }
    .t-item-check { width: 17px; height: 17px; accent-color: #1565c0; flex-shrink: 0; cursor: pointer; }
    .t-item-photo {
      width: 42px; height: 42px; border-radius: 50%;
      background: #dce8fb; overflow: hidden; flex-shrink: 0;
      display: flex; align-items: center; justify-content: center;
    }
    .t-item-photo img { width: 100%; height: 100%; object-fit: cover; }
    .t-item-photo span { font-size: 1.3rem; color: #90b4e8; }
    .t-item-name { font-size: 0.88rem; font-weight: 700; color: #1a1a1a; }
    .t-item-office { font-size: 0.72rem; color: #777; margin-top: 1px; }
    #targeted-modal-footer {
      border-top: 1px solid #e8e8e8;
      padding: 12px 20px;
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
      flex-shrink: 0;
      background: #fff;
    }
    #targeted-footer-chips { display: flex; gap: 5px; align-items: center; flex-wrap: wrap; flex: 1; }
    #targeted-footer-btn {
      padding: 9px 18px;
      background: #1565c0;
      color: #fff;
      border: none;
      border-radius: 20px;
      font-size: 0.85rem;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
      transition: background 0.15s;
    }
    #targeted-footer-btn:hover { background: #0d47a1; }
    #targeted-footer-btn:disabled { opacity: 0.45; cursor: default; }

    /* ── Address hero ── */
    #addr-hero {
      background: #e8f0fe;
      border-bottom: 1px solid #c5d8f8;
      padding: 18px 20px;
      flex-shrink: 0;
    }
    #addr-hero-inner {
      max-width: 640px;
      margin: 0 auto;
      text-align: center;
    }
    #addr-label {
      display: block;
      font-size: 1.05rem;
      font-weight: 700;
      color: #1565c0;
      margin-bottom: 10px;
      letter-spacing: -0.01em;
    }
    #addr-row { display: flex; gap: 8px; justify-content: center; }
    #addr-input {
      flex: 1;
      max-width: 420px;
      padding: 10px 18px;
      border: 2px solid #90b4e8;
      border-radius: 24px;
      font-size: 0.9rem;
      outline: none;
      color: #1a1a1a;
      background: #fff;
      transition: border-color 0.15s;
    }
    #addr-input:focus { border-color: #1565c0; }
    #addr-btn {
      padding: 10px 22px;
      background: #1565c0;
      color: #fff;
      border: none;
      border-radius: 24px;
      font-size: 0.88rem;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
      transition: background 0.15s;
    }
    #addr-btn:hover { background: #0d47a1; }
    #addr-btn:disabled { opacity: 0.55; cursor: default; }
    #addr-err { font-size: 0.8rem; color: #c0392b; display: none; margin-top: 8px; }

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
      text-decoration: none;
      display: inline-flex;
      line-height: 0;
      transition: transform 0.12s, opacity 0.12s;
    }
    .social-btn:hover { transform: scale(1.15); opacity: 0.85; }

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

    /* ── Select mode (card grid) ── */
    #grid-controls {
      padding: 10px 20px 0;
      display: flex;
      justify-content: flex-end;
      max-width: 1440px;
      margin: 0 auto;
    }
    #select-toggle {
      padding: 6px 14px;
      background: none;
      border: 2px solid #1565c0;
      color: #1565c0;
      border-radius: 20px;
      font-size: 0.8rem;
      font-weight: 700;
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
      white-space: nowrap;
    }
    #select-toggle:hover { background: #e3eefb; }
    #select-toggle.active { background: #1565c0; color: #fff; }
    #select-toggle.active:hover { background: #0d47a1; }

    .ccard { position: relative; }
    .card-check-wrap {
      display: none;
      position: absolute;
      top: 10px; left: 10px;
    }
    .select-mode .card-check-wrap { display: block; }
    .card-check { width: 18px; height: 18px; cursor: pointer; accent-color: #1565c0; }
    .ccard.selected { box-shadow: 0 0 0 3px #1565c0, 0 2px 10px rgba(0,0,0,0.07); }

    /* ── Select bar (sticky bottom) ── */
    #select-bar {
      display: none;
      position: fixed;
      bottom: 0; left: 0; right: 0;
      background: #1565c0;
      color: #fff;
      padding: 12px 20px;
      z-index: 900;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      box-shadow: 0 -4px 20px rgba(0,0,0,0.22);
    }
    #select-bar.visible { display: flex; }
    #select-bar-label { font-size: 0.85rem; font-weight: 600; flex: 1; min-width: 120px; }
    .amt-chips { display: flex; gap: 5px; align-items: center; flex-wrap: wrap; }
    .amt-chip {
      padding: 5px 11px;
      background: rgba(255,255,255,0.15);
      border: 1px solid rgba(255,255,255,0.35);
      border-radius: 14px;
      color: #fff;
      font-size: 0.8rem;
      font-weight: 700;
      cursor: pointer;
      transition: background 0.12s;
    }
    .amt-chip:hover { background: rgba(255,255,255,0.25); }
    .amt-chip.active { background: rgba(255,255,255,0.35); border-color: rgba(255,255,255,0.7); }
    .amt-custom {
      width: 62px;
      padding: 5px 8px;
      border: 1px solid rgba(255,255,255,0.35);
      border-radius: 14px;
      background: rgba(255,255,255,0.15);
      color: #fff;
      font-size: 0.8rem;
      text-align: center;
      outline: none;
    }
    .amt-custom::placeholder { color: rgba(255,255,255,0.55); }
    .amt-custom:focus { background: rgba(255,255,255,0.25); border-color: rgba(255,255,255,0.6); }
    #select-donate-btn {
      padding: 8px 18px;
      background: #fff;
      color: #1565c0;
      border: none;
      border-radius: 20px;
      font-size: 0.85rem;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
      transition: background 0.12s;
    }
    #select-donate-btn:hover { background: #e3eefb; }
    #select-donate-btn:disabled { opacity: 0.5; cursor: default; }

    /* ── Address modal donate strip ── */
    #addr-donate-strip {
      background: #f0f4fa;
      border-bottom: 1px solid #dde8f8;
      padding: 14px 20px 12px;
    }
    #addr-donate-strip h3 {
      font-size: 0.78rem;
      font-weight: 700;
      color: #1565c0;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 10px;
    }
    #addr-donate-controls { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
    .addr-amt-chip {
      padding: 5px 12px;
      background: #fff;
      border: 2px solid #c5d8f8;
      border-radius: 14px;
      color: #1565c0;
      font-size: 0.82rem;
      font-weight: 700;
      cursor: pointer;
      transition: background 0.12s, border-color 0.12s;
    }
    .addr-amt-chip:hover { border-color: #1565c0; }
    .addr-amt-chip.active { background: #1565c0; color: #fff; border-color: #1565c0; }
    .addr-amt-custom {
      width: 68px;
      padding: 5px 8px;
      border: 2px solid #c5d8f8;
      border-radius: 14px;
      font-size: 0.82rem;
      text-align: center;
      outline: none;
      color: #1a1a1a;
    }
    .addr-amt-custom:focus { border-color: #1565c0; }
    #addr-donate-btn {
      padding: 7px 16px;
      background: #1565c0;
      color: #fff;
      border: none;
      border-radius: 18px;
      font-size: 0.85rem;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
      transition: background 0.15s;
      margin-left: auto;
    }
    #addr-donate-btn:hover { background: #0d47a1; }
    #addr-donate-btn:disabled { opacity: 0.45; cursor: default; }
    #addr-donate-count { font-size: 0.73rem; color: #777; margin-top: 7px; }
    .me-check { margin-right: 8px; accent-color: #1565c0; width: 16px; height: 16px; cursor: pointer; flex-shrink: 0; vertical-align: middle; }

    /* ── Donor info modal ── */
    #donor-modal .modal-box { max-width: 480px; }
    #donor-modal-body { padding: 20px 24px; overflow-y: auto; max-height: 72vh; }
    .dform-row { display: flex; gap: 10px; }
    .dform-field { display: flex; flex-direction: column; gap: 4px; margin-bottom: 13px; flex: 1; }
    .dform-field label { font-size: 0.71rem; font-weight: 700; color: #666; text-transform: uppercase; letter-spacing: 0.05em; }
    .dform-field input {
      padding: 8px 11px;
      border: 1.5px solid #dde4ef;
      border-radius: 8px;
      font-size: 0.88rem;
      outline: none;
      color: #1a1a1a;
      transition: border-color 0.15s;
      width: 100%;
    }
    .dform-field input:focus { border-color: #1565c0; }
    .dform-optional { margin-bottom: 12px; border: 1.5px solid #e8eef8; border-radius: 8px; padding: 0 12px; }
    .dform-optional summary {
      font-size: 0.8rem; font-weight: 600;
      color: #1565c0; cursor: pointer; padding: 10px 0; list-style: none;
    }
    .dform-optional summary::-webkit-details-marker { display: none; }
    .dform-optional summary::before { content: '+ '; }
    details[open].dform-optional summary::before { content: '− '; }
    .dform-optional-note { font-size: 0.71rem; color: #999; margin-top: -4px; margin-bottom: 10px; }
    .dform-optional-body { padding-bottom: 4px; }
    .dform-remember {
      display: flex; align-items: center; gap: 8px;
      font-size: 0.8rem; color: #555; margin-bottom: 16px; cursor: pointer;
    }
    .dform-remember input { accent-color: #1565c0; width: 16px; height: 16px; flex-shrink: 0; }
    .dform-actions { display: flex; gap: 10px; justify-content: flex-end; align-items: center; }
    .dform-skip {
      padding: 9px 14px; background: none; border: 1px solid #ddd;
      border-radius: 20px; font-size: 0.82rem; color: #888; cursor: pointer;
      transition: background 0.12s;
    }
    .dform-skip:hover { background: #f5f5f5; color: #555; }
    .dform-submit {
      padding: 9px 22px; background: #1565c0; color: #fff; border: none;
      border-radius: 20px; font-size: 0.85rem; font-weight: 700; cursor: pointer;
      transition: background 0.15s;
    }
    .dform-submit:hover { background: #0d47a1; }
    #step-donor-note {
      font-size: 0.74rem; color: #999; text-align: center;
      margin-bottom: 10px; display: flex; align-items: center; justify-content: center; gap: 6px;
    }
    #step-donor-edit {
      font-size: 0.74rem; color: #1565c0; background: none; border: none;
      cursor: pointer; text-decoration: underline; padding: 0;
    }
    .ldp-include-row {
      display: flex; align-items: center; gap: 8px;
      font-size: 0.8rem; color: #333; cursor: pointer;
      padding: 6px 0 2px;
    }
    .ldp-include-row input { accent-color: #1565c0; width: 15px; height: 15px; flex-shrink: 0; }
    .ldp-include-row strong { color: #1565c0; }

    /* ── Step-through donate modal ── */
    #step-modal {
      display: none;
      position: fixed; inset: 0;
      background: rgba(0,0,0,0.55);
      z-index: 9999;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    #step-modal.open { display: flex; }
    #step-box {
      background: #fff;
      border-radius: 14px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.25);
      width: 100%; max-width: 400px;
      padding: 28px 24px 22px;
      text-align: center;
      position: relative;
    }
    #step-close-btn {
      position: absolute; top: 12px; right: 14px;
      background: none; border: none; font-size: 1.2rem; cursor: pointer; color: #aaa;
    }
    #step-close-btn:hover { color: #555; }
    #step-progress {
      font-size: 0.72rem; color: #999; font-weight: 600;
      text-transform: uppercase; letter-spacing: 0.06em;
      margin-bottom: 16px;
    }
    #step-photo-wrap {
      width: 76px; height: 76px; border-radius: 50%;
      background: #dce8fb; overflow: hidden;
      margin: 0 auto 12px;
      display: flex; align-items: center; justify-content: center;
    }
    #step-photo-wrap img { width: 100%; height: 100%; object-fit: cover; }
    #step-photo-wrap span { font-size: 2rem; color: #90b4e8; }
    #step-name { font-size: 1rem; font-weight: 700; color: #1a1a1a; margin-bottom: 3px; }
    #step-office { font-size: 0.76rem; color: #777; margin-bottom: 16px; line-height: 1.35; }
    #step-note {
      font-size: 0.79rem;
      background: #f0f4fa;
      border-radius: 8px;
      padding: 9px 12px;
      color: #555;
      margin-bottom: 18px;
      line-height: 1.45;
      text-align: left;
    }
    #step-actions { display: flex; gap: 8px; justify-content: center; }
    #step-open-btn {
      padding: 10px 22px;
      background: #1565c0;
      color: #fff;
      border: none;
      border-radius: 22px;
      font-size: 0.88rem;
      font-weight: 700;
      cursor: pointer;
      transition: background 0.15s;
    }
    #step-open-btn:hover { background: #0d47a1; }
    #step-skip-btn {
      padding: 10px 14px;
      background: none;
      color: #999;
      border: 1px solid #ddd;
      border-radius: 22px;
      font-size: 0.82rem;
      cursor: pointer;
      transition: background 0.12s;
    }
    #step-skip-btn:hover { background: #f5f5f5; color: #555; }
  </style>
</head>
<body>

<header>
  <h1>&#127455; Jefferson County Democrats &mdash; 2026</h1>
</header>

<div id="targeted-strip">
  <div id="targeted-inner">
    <div class="t-label">
      <strong>&#127919; Give to our priority races</strong>
      <span>Competitive districts where every dollar counts most</span>
    </div>
    <button id="targeted-btn" onclick="openTargetedModal()">Choose &amp; donate &rarr;</button>
  </div>
</div>

<div id="tabs">
  <button class="tab-btn active" data-tab="federal">Federal</button>
  <button class="tab-btn" data-tab="senate">State Senate</button>
  <button class="tab-btn" data-tab="house">State House</button>
  <button class="tab-btn" data-tab="county">County</button>
  <button class="tab-btn" data-tab="metro">Metro</button>
</div>

<div id="addr-hero">
  <div id="addr-hero-inner">
    <label for="addr-input" id="addr-label">&#128205; Find YOUR candidates</label>
    <div id="addr-row">
      <input id="addr-input" type="text" placeholder="Enter your Louisville address&hellip;" autocomplete="street-address">
      <button id="addr-btn" onclick="lookupAddress()">Find My Candidates</button>
    </div>
    <span id="addr-err"></span>
  </div>
</div>

<div id="grid-controls">
  <button id="select-toggle" onclick="toggleSelectMode()">&#9745; Select candidates to donate</button>
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

<!-- Sticky select-to-donate bar -->
<div id="select-bar">
  <span id="select-bar-label"></span>
  <div class="amt-chips" id="grid-amt-chips">
    <span class="amt-chip active" onclick="setGridAmt(5,this)">$5</span>
    <span class="amt-chip" onclick="setGridAmt(10,this)">$10</span>
    <span class="amt-chip" onclick="setGridAmt(25,this)">$25</span>
    <span class="amt-chip" onclick="setGridAmt(50,this)">$50</span>
    <input class="amt-custom" id="grid-custom-amt" type="number" min="1" placeholder="Other"
      oninput="setGridAmt(parseFloat(this.value)||gridDonateAmt,null)">
  </div>
  <label style="display:flex;align-items:center;gap:6px;font-size:0.78rem;color:rgba(255,255,255,0.9);cursor:pointer;white-space:nowrap">
    <input type="checkbox" id="grid-ldp-check" checked style="accent-color:#fff;width:14px;height:14px">
    +&nbsp;Louisville&nbsp;Dems
  </label>
  <button id="select-donate-btn" onclick="startGridDonate()" disabled>Donate</button>
</div>

<!-- Donor info modal -->
<div class="modal-overlay" id="donor-modal">
  <div class="modal-box">
    <div class="modal-head">
      <div>
        <h2>Your information</h2>
        <p>Pre-fills on each donation page &mdash; enter once, reused every time</p>
      </div>
      <button class="modal-close" onclick="skipDonorModal()">&#x2715;</button>
    </div>
    <div id="donor-modal-body">
      <form id="donor-form" onsubmit="submitDonorForm(event)" novalidate>
        <div class="dform-row">
          <div class="dform-field">
            <label for="d-firstname">First name *</label>
            <input id="d-firstname" type="text" required autocomplete="given-name">
          </div>
          <div class="dform-field">
            <label for="d-lastname">Last name *</label>
            <input id="d-lastname" type="text" required autocomplete="family-name">
          </div>
        </div>
        <div class="dform-field">
          <label for="d-email">Email *</label>
          <input id="d-email" type="email" required autocomplete="email">
        </div>
        <div class="dform-field">
          <label for="d-addr1">Street address *</label>
          <input id="d-addr1" type="text" required autocomplete="street-address">
        </div>
        <div class="dform-row">
          <div class="dform-field" style="flex:2">
            <label for="d-city">City *</label>
            <input id="d-city" type="text" required autocomplete="address-level2">
          </div>
          <div class="dform-field" style="flex:1">
            <label for="d-state">State *</label>
            <input id="d-state" type="text" required maxlength="2" value="KY" autocomplete="address-level1">
          </div>
          <div class="dform-field" style="flex:1">
            <label for="d-zip">Zip *</label>
            <input id="d-zip" type="text" required maxlength="10" autocomplete="postal-code">
          </div>
        </div>
        <details class="dform-optional">
          <summary>Phone &amp; employment info</summary>
          <p class="dform-optional-note">Required by FEC for donations over $200</p>
          <div class="dform-optional-body">
            <div class="dform-field">
              <label for="d-phone">Phone</label>
              <input id="d-phone" type="tel" autocomplete="tel">
            </div>
            <div class="dform-row">
              <div class="dform-field">
                <label for="d-employer">Employer</label>
                <input id="d-employer" type="text" autocomplete="organization">
              </div>
              <div class="dform-field">
                <label for="d-occupation">Occupation</label>
                <input id="d-occupation" type="text">
              </div>
            </div>
          </div>
        </details>
        <label class="dform-remember">
          <input type="checkbox" id="d-remember" checked>
          Remember my info on this device
        </label>
        <div class="dform-actions">
          <button type="button" class="dform-skip" onclick="skipDonorModal()">Skip &mdash; don&rsquo;t pre-fill</button>
          <button type="submit" class="dform-submit">Save &amp; continue &rarr;</button>
        </div>
      </form>
    </div>
  </div>
</div>

<!-- Targeted races checklist modal -->
<div class="modal-overlay" id="targeted-modal">
  <div class="modal-box">
    <div class="modal-head">
      <div>
        <h2>&#127919; Priority Races</h2>
        <p>Uncheck any candidates you&rsquo;d like to skip</p>
      </div>
      <button class="modal-close" onclick="closeTargetedModal()">&#x2715;</button>
    </div>
    <div id="targeted-modal-body"></div>
    <div id="targeted-modal-footer">
      <div id="targeted-footer-chips">
        <span class="addr-amt-chip active" onclick="setTargetedModalAmt(5,this)">$5</span>
        <span class="addr-amt-chip" onclick="setTargetedModalAmt(10,this)">$10</span>
        <span class="addr-amt-chip" onclick="setTargetedModalAmt(25,this)">$25</span>
        <span class="addr-amt-chip" onclick="setTargetedModalAmt(50,this)">$50</span>
        <input class="addr-amt-custom" id="targeted-footer-custom" type="number" min="1" placeholder="Other"
          oninput="setTargetedModalAmt(parseFloat(this.value)||targetedModalAmt,null)">
      </div>
      <label class="ldp-include-row" style="width:100%">
        <input type="checkbox" id="targeted-ldp-check" checked>
        Also give to the <strong>Louisville Democratic Party</strong>
      </label>
      <button id="targeted-footer-btn" onclick="startTargetedFromModal()">Donate $5 to 20</button>
    </div>
  </div>
</div>

<!-- Step-through donate modal -->
<div id="step-modal">
  <div id="step-box">
    <button id="step-close-btn" onclick="closeStepModal()">&#x2715;</button>
    <div id="step-progress"></div>
    <div id="step-photo-wrap"></div>
    <div id="step-name"></div>
    <div id="step-office"></div>
    <div id="step-note"></div>
    <div id="step-donor-note"></div>
    <div id="step-actions">
      <button id="step-skip-btn" onclick="stepSkip()">Skip</button>
      <button id="step-open-btn" onclick="stepOpen()">Open &amp; next &rarr;</button>
    </div>
  </div>
</div>

<!-- gradient defs for Instagram icon (referenced by url(#ig-grad) in all instances) -->
<svg width="0" height="0" aria-hidden="true" style="position:absolute;overflow:hidden">
  <defs>
    <linearGradient id="ig-grad" x1="0" y1="1" x2="1" y2="0">
      <stop offset="0%"   stop-color="#F9CE34"/>
      <stop offset="30%"  stop-color="#EE2A7B"/>
      <stop offset="100%" stop-color="#6228D7"/>
    </linearGradient>
  </defs>
</svg>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<script>
const ENTRIES = __ENTRIES__;
const GEO     = __GEOJSON__;

const SOCIAL_ICONS = {
  website_url:   '<svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="12" fill="#546e7a"/><path fill="#fff" d="M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zm6.9 9h-2.8a15.6 15.6 0 0 0-1.9-7 8 8 0 0 1 4.7 7zM12 20a13.5 13.5 0 0 1-1.9-7h3.8A13.5 13.5 0 0 1 12 20zm-1.9-9A13.5 13.5 0 0 1 12 4a13.5 13.5 0 0 1 1.9 7h-3.8zM9.8 4a15.6 15.6 0 0 0-1.9 7H5.1A8 8 0 0 1 9.8 4zM5.1 13h2.8a15.6 15.6 0 0 0 1.9 7A8 8 0 0 1 5.1 13zm9.1 7a15.6 15.6 0 0 0 1.9-7h2.8a8 8 0 0 1-4.7 7z"/></svg>',
  facebook_url:  '<svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="12" fill="#1877F2"/><path fill="#fff" d="M13.5 22v-9h3l.44-3.5H13.5V7.44c0-.97.27-1.63 1.68-1.63H17V2.6A22.7 22.7 0 0 0 14.45 2.4c-2.57 0-4.33 1.57-4.33 4.45V9.5H7V13h3.12v9z"/></svg>',
  twitter_url:   '<svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="12" fill="#000"/><path fill="#fff" d="m13.96 10.5 4.77-5.5h-1.13L13.38 9.8 10.28 5H6.5l5.02 7.09L6.5 17.9h1.13l4.39-5.1L15.2 19H19zm-1.55 1.8-.52-.74-4.1-5.86h1.76l3.3 4.7.5.73 4.3 5.99H15.9z"/></svg>',
  instagram_url: '<svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true"><rect width="24" height="24" rx="6" fill="url(#ig-grad)"/><rect x="6.5" y="6.5" width="11" height="11" rx="3.2" stroke="#fff" stroke-width="1.5" fill="none"/><circle cx="12" cy="12" r="2.8" stroke="#fff" stroke-width="1.5" fill="none"/><circle cx="16.2" cy="7.8" r="1" fill="#fff"/></svg>',
};
const SOCIAL_LABELS = { website_url: 'Website', facebook_url: 'Facebook', twitter_url: 'X / Twitter', instagram_url: 'Instagram' };

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
  const donateCls = e.links.campaign_deputy_url && !e.links.actblue_url ? ' cd' : '';
  const donateHtml = donateUrl
    ? `<a class="btn-donate${donateCls}" href="${donateUrl}" target="_blank" rel="noopener">Donate</a>`
    : '';

  const socials = Object.keys(SOCIAL_ICONS)
    .filter(k => e.links[k])
    .map(k => `<a class="social-btn" href="${e.links[k]}" target="_blank" rel="noopener" title="${SOCIAL_LABELS[k]}">${SOCIAL_ICONS[k]}</a>`)
    .join('');

  const safeId = e.id.replace(/"/g, '&quot;');
  const viewMap = e.geo_layer !== 'county'
    ? `<span class="view-map-link" data-id="${safeId}" onclick="openMapModal(this.dataset.id)">View district &rarr;</span>`
    : '';
  const hasDonate = !!(e.links.actblue_url || e.links.campaign_deputy_url);
  const checkHtml = hasDonate
    ? `<div class="card-check-wrap"><input class="card-check" type="checkbox" data-id="${safeId}"
        ${selectedIds.has(e.id) ? 'checked' : ''}
        onchange="toggleCardSelect(this.dataset.id,this.checked)" aria-label="Select ${e.candidate}"></div>`
    : '';

  return `<div class="ccard${e.is_primary ? ' is-primary' : ''}${selectedIds.has(e.id) ? ' selected' : ''}" data-id="${safeId}">
    ${checkHtml}
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
  addrModalEntries = entries;
  addrDonateAmt = 5;

  const grouped = {};
  for (const e of entries) (grouped[e.tab] = grouped[e.tab] || []).push(e);

  const donatableCount = entries.filter(e => e.links.actblue_url || e.links.campaign_deputy_url).length;

  // Donate strip (only if any candidate has a donation link)
  let strip = '';
  if (donatableCount > 0) {
    strip = `<div id="addr-donate-strip">
      <h3>Donate to your candidates</h3>
      <div id="addr-donate-controls">
        <span class="addr-amt-chip active" onclick="setAddrAmt(5,this)">$5</span>
        <span class="addr-amt-chip" onclick="setAddrAmt(10,this)">$10</span>
        <span class="addr-amt-chip" onclick="setAddrAmt(25,this)">$25</span>
        <span class="addr-amt-chip" onclick="setAddrAmt(50,this)">$50</span>
        <input class="addr-amt-custom" id="addr-custom-amt" type="number" min="1" placeholder="Other"
          oninput="setAddrAmt(parseFloat(this.value)||addrDonateAmt,null)">
        <button id="addr-donate-btn" onclick="startAddrDonate()">Donate $5 to ${donatableCount}</button>
      </div>
      <label class="ldp-include-row">
        <input type="checkbox" id="addr-ldp-check" checked>
        Also give to the <strong>Louisville Democratic Party</strong>
      </label>
      <div id="addr-donate-count">${donatableCount} candidate${donatableCount !== 1 ? 's' : ''} with donation links — uncheck any you&rsquo;d like to skip</div>
    </div>`;
  }

  let html = strip;
  for (const tab of ['federal', 'senate', 'house', 'county', 'metro']) {
    if (!grouped[tab]) continue;
    html += `<div class="modal-section-head">${TAB_LABELS[tab]}</div>`;
    for (const e of grouped[tab]) {
      const imgHtml = e.image
        ? `<img class="me-photo" src="${e.image}" alt="${e.candidate}">`
        : `<span class="me-placeholder">&#128100;</span>`;
      const hasDonate = !!(e.links.actblue_url || e.links.campaign_deputy_url);
      const donateUrl = e.links.actblue_url || e.links.campaign_deputy_url;
      const donateCls = e.links.campaign_deputy_url && !e.links.actblue_url ? ' cd' : '';
      const donateHtml = donateUrl
        ? `<a class="me-donate${donateCls}" href="${donateUrl}" target="_blank" rel="noopener">Donate</a>` : '';
      const socials = Object.keys(SOCIAL_ICONS)
        .filter(k => e.links[k])
        .map(k => `<a class="me-social" href="${e.links[k]}" target="_blank" rel="noopener" title="${SOCIAL_LABELS[k]}">${SOCIAL_ICONS[k]}</a>`)
        .join('');
      const safeId = e.id.replace(/"/g, '&quot;');
      const viewMap = e.geo_layer !== 'county'
        ? `<span class="me-view" data-id="${safeId}" onclick="closeAddrModal();openMapModal(this.dataset.id)">View district &rarr;</span>` : '';
      const checkHtml = hasDonate
        ? `<input class="me-check" type="checkbox" data-id="${safeId}" checked onchange="updateAddrDonateBtn()" aria-label="Include ${e.candidate}">` : '';
      html += `<div class="modal-entry">
        <div class="me-row">
          ${checkHtml}
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

// ── Louisville Democratic Party entry ────────────────────────────────────────
const LDP_ENTRY = {
  id: 'ldp::louisville-democrats',
  race_id: 'ldp',
  office: 'Louisville Democratic Party',
  district: null,
  level: 'metro',
  tab: 'metro',
  geo_layer: 'county',
  map_district: null,
  candidate: 'Louisville Democratic Party',
  is_primary: false,
  image: null,
  links: { actblue_url: 'https://secure.actblue.com/donate/louisvilledemocrats' },
};

// ── Targeted races donate ─────────────────────────────────────────────────────
const TARGETED_RACE_IDS = new Set([
  'us-senate-ky',
  'ky-senate-06', 'ky-senate-36',
  'ky-house-28', 'ky-house-29', 'ky-house-31', 'ky-house-33',
  'ky-house-36', 'ky-house-38', 'ky-house-48',
  'louisville-mayor',
  'metro-council-03', 'metro-council-05', 'metro-council-07',
  'metro-council-11', 'metro-council-17', 'metro-council-21',
  'metro-council-23',
]);

// Priority order — first 10 highlighted, rest appended
const TARGETED_RACE_ORDER = [
  'metro-council-11',
  'ky-house-31',
  'ky-house-48',
  'ky-senate-36',
  'ky-senate-06',
  'ky-house-29',
  'ky-house-33',
  'metro-council-17',
  'metro-council-21',
  'metro-council-07',
  // rest
  'ky-house-28',
  'ky-house-36',
  'ky-house-38',
  'louisville-mayor',
  'metro-council-03',
  'metro-council-05',
  'metro-council-23',
  'us-senate-ky',
];

function getTargetedEntries() {
  return ENTRIES
    .filter(e => TARGETED_RACE_IDS.has(e.race_id) && (e.links.actblue_url || e.links.campaign_deputy_url))
    .sort((a, b) => {
      const ai = TARGETED_RACE_ORDER.indexOf(a.race_id);
      const bi = TARGETED_RACE_ORDER.indexOf(b.race_id);
      if (ai !== bi) return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
      return a.candidate.localeCompare(b.candidate);
    });
}

let targetedModalAmt = 5;

function openTargetedModal() {
  targetedModalAmt = 5;
  // Reset chips
  document.querySelectorAll('#targeted-footer-chips .addr-amt-chip').forEach((c,i) => c.classList.toggle('active', i===0));
  document.getElementById('targeted-footer-custom').value = '';

  const entries = getTargetedEntries();
  let html = `<div class="t-select-row">
    <span>Candidates (${entries.length})</span>
    <button class="t-selall" onclick="targetedSelectAll(true)">Select all</button>
    <button class="t-selall" onclick="targetedSelectAll(false)">Deselect all</button>
  </div>`;
  for (const e of entries) {
    const safeId = e.id.replace(/"/g, '&quot;');
    const photoHtml = e.image
      ? `<img src="${e.image}" alt="${e.candidate}">`
      : `<span>&#128100;</span>`;
    html += `<label class="targeted-item">
      <input type="checkbox" class="t-item-check" data-id="${safeId}" checked onchange="updateTargetedCount()">
      <div class="t-item-photo">${photoHtml}</div>
      <div>
        <div class="t-item-name">${e.candidate}${e.is_primary ? ' <span class="primary-badge">Primary</span>' : ''}</div>
        <div class="t-item-office">${e.office} &mdash; ${distLabel(e)}</div>
      </div>
    </label>`;
  }
  document.getElementById('targeted-modal-body').innerHTML = html;
  updateTargetedCount();
  document.getElementById('targeted-modal').classList.add('open');
}

function closeTargetedModal() {
  document.getElementById('targeted-modal').classList.remove('open');
}

document.getElementById('targeted-modal').addEventListener('click', function(e) {
  if (e.target === this) closeTargetedModal();
});

function setTargetedModalAmt(amt, el) {
  targetedModalAmt = amt;
  document.querySelectorAll('#targeted-footer-chips .addr-amt-chip').forEach(c => c.classList.remove('active'));
  if (el) el.classList.add('active');
  updateTargetedCount();
}

function updateTargetedCount() {
  const n = document.querySelectorAll('#targeted-modal-body .t-item-check:checked').length;
  const btn = document.getElementById('targeted-footer-btn');
  btn.textContent = `Donate $${targetedModalAmt} to ${n}`;
  btn.disabled = n === 0;
}

function targetedSelectAll(checked) {
  document.querySelectorAll('#targeted-modal-body .t-item-check').forEach(cb => cb.checked = checked);
  updateTargetedCount();
}

function startTargetedFromModal() {
  const customVal = parseFloat(document.getElementById('targeted-footer-custom').value);
  const amt = isNaN(customVal) ? targetedModalAmt : customVal;
  const checkedIds = [...document.querySelectorAll('#targeted-modal-body .t-item-check:checked')]
    .map(cb => cb.dataset.id);
  const allTargeted = getTargetedEntries();
  const entries = checkedIds.map(id => allTargeted.find(e => e.id === id)).filter(Boolean);
  if (document.getElementById('targeted-ldp-check')?.checked) entries.push(LDP_ENTRY);
  closeTargetedModal();
  startDonateQueue(entries, amt);
}

// ── Select mode (card grid) ──────────────────────────────────────────────────
let selectedIds = new Set();
let selectModeActive = false;
let gridDonateAmt = 5;

function toggleSelectMode() {
  selectModeActive = !selectModeActive;
  selectedIds.clear();
  const toggle = document.getElementById('select-toggle');
  toggle.classList.toggle('active', selectModeActive);
  toggle.textContent = selectModeActive ? '✕ Cancel selection' : '☑ Select candidates to donate';
  document.getElementById('grid-wrap').classList.toggle('select-mode', selectModeActive);
  updateSelectBar();
  renderCards();
}

function toggleCardSelect(id, checked) {
  if (checked) selectedIds.add(id);
  else selectedIds.delete(id);
  const card = document.querySelector(`.ccard[data-id="${CSS.escape(id)}"]`);
  if (card) card.classList.toggle('selected', checked);
  updateSelectBar();
}

function setGridAmt(amt, el) {
  gridDonateAmt = amt;
  document.querySelectorAll('#grid-amt-chips .amt-chip').forEach(c => c.classList.remove('active'));
  if (el) el.classList.add('active');
  if (!el) document.getElementById('grid-custom-amt').focus();
  updateSelectBar();
}

function updateSelectBar() {
  const bar = document.getElementById('select-bar');
  const donatable = [...selectedIds].filter(id => {
    const e = ENTRIES.find(x => x.id === id);
    return e && (e.links.actblue_url || e.links.campaign_deputy_url);
  });
  const count = selectedIds.size;
  if (!selectModeActive || count === 0) { bar.classList.remove('visible'); return; }
  bar.classList.add('visible');
  const noDonate = count - donatable.length;
  document.getElementById('select-bar-label').textContent =
    `${count} selected` + (noDonate ? ` (${noDonate} without donation link)` : '');
  const btn = document.getElementById('select-donate-btn');
  btn.textContent = `Donate $${gridDonateAmt} to ${donatable.length}`;
  btn.disabled = donatable.length === 0;
}

function startGridDonate() {
  const customVal = parseFloat(document.getElementById('grid-custom-amt').value);
  const amt = isNaN(customVal) ? gridDonateAmt : customVal;
  const entries = [...selectedIds]
    .map(id => ENTRIES.find(e => e.id === id))
    .filter(e => e && (e.links.actblue_url || e.links.campaign_deputy_url));
  if (document.getElementById('grid-ldp-check')?.checked) entries.push(LDP_ENTRY);
  startDonateQueue(entries, amt);
}

// ── Address modal donate ──────────────────────────────────────────────────────
let addrModalEntries = [];
let addrDonateAmt = 5;

function setAddrAmt(amt, el) {
  addrDonateAmt = amt;
  document.querySelectorAll('#addr-donate-strip .addr-amt-chip').forEach(c => c.classList.remove('active'));
  if (el) el.classList.add('active');
  updateAddrDonateBtn();
}

function updateAddrDonateBtn() {
  const checked = document.querySelectorAll('#addr-modal-body .me-check:checked');
  const n = checked.length;
  const btn = document.getElementById('addr-donate-btn');
  if (!btn) return;
  btn.textContent = `Donate $${addrDonateAmt} to ${n}`;
  btn.disabled = n === 0;
}

function startAddrDonate() {
  const customVal = parseFloat(document.getElementById('addr-custom-amt').value);
  const amt = isNaN(customVal) ? addrDonateAmt : customVal;
  const checkedIds = [...document.querySelectorAll('#addr-modal-body .me-check:checked')]
    .map(cb => cb.dataset.id);
  const entries = checkedIds
    .map(id => addrModalEntries.find(e => e.id === id))
    .filter(e => e && (e.links.actblue_url || e.links.campaign_deputy_url));
  if (document.getElementById('addr-ldp-check')?.checked) entries.push(LDP_ENTRY);
  closeAddrModal();
  startDonateQueue(entries, amt);
}

// ── Donor info ────────────────────────────────────────────────────────────────
const DONOR_FIELDS = ['firstname','lastname','email','addr1','city','state','zip','phone','employer','occupation'];
const DONOR_KEY = 'jcdems_donor_v1';
let savedDonor = null;
let pendingQueue = null;  // { entries, amount } waiting while donor modal is open

(function loadDonorInfo() {
  try { const r = localStorage.getItem(DONOR_KEY); if (r) savedDonor = JSON.parse(r); } catch {}
})();

function openDonorModal(entries, amount) {
  pendingQueue = { entries, amount };
  if (savedDonor) {
    DONOR_FIELDS.forEach(k => {
      const el = document.getElementById('d-' + k);
      if (el) el.value = savedDonor[k] || '';
    });
  }
  document.getElementById('donor-modal').classList.add('open');
}

function closeDonorModal() {
  document.getElementById('donor-modal').classList.remove('open');
}

function submitDonorForm(ev) {
  ev.preventDefault();
  const donor = {};
  DONOR_FIELDS.forEach(k => {
    const el = document.getElementById('d-' + k);
    if (el && el.value.trim()) donor[k] = el.value.trim();
  });
  if (!donor.firstname || !donor.lastname || !donor.email || !donor.addr1 || !donor.city || !donor.state || !donor.zip) {
    alert('Please fill in all required fields (marked with *).');
    return;
  }
  if (document.getElementById('d-remember').checked) {
    try { localStorage.setItem(DONOR_KEY, JSON.stringify(donor)); } catch {}
    savedDonor = donor;
  } else {
    try { localStorage.removeItem(DONOR_KEY); } catch {}
    savedDonor = null;
  }
  closeDonorModal();
  if (pendingQueue) {
    launchDonateQueue(pendingQueue.entries, pendingQueue.amount, donor);
    pendingQueue = null;
  }
}

function skipDonorModal() {
  closeDonorModal();
  if (pendingQueue) {
    launchDonateQueue(pendingQueue.entries, pendingQueue.amount, null);
    pendingQueue = null;
  }
}

document.getElementById('donor-modal').addEventListener('click', function(e) {
  if (e.target === this) skipDonorModal();
});

// ── Step-through donate queue ─────────────────────────────────────────────────
let donateQueue = [];
let donateQueueIdx = 0;
let currentDonor = null;

function buildDonateUrl(e, amount, donor) {
  const base = e.links.actblue_url || e.links.campaign_deputy_url;
  if (!base) return null;
  const params = new URLSearchParams({ amount });
  if (donor) {
    DONOR_FIELDS.forEach(k => { if (donor[k]) params.set(k, donor[k]); });
  }
  const sep = base.includes('?') ? '&' : '?';
  return base + sep + params.toString();
}

function startDonateQueue(entries, amount) {
  openDonorModal(entries, amount);
}

function launchDonateQueue(entries, amount, donor) {
  currentDonor = donor;
  donateQueue = entries.map(e => ({ e, url: buildDonateUrl(e, amount, donor), amount }));
  donateQueueIdx = 0;
  if (!donateQueue.length) return;
  document.getElementById('step-modal').classList.add('open');
  renderStepEntry();
}

function renderStepEntry() {
  const { e, amount } = donateQueue[donateQueueIdx];
  const total = donateQueue.length;
  const idx = donateQueueIdx;

  document.getElementById('step-progress').textContent = `${idx + 1} of ${total}`;
  document.getElementById('step-name').textContent = e.candidate;
  document.getElementById('step-office').textContent =
    e.office + (e.district ? ` — District ${e.district}` : '');

  const wrap = document.getElementById('step-photo-wrap');
  wrap.innerHTML = e.image
    ? `<img src="${e.image}" alt="${e.candidate}">`
    : `<span>&#128100;</span>`;

  const platform = e.links.actblue_url ? 'ActBlue' : 'Campaign Deputy';
  const donorNote = currentDonor
    ? `Form pre-filled as <strong>${currentDonor.firstname} ${currentDonor.lastname}</strong>.`
    : `Forms will <em>not</em> be pre-filled.`;
  document.getElementById('step-note').innerHTML =
    `<strong>$${amount}</strong> will be pre-filled on ${platform}. ${donorNote} Complete your donation in the new tab, then come back here.`;

  document.getElementById('step-donor-note').innerHTML = currentDonor
    ? `Donating as ${currentDonor.firstname} ${currentDonor.lastname} &mdash; <button id="step-donor-edit" onclick="editDonorFromStep()">edit info</button>`
    : `<button id="step-donor-edit" onclick="editDonorFromStep()">+ Add your info to pre-fill forms</button>`;

  const isLast = idx === total - 1;
  document.getElementById('step-open-btn').textContent = isLast ? 'Open → finish' : 'Open → next';
  document.getElementById('step-skip-btn').style.display = total > 1 ? '' : 'none';
}

function editDonorFromStep() {
  document.getElementById('step-modal').classList.remove('open');
  const remaining = donateQueue.slice(donateQueueIdx);
  const amount = remaining[0]?.amount;
  pendingQueue = { entries: remaining.map(item => item.e), amount };
  if (savedDonor) {
    DONOR_FIELDS.forEach(k => {
      const el = document.getElementById('d-' + k);
      if (el) el.value = savedDonor[k] || '';
    });
  }
  document.getElementById('donor-modal').classList.add('open');
}

function stepOpen() {
  window.open(donateQueue[donateQueueIdx].url, '_blank', 'noopener');
  donateQueueIdx++;
  if (donateQueueIdx >= donateQueue.length) closeStepModal();
  else renderStepEntry();
}

function stepSkip() {
  donateQueueIdx++;
  if (donateQueueIdx >= donateQueue.length) closeStepModal();
  else renderStepEntry();
}

function closeStepModal() {
  document.getElementById('step-modal').classList.remove('open');
  donateQueue = [];
  donateQueueIdx = 0;
}

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
