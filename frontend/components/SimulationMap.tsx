'use client';

import { useEffect, useRef, useCallback } from 'react';
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

// Map impact score 0-100 to a colour on green→yellow→red scale
function scoreToColor(score: number): string {
  if (score < 30) return '#22c55e';   // green
  if (score < 60) return '#f59e0b';   // amber
  return '#ef4444';                    // red
}

// Build a Mapbox expression that colours each tract by its impact_score property
function buildColorExpression() {
  return [
    'interpolate', ['linear'],
    ['coalesce', ['get', 'impact_score'], 0],
    0,   '#22c55e',
    30,  '#84cc16',
    50,  '#f59e0b',
    70,  '#f97316',
    100, '#ef4444',
  ];
}

export default function SimulationMap({ tractData }: SimulationMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const popup = useRef<mapboxgl.Popup | null>(null);

  // Merge simulation scores into the GeoJSON source
  const updateMapData = useCallback((data: TractImpact[]) => {
    if (!map.current || !map.current.isStyleLoaded()) return;

    const source = map.current.getSource('nyc-tracts') as mapboxgl.GeoJSONSource;
    if (!source) return;

    // Build a lookup map for fast access
    const scoreMap = new Map(data.map(t => [t.tract_id, t.impact_score]));

    // Update impact_score property on each feature
    const geojsonSource = source as any;
    const currentData = geojsonSource._data;
    if (!currentData || !currentData.features) return;

    const updated = {
      ...currentData,
      features: currentData.features.map((f: any) => ({
        ...f,
        properties: {
          ...f.properties,
          impact_score: scoreMap.get(f.properties.tract_id) ?? 0,
        },
      })),
    };

    source.setData(updated);
  }, []);

  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN!;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [-73.9712, 40.7831],   // Manhattan centre
      zoom: 11,
      pitch: 45,
      bearing: -17.6,
      antialias: true,
    });

    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

    map.current.on('load', () => {
      if (!map.current) return;

      // Load the NYC tract boundaries we saved to /public
      fetch('/nyc-tracts.geojson')
        .then(r => r.json())
        .then(geojson => {
          if (!map.current) return;

          map.current.addSource('nyc-tracts', {
            type: 'geojson',
            data: geojson,
          });

          // 3D extruded layer — height driven by impact_score
          map.current.addLayer({
            id: 'impact-zones',
            type: 'fill-extrusion',
            source: 'nyc-tracts',
            paint: {
              'fill-extrusion-color': buildColorExpression() as any,
              'fill-extrusion-height': [
                'interpolate', ['linear'],
                ['coalesce', ['get', 'impact_score'], 0],
                0, 10,
                100, 600,
              ],
              'fill-extrusion-base': 0,
              'fill-extrusion-opacity': 0.85,
            },
          });

          // Flat outline layer so tract boundaries are always visible
          map.current.addLayer({
            id: 'tract-outlines',
            type: 'line',
            source: 'nyc-tracts',
            paint: {
              'line-color': '#334155',
              'line-width': 0.5,
              'line-opacity': 0.8,
            },
          });
        });

      // Hover popup
      popup.current = new mapboxgl.Popup({
        closeButton: false,
        closeOnClick: false,
      });

      map.current.on('mousemove', 'impact-zones', (e) => {
        if (!map.current || !e.features?.length) return;
        map.current.getCanvas().style.cursor = 'pointer';

        const props = e.features[0].properties;
        const score = Math.round(props?.impact_score ?? 0);
        const tractId = props?.tract_id ?? 'Unknown';

        popup.current!
          .setLngLat(e.lngLat)
          .setHTML(`
            <div style="font-family:monospace;font-size:12px;color:#f1f5f9">
              <div style="font-weight:bold;margin-bottom:4px">Tract ${tractId}</div>
              <div>Impact Score: <span style="color:${scoreToColor(score)};font-weight:bold">${score}/100</span></div>
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

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Update colours whenever new simulation data arrives
  useEffect(() => {
    if (!tractData || !map.current) return;
    if (map.current.isStyleLoaded()) {
      updateMapData(tractData);
    } else {
      map.current.on('load', () => updateMapData(tractData));
    }
  }, [tractData, updateMapData]);

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

      {/* No-data overlay */}
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
