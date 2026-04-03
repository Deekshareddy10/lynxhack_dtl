'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import LoadingState from '@/components/LoadingState';
import { simulatePolicy, getDemo } from '@/lib/api';

export default function HomePage() {
  const router = useRouter();
  const [policyText, setPolicyText] = useState('');
  const [city, setCity] = useState('New York City');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.SyntheticEvent) {
    e.preventDefault();
    if (!policyText.trim()) return;
    setError(null);
    setLoading(true);
    try {
      const result = await simulatePolicy(policyText, city);
      localStorage.setItem('civiclens_result', JSON.stringify(result));
      router.push(`/simulate/${result.simulation_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Simulation failed');
      setLoading(false);
    }
  }

  async function handleDemo() {
    setError(null);
    setLoading(true);
    try {
      const result = await getDemo();
      localStorage.setItem('civiclens_result', JSON.stringify(result));
      router.push(`/simulate/${result.simulation_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Demo failed');
      setLoading(false);
    }
  }

  if (loading) return <LoadingState />;

  return (
    <main className="min-h-screen bg-slate-950 flex flex-col items-center justify-center px-4">
      {/* Logo */}
      <div className="mb-2 text-6xl font-black tracking-tighter text-amber-400">
        CivicLens
      </div>
      <p className="text-slate-400 text-center mb-12 max-w-md">
        Stress-test policy before it hits the real world.
        <br />
        <span className="text-slate-500 text-sm">
          Three AI agents. Real census data. Interactive impact map.
        </span>
      </p>

      {/* Form */}
      <form onSubmit={handleSubmit} className="w-full max-w-2xl flex flex-col gap-4">
        <textarea
          value={policyText}
          onChange={e => setPolicyText(e.target.value)}
          placeholder="Describe your policy... e.g. Cap annual rent increases at 3% for all residential properties in New York City"
          className="w-full h-36 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 resize-none focus:outline-none focus:border-amber-500 transition-colors text-sm"
        />

        <div className="flex gap-3">
          <input
            value={city}
            onChange={e => setCity(e.target.value)}
            placeholder="City"
            className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-colors text-sm"
          />
          <button
            type="submit"
            disabled={!policyText.trim()}
            className="px-8 py-3 bg-amber-500 hover:bg-amber-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-900 font-bold rounded-xl transition-colors"
          >
            Run Simulation
          </button>
        </div>

        {error && (
          <div className="text-red-400 text-sm bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3">
            {error}
          </div>
        )}
      </form>

      {/* Demo button */}
      <div className="mt-8 flex flex-col items-center gap-2">
        <div className="text-slate-600 text-sm">— or —</div>
        <button
          onClick={handleDemo}
          className="text-amber-400 hover:text-amber-300 text-sm font-medium border border-amber-500/30 hover:border-amber-500/60 px-6 py-2 rounded-full transition-colors"
        >
          ⚡ Try Demo — NYC Rent Control Cap
        </button>
        <span className="text-slate-600 text-xs">Pre-analysed · loads instantly</span>
      </div>
    </main>
  );
}
