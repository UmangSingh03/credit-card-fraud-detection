import React from 'react';
import { OverviewStats } from '../types';
import { ShieldCheck, ShieldAlert, Zap, Layers, ArrowUpRight, Clock } from 'lucide-react';

interface StatCardsProps {
  stats: OverviewStats | null;
  liveStreamCount: number;
}

export const StatCards: React.FC<StatCardsProps> = ({ stats, liveStreamCount }) => {
  const total = (stats?.total_transactions || 0) + liveStreamCount;
  const highRisk = stats?.high_risk_count || 0;
  const fraudRate = stats?.fraud_rate_pct || 0.0;
  const pendingAlerts = stats?.alerts?.pending || 0;
  const avgLatency = stats?.avg_latency_ms || 2.4;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Scored */}
      <div className="glass-panel p-5 rounded-2xl relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/10 rounded-full blur-2xl group-hover:bg-indigo-500/20 transition-all"></div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Scored</span>
          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Layers className="h-4 w-4" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-2xl font-bold font-mono tracking-tight text-white">{total.toLocaleString()}</span>
          <span className="text-xs text-emerald-400 flex items-center font-medium">
            <ArrowUpRight className="h-3 w-3" /> Live
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-2 flex items-center">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 mr-1.5"></span>
          Processed across stream & API
        </p>
      </div>

      {/* Fraud Rate / High Risk */}
      <div className="glass-panel p-5 rounded-2xl relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-24 h-24 bg-rose-500/10 rounded-full blur-2xl group-hover:bg-rose-500/20 transition-all"></div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">High Risk Rate</span>
          <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <ShieldAlert className="h-4 w-4" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-2xl font-bold font-mono tracking-tight text-rose-400">{fraudRate.toFixed(2)}%</span>
          <span className="text-xs text-slate-400">({highRisk} flagged)</span>
        </div>
        <p className="text-xs text-slate-400 mt-2">
          Policy threshold: &ge; 70% probability
        </p>
      </div>

      {/* Pending Alerts */}
      <div className="glass-panel p-5 rounded-2xl relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/10 rounded-full blur-2xl group-hover:bg-amber-500/20 transition-all"></div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Pending Triage</span>
          <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <ShieldCheck className="h-4 w-4" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-2xl font-bold font-mono tracking-tight text-white">{pendingAlerts}</span>
          <span className="text-xs text-amber-400 font-medium">Action Required</span>
        </div>
        <p className="text-xs text-slate-400 mt-2">
          Total alerts logged: {stats?.alerts?.total || 0}
        </p>
      </div>

      {/* Inference Latency */}
      <div className="glass-panel p-5 rounded-2xl relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/10 rounded-full blur-2xl group-hover:bg-cyan-500/20 transition-all"></div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Avg Latency</span>
          <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Zap className="h-4 w-4" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-2xl font-bold font-mono tracking-tight text-cyan-400">{avgLatency.toFixed(2)} ms</span>
          <span className="text-xs text-emerald-400 font-medium">&lt; 10ms SLA</span>
        </div>
        <p className="text-xs text-slate-400 mt-2 flex items-center">
          <Clock className="h-3 w-3 mr-1 text-slate-400" />
          Sub-millisecond model inference
        </p>
      </div>
    </div>
  );
};
