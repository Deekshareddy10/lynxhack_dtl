'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import AgentCard from '@/components/AgentCard';
import TimeSlider from '@/components/TimeSlider';
import type { SimulationResult, TractImpact } from '@/lib/api';

// Mapbox requires browser APIs — load it client-side only
const SimulationMap = dynamic(() => import('@/components/SimulationMap'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-slate-900 rounded-lg flex items-center justify-center text-slate-500 text-sm">
      Loading map...
    </div>
  ),
});

type Year = 1 | 5 | 10;

const VERDICT_COLORS: Record<string, string> = {
  'HIGH RISK':     'text-red-400',
  'MODERATE RISK': 'text-amber-400',
  'LOW RISK':      'text-green-400',
  'BENEFICIAL':    'text-emerald-400',
};

// Build per-tract data scaled for a given projection year
// Year multiplier makes impact look progressively worse/better over time
function getTractDataForYear(mapData: TractImpact[], year: Year): TractImpact[] {
  const multiplier = year === 1 ? 0.6 : year === 5 ? 0.85 : 1.0;
  return mapData.map(t => ({
    ...t,
    impact_score: Math.min(t.impact_score * multiplier, 100),
  }));
}

export default function SimulatePage() {
  const router = useRouter();
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [selectedYear, setSelectedYear] = useState<Year>(5);
  const [tractData, setTractData] = useState<TractImpact[] | null>(null);

  useEffect(() => {
    const raw = localStorage.getItem('urban_result');
    if (!raw) {
      router.push('/');
      return;
    }
    try {
      const parsed: SimulationResult = JSON.parse(raw);
      setResult(parsed);
      setTractData(getTractDataForYear(parsed.map_data, 5));
    } catch {
      router.push('/');
    }
  }, [router]);

  function handleYearChange(year: Year) {
    setSelectedYear(year);
    if (result) {
      setTractData(getTractDataForYear(result.map_data, year));
    }
  }

  if (!result) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        Loading simulation...
      </div>
    );
  }

  const verdictColor = VERDICT_COLORS[result.overall_verdict] ?? 'text-slate-300';

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {/* Top bar */}
      <header className="border-b border-slate-800 px-6 py-3 flex items-center gap-4">
        <span className="text-amber-400 font-black text-xl tracking-tighter">URBAN</span>
        <div className="flex-1 text-slate-300 text-sm truncate">
          <span className="text-slate-500 mr-2">Policy:</span>
          {result.policy_text.slice(0, 100)}{result.policy_text.length > 100 ? '...' : ''}
        </div>
        <div className={`font-bold text-sm ${verdictColor}`}>
          {result.overall_verdict} — {result.overall_risk_score.toFixed(0)}/100
        </div>
        <button
          onClick={() => router.push('/')}
          className="text-xs text-slate-500 hover:text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg transition-colors"
        >
          New Simulation
        </button>
      </header>

      {/* Main layout: left panel (40%) + right map (60%) */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Agent cards */}
        <div className="w-2/5 flex flex-col gap-3 p-4 overflow-y-auto border-r border-slate-800">
          <div className="text-xs text-slate-500 uppercase tracking-widest font-semibold px-1">
            Agent Analysis · {result.city}
          </div>
          {result.agents.map(agent => (
            <AgentCard key={agent.agent_name} verdict={agent} />
          ))}
        </div>

        {/* Right: Map + time slider */}
        <div className="flex-1 flex flex-col p-4 gap-4">
          <div className="flex-1 min-h-0">
            <SimulationMap tractData={tractData} />
          </div>
          <TimeSlider selectedYear={selectedYear} onYearChange={handleYearChange} />
        </div>
      </div>
    </div>
  );
}
