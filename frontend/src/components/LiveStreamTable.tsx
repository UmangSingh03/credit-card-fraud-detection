import React, { useState } from 'react';
import { TransactionItem } from '../types';
import { AlertTriangle, CheckCircle, Info, Search, Filter, ShieldAlert, Sparkles, ExternalLink } from 'lucide-react';

interface LiveStreamTableProps {
  transactions: TransactionItem[];
  onSelectTransaction: (tx: TransactionItem) => void;
  onClear: () => void;
}

export const LiveStreamTable: React.FC<LiveStreamTableProps> = ({
  transactions,
  onSelectTransaction,
  onClear,
}) => {
  const [filterRisk, setFilterRisk] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filtered = transactions.filter((tx) => {
    const risk = tx.prediction?.risk_category || 'LOW';
    if (filterRisk !== 'ALL' && risk !== filterRisk) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const id = (tx.id || tx.transaction_id || '').toLowerCase();
      const amount = (tx.amount || 0).toString();
      return id.includes(q) || amount.includes(q);
    }
    return true;
  });

  return (
    <div className="glass-panel rounded-2xl overflow-hidden border border-white/10 flex flex-col h-[580px]">
      {/* Header & Controls */}
      <div className="p-4 border-b border-white/10 flex flex-wrap items-center justify-between gap-3 bg-white/[0.02]">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <span className="flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide">Live Transaction Stream</h3>
            <p className="text-xs text-slate-400">{filtered.length} visible transactions ({transactions.length} buffered)</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Search */}
          <div className="relative">
            <Search className="h-3.5 w-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search ID or amount..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-44"
            />
          </div>

          {/* Risk Filter */}
          <div className="flex items-center bg-white/5 rounded-lg p-0.5 border border-white/10 text-xs">
            {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((risk) => (
              <button
                key={risk}
                onClick={() => setFilterRisk(risk)}
                className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                  filterRisk === risk
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {risk}
              </button>
            ))}
          </div>

          {/* Clear */}
          <button
            onClick={onClear}
            className="text-xs text-slate-400 hover:text-rose-400 px-2 py-1.5 rounded-lg hover:bg-rose-500/10 transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-y-auto flex-1 divide-y divide-white/5 font-mono text-xs">
        {filtered.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-8 text-center text-slate-500">
            <Sparkles className="h-8 w-8 mb-2 text-indigo-400/50" />
            <p className="font-sans text-sm font-medium text-slate-400">Waiting for incoming transactions...</p>
            <p className="font-sans text-xs text-slate-500 mt-1">Start the simulation or send requests to POST /api/transactions</p>
          </div>
        ) : (
          <table className="w-full text-left">
            <thead className="bg-[#0e1320] text-slate-400 text-[11px] uppercase tracking-wider sticky top-0 z-10 font-sans border-b border-white/5">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Time</th>
                <th className="py-2.5 px-4 font-semibold">Tx ID</th>
                <th className="py-2.5 px-4 font-semibold text-right">Amount</th>
                <th className="py-2.5 px-4 font-semibold">Risk Level</th>
                <th className="py-2.5 px-4 font-semibold text-right">Fraud Prob</th>
                <th className="py-2.5 px-4 font-semibold">Anomaly Status</th>
                <th className="py-2.5 px-4 font-semibold text-right">Latency</th>
                <th className="py-2.5 px-4 font-semibold text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filtered.map((tx) => {
                const id = tx.id || tx.transaction_id || 'tx-temp';
                const risk = tx.prediction?.risk_category || 'LOW';
                const prob = tx.prediction?.fraud_probability;
                const isAnomalous = tx.prediction?.is_anomalous;
                const latency = tx.prediction?.latency_ms || 1.2;

                return (
                  <tr
                    key={id}
                    onClick={() => onSelectTransaction(tx)}
                    className="hover:bg-white/[0.04] cursor-pointer transition-colors group"
                  >
                    <td className="py-2.5 px-4 text-slate-400 whitespace-nowrap">
                      {tx.created_at ? new Date(tx.created_at).toLocaleTimeString() : 'now'}
                    </td>
                    <td className="py-2.5 px-4 text-slate-300 font-medium whitespace-nowrap">
                      {id.slice(0, 8)}...
                    </td>
                    <td className="py-2.5 px-4 text-right font-bold text-white whitespace-nowrap">
                      ${(tx.amount || 0).toFixed(2)}
                    </td>
                    <td className="py-2.5 px-4 whitespace-nowrap">
                      <span className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wide font-sans ${
                        risk === 'HIGH'
                          ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30 animate-pulse'
                          : risk === 'MEDIUM'
                          ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                          : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                      }`}>
                        {risk === 'HIGH' ? <ShieldAlert className="h-3 w-3 mr-1" /> : null}
                        {risk}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-right whitespace-nowrap">
                      <span className={`font-semibold ${
                        (prob || 0) > 0.5 ? 'text-rose-400' : 'text-slate-300'
                      }`}>
                        {prob !== null && prob !== undefined ? `${(prob * 100).toFixed(1)}%` : 'N/A'}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 whitespace-nowrap">
                      {isAnomalous ? (
                        <span className="inline-flex items-center text-[10px] font-sans px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-400 border border-cyan-500/30">
                          Anomaly Detected
                        </span>
                      ) : (
                        <span className="text-slate-500 text-[11px] font-sans">Normal</span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 text-right text-slate-400 whitespace-nowrap">
                      {latency.toFixed(1)}ms
                    </td>
                    <td className="py-2.5 px-4 text-center whitespace-nowrap">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectTransaction(tx);
                        }}
                        className="p-1 rounded hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
                        title="Inspect transaction"
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
