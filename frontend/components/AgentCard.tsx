'use client';

import { useState } from 'react';
import type { AgentVerdict } from '@/lib/api';

interface AgentCardProps {
  verdict: AgentVerdict;
}

const AGENT_META: Record<string, { icon: string; color: string }> = {
  'Economist':      { icon: '📊', color: 'blue'   },
  'Urban Planner':  { icon: '🏙️', color: 'purple' },
  'Equity Analyst': { icon: '⚖️', color: 'orange' },
};

const VERDICT_STYLES: Record<string, string> = {
  'HIGH RISK':      'bg-red-500/20 text-red-400 border-red-500/40',
  'MODERATE RISK':  'bg-amber-500/20 text-amber-400 border-amber-500/40',
  'LOW RISK':       'bg-green-500/20 text-green-400 border-green-500/40',
  'BENEFICIAL':     'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
};

type ProjectionYear = '1yr' | '5yr' | '10yr';

export default function AgentCard({ verdict }: AgentCardProps) {
  const [activeYear, setActiveYear] = useState<ProjectionYear>('1yr');
  const meta = AGENT_META[verdict.agent_name] ?? { icon: '🤖', color: 'slate' };
  const verdictStyle = VERDICT_STYLES[verdict.verdict] ?? VERDICT_STYLES['MODERATE RISK'];
  const confidencePct = Math.round(verdict.confidence * 100);

  const projections: Record<ProjectionYear, string> = {
    '1yr':  verdict.projection_1yr,
    '5yr':  verdict.projection_5yr,
    '10yr': verdict.projection_10yr,
  };

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-4 flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl">{meta.icon}</span>
          <span className="font-semibold text-slate-100">{verdict.agent_name}</span>
        </div>
        <span className={`text-xs font-bold px-2 py-1 rounded border ${verdictStyle}`}>
          {verdict.verdict}
        </span>
      </div>

      {/* Impact score + confidence */}
      <div className="flex items-center gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-slate-100">{Math.round(verdict.impact_score)}</div>
          <div className="text-xs text-slate-500">Impact /100</div>
        </div>
        <div className="flex-1">
          <div className="flex justify-between text-xs text-slate-400 mb-1">
            <span>Confidence</span>
            <span>{confidencePct}%</span>
          </div>
          <div className="h-1.5 bg-slate-700 rounded-full">
            <div
              className="h-1.5 bg-amber-500 rounded-full transition-all"
              style={{ width: `${confidencePct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Risks + Benefits */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className="text-xs font-semibold text-red-400 mb-1.5 uppercase tracking-wide">Risks</div>
          <ul className="space-y-1">
            {verdict.key_risks.slice(0, 3).map((r: string, i: number) => (
              <li key={i} className="text-xs text-slate-300 flex gap-1.5">
                <span className="text-red-400 mt-0.5 shrink-0">▸</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <div className="text-xs font-semibold text-green-400 mb-1.5 uppercase tracking-wide">Benefits</div>
          <ul className="space-y-1">
            {verdict.key_benefits.slice(0, 3).map((b: string, i: number) => (
              <li key={i} className="text-xs text-slate-300 flex gap-1.5">
                <span className="text-green-400 mt-0.5 shrink-0">▸</span>
                <span>{b}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Projection tabs */}
      <div>
        <div className="flex gap-1 mb-2">
          {(['1yr', '5yr', '10yr'] as ProjectionYear[]).map(yr => (
            <button
              key={yr}
              onClick={() => setActiveYear(yr)}
              className={`text-xs px-2 py-1 rounded transition-colors ${
                activeYear === yr
                  ? 'bg-amber-500 text-slate-900 font-semibold'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {yr}
            </button>
          ))}
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">{projections[activeYear]}</p>
      </div>
    </div>
  );
}
