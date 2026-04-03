'use client';

import { useEffect, useState } from 'react';

const MESSAGES = [
  'Pulling live economic data...',
  'Analysing demographic patterns...',
  'Running Economist agent...',
  'Running Urban Planner agent...',
  'Running Equity Analyst agent...',
  'Generating impact map...',
];

export default function LoadingState() {
  const [msgIndex, setMsgIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMsgIndex(i => (i + 1) % MESSAGES.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/95 flex flex-col items-center justify-center gap-8">
      {/* Pulsing logo */}
      <div className="text-5xl font-black tracking-tighter text-amber-400 animate-pulse">
        CivicLens
      </div>

      {/* Spinner */}
      <div className="w-12 h-12 border-4 border-slate-700 border-t-amber-500 rounded-full animate-spin" />

      {/* Cycling message */}
      <div className="text-slate-400 text-sm font-mono min-h-[20px] transition-all">
        {MESSAGES[msgIndex]}
      </div>

      <div className="text-slate-600 text-xs">
        Three AI agents are analysing your policy in parallel...
      </div>
    </div>
  );
}
