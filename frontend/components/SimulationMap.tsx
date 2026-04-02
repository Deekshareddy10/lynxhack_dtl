'use client';

import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

export interface TractImpact {
  tract_id: string;
  impact_score: number;
  agent_breakdown?: Record<string, number>;
}

interface SimulationMapProps {
  tractData: TractImpact[] | null;
}

function scoreToColor(score: number): string {
  if (score < 30) return '#22c55e';
  if (score < 60) return '#f59e0b';
  return '#ef4444';
}

export default function SimulationMap({ tractData }: SimulationMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const geojsonRef = useRef<any>(null);   // stores the raw GeoJSON we fetched
  const popup = useRef<mapboxgl.Popup | null>(null);
  const mapReady = useRef(false);

  // Called once the map style + source are loaded — applies current tractData
  function applyScores(data: TractImpact[]) {
    if (!map.current || !geojsonRef.current) return;
    const source = map.current.getSource('nyc-tracts') as mapboxgl.GeoJSONSource;
    if (!source) return;

    const scoreMap = new Map(data.map(t => [t.tract_id, t.impact_score]));

    const updated = {
      ...geojsonRef.current,
      features: geojsonRef.current.features.map((f: any) => ({
        ...f,
        properties: {
          ...f.properties,
          impact_score: scoreMap.get(f.properties.tract_id) ?? 0,
        },
      })),
    };

    // Keep a reference to the updated data so future calls have current scores
    geojsonRef.current = updated;
    source.setData(updated);
  }

  // Initialise map once
  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN!;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [-73.9712, 40.7831],
      zoom: 11,
      pitch: 45,
      bearing: -17.6,
      antialias: true,
    });

    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

    map.current.on('load', () => {
      if (!map.current) return;

      fetch('/nyc-tracts.geojson')
        .then(r => r.json())
        .then((geojson: any) => {
          if (!map.current) return;

          // Store GeoJSON so applyScores can reference it
          geojsonRef.current = geojson;

          map.current.addSource('nyc-tracts', {
            type: 'geojson',
            data: geojson,
          });

          map.current.addLayer({
            id: 'impact-zones',
            type: 'fill-extrusion',
            source: 'nyc-tracts',
            paint: {
              'fill-extrusion-color': [
                'interpolate', ['linear'],
                ['coalesce', ['get', 'impact_score'], 0],
                0,   '#22c55e',
                30,  '#84cc16',
                50,  '#f59e0b',
                70,  '#f97316',
                100, '#ef4444',
              ] as any,
              'fill-extrusion-height': [
                'interpolate', ['linear'],
                ['coalesce', ['get', 'impact_score'], 0],
                0, 20,
                100, 800,
              ],
              'fill-extrusion-base': 0,
              'fill-extrusion-opacity': 0.85,
            },
          });

          map.current.addLayer({
            id: 'tract-outlines',
            type: 'line',
            source: 'nyc-tracts',
            paint: {
              'line-color': '#475569',
              'line-width': 0.8,
              'line-opacity': 0.9,
            },
          });

          mapReady.current = true;

          // If tractData arrived before the map was ready, apply it now
          // We access it via a DOM dataset trick to avoid stale closure
          const pending = mapContainer.current?.dataset.pendingScores;
          if (pending) {
            applyScores(JSON.parse(pending));
            delete mapContainer.current!.dataset.pendingScores;
          }

          // Hover popup
          popup.current = new mapboxgl.Popup({ closeButton: false, closeOnClick: false });

          map.current.on('mousemove', 'impact-zones', (e) => {
            if (!map.current || !e.features?.length) return;
            map.current.getCanvas().style.cursor = 'pointer';
            const props = e.features[0].properties;
            const score = Math.round(props?.impact_score ?? 0);
            const tractId = props?.tract_id ?? '—';
            popup.current!
              .setLngLat(e.lngLat)
              .setHTML(`
                <div style="font-family:monospace;font-size:12px;color:#f1f5f9;padding:2px">
                  <div style="font-weight:bold;margin-bottom:4px">Tract ${tractId}</div>
                  <div>Impact: <span style="color:${scoreToColor(score)};font-weight:bold">${score}/100</span></div>
                </div>
              `)
              .addTo(map.current!);
          });

          map.current.on('mouseleave', 'impact-zones', () => {
            if (!map.current) return;
            map.current.getCanvas().style.cursor = '';
            popup.current?.remove();
          });
        });
    });

    return () => {
      map.current?.remove();
      map.current = null;
      mapReady.current = false;
    };
  }, []);

  // Apply new scores whenever tractData changes
  useEffect(() => {
    if (!tractData) return;

    if (mapReady.current) {
      applyScores(tractData);
    } else if (mapContainer.current) {
      // Map not ready yet — stash data to apply once GeoJSON loads
      mapContainer.current.dataset.pendingScores = JSON.stringify(tractData);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tractData]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full rounded-lg" />

      {/* Legend */}
      <div className="absolute bottom-8 left-4 bg-slate-900/90 border border-slate-700 rounded-lg p-3 text-xs text-slate-300">
        <div className="font-semibold mb-2 text-slate-100">Impact Level</div>
        <div className="flex items-center gap-2 mb-1">
          <div className="w-3 h-3 rounded-sm bg-green-500" />
          <span>Low Impact (0–30)</span>
        </div>
        <div className="flex items-center gap-2 mb-1">
          <div className="w-3 h-3 rounded-sm bg-amber-500" />
          <span>Moderate (30–60)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-sm bg-red-500" />
          <span>High Impact (60–100)</span>
        </div>
      </div>

      {!tractData && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="bg-slate-900/80 border border-slate-700 rounded-xl px-6 py-4 text-slate-400 text-sm text-center">
            <div className="text-2xl mb-2">🗺️</div>
            Run a simulation to see impact zones
          </div>
        </div>
      )}
    </div>
  );
}
