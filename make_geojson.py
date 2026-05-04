#!/usr/bin/env python3
"""Generate clipped GeoJSON district files for the Jefferson County Democrats app.

All legislative boundaries are derived by dissolving the authoritative 2026
Jefferson County precinct shapefile on each district field. Metro Council uses
its own shapefile since precincts don't carry that field.
"""

import geopandas as gpd
from shapely.geometry import MultiPolygon
import json
import os


def clean_geometry(gdf):
    """Remove interior holes and tiny polygon parts — both are precinct dissolve artifacts."""
    from shapely.geometry import Polygon, MultiPolygon

    def fill_holes(geom):
        if geom.geom_type == 'Polygon':
            return Polygon(geom.exterior)
        elif geom.geom_type == 'MultiPolygon':
            parts = [Polygon(p.exterior) for p in geom.geoms if p.area > 1e-8]
            if not parts:
                return geom
            return parts[0] if len(parts) == 1 else MultiPolygon(parts)
        return geom

    gdf = gdf.copy()
    gdf['geometry'] = gdf['geometry'].apply(fill_holes)
    return gdf

os.makedirs('data', exist_ok=True)

SHP = (
    'F:/robert_kahne/kentucky-political-data/shapefiles/'
    'louisville_precincts_2026/Jefferson_County_KY_Voting_Precincts_2026.shp'
)

print('Loading 2026 precincts...')
precincts = gpd.read_file(SHP).to_crs('EPSG:4326')


def save_dissolved(gdf, by_col, keep, out_path, simplify_tol=0.0001):
    """Dissolve gdf by by_col, keep only the listed district numbers, simplify, save."""
    dissolved = gdf.dissolve(by=by_col)[['geometry']].reset_index()
    dissolved.columns = ['district', 'geometry']
    dissolved['district'] = dissolved['district'].astype(int)
    filtered = dissolved[dissolved['district'].isin(keep)].copy()
    filtered = clean_geometry(filtered)
    if simplify_tol:
        filtered['geometry'] = filtered['geometry'].simplify(simplify_tol, preserve_topology=True)
    filtered.to_file(out_path, driver='GeoJSON')
    size = os.path.getsize(out_path)
    print(f'  {out_path}: {size:,} bytes ({len(filtered)} features)')


# County boundary
print('County boundary...')
county = clean_geometry(precincts.dissolve()[['geometry']])
county['geometry'] = county['geometry'].simplify(0.0001, preserve_topology=True)
county.to_file('data/county.geojson', driver='GeoJSON')
print(f'  data/county.geojson: {os.path.getsize("data/county.geojson"):,} bytes')

# KY House
print('House districts...')
HOUSE_DISTRICTS = [28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 40, 41, 42, 43, 44, 46, 48]
save_dissolved(precincts, 'LEGISDIST', HOUSE_DISTRICTS, 'data/house.geojson')

# KY Senate
print('Senate districts...')
SENATE_DISTRICTS = [6, 7, 10, 19, 26, 33, 35, 36, 37, 38]
save_dissolved(precincts, 'SENDIST', SENATE_DISTRICTS, 'data/senate.geojson')

# Congressional
print('Congressional districts...')
CONG_DISTRICTS = [2, 3]
save_dissolved(precincts, 'CONGDIST', CONG_DISTRICTS, 'data/congress.geojson')

# Metro Council — separate shapefile, filter to LDP-endorsed districts
print('Metro Council districts...')
metro = gpd.read_file(
    'F:/robert_kahne/kentucky-political-data/shapefiles/metro-council/'
    'Louisville_KY_Metro_Council_Districts.shp'
).to_crs('EPSG:4326')
METRO_DISTRICTS = [1, 3, 5, 7, 11, 15, 17, 21, 23]
mc = metro[metro['COUNDIST'].isin(METRO_DISTRICTS)].copy()
mc['district'] = mc['COUNDIST'].astype(int)
mc = clean_geometry(mc)
mc['geometry'] = mc['geometry'].simplify(0.0001, preserve_topology=True)
mc[['district', 'geometry']].to_file('data/metro_council.geojson', driver='GeoJSON')
print(f'  data/metro_council.geojson: {os.path.getsize("data/metro_council.geojson"):,} bytes ({len(mc)} features)')

# All 26 Metro Council districts — used for address lookup PIP only, not displayed
print('Metro Council all districts (address lookup)...')
mc_all = metro.copy()
mc_all['district'] = mc_all['COUNDIST'].astype(int)
mc_all = clean_geometry(mc_all)
mc_all['geometry'] = mc_all['geometry'].simplify(0.0001, preserve_topology=True)
mc_all[['district', 'geometry']].to_file('data/metro_all.geojson', driver='GeoJSON')
print(f'  data/metro_all.geojson: {os.path.getsize("data/metro_all.geojson"):,} bytes ({len(mc_all)} features)')

print('\nDone.')
