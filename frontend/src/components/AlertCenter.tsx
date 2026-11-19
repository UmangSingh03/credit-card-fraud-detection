import React, { useState, useEffect } from 'react';
import { AlertItem, TransactionItem } from '../types';
import { ShieldAlert, ShieldCheck, Check, X, Clock, MessageSquare, AlertCircle, RefreshCw } from 'lucide-react';

interface AlertCenterProps {
  alerts: AlertItem[];
  onSelectTransactionId: (txId: string) => void;
  onUpdateAlert: (alertId: string, status: string, notes?: string, confirmedFraud?: boolean | null) => void;
}

export const AlertCenter: React.FC<AlertCenterProps> = ({
  alerts,
  onSelectTransactionId,
  onUpdateAlert,
}) => {
  const [filterStatus, setFilterStatus] = useState<string>('PENDING');
  const [activeNotes, setActiveNotes] = useState<Record<string, string>>({});
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const filteredAlerts = alerts.filter((a) => {
    if (filterStatus === 'ALL') return true;
    return a.status === filterStatus;
  });

  const handleAction = async (
    alertId: string,
    newStatus: string,
    confirmedFraud: boolean | null = null
  ) => {
    setLoadingId(alertId);
    try {
      const notes = activeNotes[alertId];
      const payload: any = { status: newStatus };
      if (notes !== undefined) payload.review_notes = notes;
      if (confirmedFraud !== null) payload.confirmed_fraud = confirmedFraud;

      const res = await fetch(`/api/alerts/${alertId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        onUpdateAlert(alertId, newStatus, notes, confirmedFraud);
      }
    } catch (err) {
      console.error('Failed to update alert', err);
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="space-y-4">
      {/* Filters & Header */}
      <div className="glass-panel p-5 rounded-2xl flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center space-x-2">
            <ShieldAlert className="h-5 w-5 text-rose-400" />
            <span>Fraud Alert Triage Center</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Human-in-the-loop review workflow for high-risk transactions and behavioral anomalies.
          </p>
        </div>

        {/* Status Filters */}
        <div className="flex bg-white/5 rounded-xl p-1 border border-white/10 text-xs">
          {['ALL', 'PENDING', 'ACKNOWLEDGED', 'RESOLVED', 'DISMISSED'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                filterStatus === st
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Alert Cards List */}
      <div className="space-y-3">
        {filteredAlerts.length === 0 ? (
          <div className="glass-panel p-12 rounded-2xl text-center text-slate-500">
            <ShieldCheck className="h-10 w-10 mx-auto text-emerald-400/50 mb-2" />
            <p className="font-semibold text-slate-300">No alerts found</p>
            <p className="text-xs mt-1">There are no {filterStatus.toLowerCase()} alerts requiring action right now.</p>
          </div>
        ) : (
          filteredAlerts.map((alert) => {
            const isCritical = alert.severity === 'CRITICAL';
            const isPending = alert.status === 'PENDING';
            const isAck = alert.status === 'ACKNOWLEDGED';

            return (
              <div
                key={alert.id}
                className="glass-panel p-5 rounded-2xl border border-white/10 hover:border-white/20 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                {/* Left Info */}
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center space-x-2">
                    <span className={`text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full ${
                      isCritical
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse'
                        : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    }`}>
                      {alert.severity} SEVERITY
                    </span>

                    <span className="text-[11px] font-semibold text-slate-400 font-mono">
                      Reason: <span className="text-white capitalize">{alert.alert_reason.replace('_', ' ')}</span>
                    </span>

                    <span className="text-xs text-slate-500">&bull;</span>
                    <span className="text-xs text-slate-500 flex items-center">
                      <Clock className="h-3 w-3 mr-1" />
                      {alert.created_at ? new Date(alert.created_at).toLocaleTimeString() : 'now'}
                    </span>
                  </div>

                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-semibold text-white">
                      Alert ID: <span className="font-mono text-xs text-slate-300">{alert.id.slice(0, 8)}...</span>
                    </span>
                    <button
                      onClick={() => onSelectTransactionId(alert.transaction_id)}
                      className="text-xs text-indigo-400 hover:text-indigo-300 underline font-mono flex items-center"
                    >
                      View Tx #{alert.transaction_id.slice(0, 8)}
                    </button>
                  </div>

                  {/* Review Notes field */}
                  <div className="pt-2 max-w-xl">
                    <div className="flex items-center space-x-2">
                      <MessageSquare className="h-3.5 w-3.5 text-slate-500" />
                      <input
                        type="text"
                        placeholder={alert.review_notes || "Add investigator notes..."}
                        value={activeNotes[alert.id] !== undefined ? activeNotes[alert.id] : (alert.review_notes || '')}
                        onChange={(e) => setActiveNotes({ ...activeNotes, [alert.id]: e.target.value })}
                        className="bg-white/5 border border-white/10 rounded-lg px-3 py-1 text-xs text-white placeholder-slate-500 w-full focus:outline-none focus:border-indigo-500 font-sans"
                      />
                    </div>
                  </div>
                </div>

                {/* Right Action Buttons */}
                <div className="flex flex-wrap items-center gap-2">
                  {isPending && (
                    <button
                      onClick={() => handleAction(alert.id, 'ACKNOWLEDGED')}
                      disabled={loadingId === alert.id}
                      className="px-3.5 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white text-xs font-semibold transition-colors"
                    >
                      Acknowledge
                    </button>
                  )}

                  <button
                    onClick={() => handleAction(alert.id, 'RESOLVED', true)}
                    disabled={loadingId === alert.id}
                    className="px-3.5 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-md shadow-rose-600/20 transition-all flex items-center space-x-1"
                  >
                    <ShieldAlert className="h-3.5 w-3.5 mr-1" />
                    <span>Confirm Fraud</span>
                  </button>

                  <button
                    onClick={() => handleAction(alert.id, 'RESOLVED', false)}
                    disabled={loadingId === alert.id}
                    className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/20 transition-all flex items-center space-x-1"
                  >
                    <Check className="h-3.5 w-3.5 mr-1" />
                    <span>Legitimate (False Alarm)</span>
                  </button>

                  <button
                    onClick={() => handleAction(alert.id, 'DISMISSED')}
                    disabled={loadingId === alert.id}
                    className="p-1.5 rounded-xl text-slate-500 hover:text-slate-300 hover:bg-white/5 transition-colors"
                    title="Dismiss alert"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
