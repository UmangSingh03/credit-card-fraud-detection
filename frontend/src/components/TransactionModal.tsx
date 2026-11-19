import React from 'react';
import { TransactionItem } from '../types';
import { X, ShieldAlert, ShieldCheck, Activity, Cpu, Sparkles, Layers, ArrowUp, ArrowDown } from 'lucide-react';

interface TransactionModalProps {
  transaction: TransactionItem | null;
  onClose: () => void;
}

export const TransactionModal: React.FC<TransactionModalProps> = ({ transaction, onClose }) => {
  if (!transaction) return null;

  const id = transaction.id || transaction.transaction_id || 'unknown';
  const pred = transaction.prediction;
  const risk = pred?.risk_category || 'LOW';
  const prob = pred?.fraud_probability !== null && pred?.fraud_probability !== undefined
    ? pred.fraud_probability
    : null;
  const isAnomalous = pred?.is_anomalous;
  const anomalyScore = pred?.anomaly_score;
  const latency = pred?.latency_ms || 1.4;
  const features = transaction.features || {};
  const explanation = pred?.explanation;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="glass-panel w-full max-w-4xl max-h-[90vh] rounded-3xl border border-white/15 bg-[#0D121F] shadow-2xl overflow-hidden flex flex-col">
        {/* Modal Header */}
        <div className="p-6 border-b border-white/10 flex items-center justify-between bg-white/[0.02]">
          <div className="flex items-center space-x-3">
            <div className={`p-2.5 rounded-xl border ${
              risk === 'HIGH'
                ? 'bg-rose-500/15 border-rose-500/30 text-rose-400'
                : risk === 'MEDIUM'
                ? 'bg-amber-500/15 border-amber-500/30 text-amber-400'
                : 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400'
            }`}>
              {risk === 'HIGH' ? <ShieldAlert className="h-6 w-6" /> : <ShieldCheck className="h-6 w-6" />}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white tracking-tight">Transaction Inspector</h2>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-white/10 text-slate-300">
                  {id.slice(0, 16)}...
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Processed at {new Date(transaction.created_at).toLocaleString()} &bull; Source: <span className="uppercase text-indigo-400">{transaction.source || 'api'}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Top Score Banner */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Risk Category */}
            <div className={`p-4 rounded-2xl border ${
              risk === 'HIGH'
                ? 'bg-rose-500/10 border-rose-500/30'
                : risk === 'MEDIUM'
                ? 'bg-amber-500/10 border-amber-500/30'
                : 'bg-emerald-500/10 border-emerald-500/30'
            }`}>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                Risk Classification
              </span>
              <span className={`text-2xl font-black font-sans tracking-tight ${
                risk === 'HIGH' ? 'text-rose-400' : risk === 'MEDIUM' ? 'text-amber-400' : 'text-emerald-400'
              }`}>
                {risk} RISK
              </span>
              <p className="text-[11px] text-slate-400 mt-1">
                {risk === 'HIGH' ? 'Probability exceeds 70% threshold' : risk === 'MEDIUM' ? 'Between 30% and 70%' : 'Below 30% baseline'}
              </p>
            </div>

            {/* Model Probability */}
            <div className="p-4 rounded-2xl border border-white/10 bg-white/[0.02]">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                Model Fraud Probability
              </span>
              <span className="text-2xl font-bold font-mono text-white">
                {prob !== null ? `${(prob * 100).toFixed(2)}%` : 'N/A'}
              </span>
              <div className="w-full bg-white/10 h-1.5 rounded-full mt-2 overflow-hidden">
                <div
                  className={`h-full ${risk === 'HIGH' ? 'bg-rose-500' : risk === 'MEDIUM' ? 'bg-amber-500' : 'bg-emerald-500'}`}
                  style={{ width: `${Math.min(100, Math.max(0, (prob || 0) * 100))}%` }}
                ></div>
              </div>
            </div>

            {/* Anomaly Score */}
            <div className="p-4 rounded-2xl border border-white/10 bg-white/[0.02]">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                Isolation Forest Score
              </span>
              <div className="flex items-baseline space-x-2">
                <span className="text-2xl font-bold font-mono text-cyan-400">
                  {anomalyScore !== null && anomalyScore !== undefined ? anomalyScore.toFixed(3) : '0.000'}
                </span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase ${
                  isAnomalous ? 'bg-rose-500/20 text-rose-300' : 'bg-emerald-500/20 text-emerald-300'
                }`}>
                  {isAnomalous ? 'Anomalous' : 'Normal'}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">Unsupervised pattern deviation</p>
            </div>

            {/* Transaction Amount */}
            <div className="p-4 rounded-2xl border border-white/10 bg-white/[0.02]">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                Amount & Latency
              </span>
              <span className="text-2xl font-bold font-mono text-white">
                ${(transaction.amount || 0).toFixed(2)}
              </span>
              <p className="text-[11px] text-slate-400 mt-1 font-mono">
                {latency.toFixed(2)} ms inference time
              </p>
            </div>
          </div>

          {/* Explainability (SHAP Values) */}
          <div className="p-5 rounded-2xl border border-white/10 bg-white/[0.02]">
            <div className="flex items-center space-x-2 mb-3">
              <Sparkles className="h-4 w-4 text-indigo-400" />
              <h3 className="text-sm font-bold text-white">SHAP Local Feature Explainability</h3>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Shows how individual PCA components shifted the model's fraud probability away from the base value.
            </p>

            {explanation && explanation.features && explanation.features.length > 0 ? (
              <div className="space-y-2.5">
                {explanation.features.map((feat) => {
                  const isRiskInc = feat.direction === 'increases_fraud_risk';
                  return (
                    <div key={feat.feature} className="flex items-center text-xs">
                      <span className="font-mono font-bold text-slate-300 w-16">{feat.feature}</span>
                      <span className="font-mono text-slate-400 w-24 text-right pr-4">
                        val: {feat.value.toFixed(2)}
                      </span>
                      <div className="flex-1 bg-white/5 h-4 rounded-full overflow-hidden flex items-center relative">
                        <div
                          className={`h-full rounded-full transition-all flex items-center justify-end px-2 text-[10px] font-bold ${
                            isRiskInc ? 'bg-rose-500/80 text-white' : 'bg-emerald-500/80 text-white'
                          }`}
                          style={{
                            width: `${Math.min(100, Math.max(15, Math.abs(feat.contribution) * 80))}%`,
                          }}
                        >
                          {isRiskInc ? '+' : '-'}{Math.abs(feat.contribution).toFixed(3)}
                        </div>
                      </div>
                      <span className={`w-32 text-right pl-3 font-semibold text-[11px] flex items-center justify-end ${
                        isRiskInc ? 'text-rose-400' : 'text-emerald-400'
                      }`}>
                        {isRiskInc ? (
                          <>
                            <ArrowUp className="h-3 w-3 mr-0.5" /> Increases Risk
                          </>
                        ) : (
                          <>
                            <ArrowDown className="h-3 w-3 mr-0.5" /> Normalizing
                          </>
                        )}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="py-6 text-center text-slate-500 text-xs">
                Local SHAP explanation generated automatically for elevated risk transactions.
              </div>
            )}
          </div>

          {/* Full Feature Set */}
          <div>
            <h3 className="text-sm font-bold text-white mb-3 flex items-center space-x-2">
              <Layers className="h-4 w-4 text-slate-400" />
              <span>Full PCA Feature Vector (V1–V28, Time, Amount)</span>
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-2 font-mono text-xs">
              <div className="p-2.5 rounded-xl bg-white/[0.02] border border-white/5">
                <span className="text-[10px] text-slate-500 uppercase block">Time</span>
                <span className="text-white font-medium">{transaction.time_seconds || 0}s</span>
              </div>
              <div className="p-2.5 rounded-xl bg-white/[0.02] border border-white/5">
                <span className="text-[10px] text-slate-500 uppercase block">Amount</span>
                <span className="text-emerald-400 font-bold">${(transaction.amount || 0).toFixed(2)}</span>
              </div>
              {Array.from({ length: 28 }, (_, i) => `V${i + 1}`).map((k) => (
                <div key={k} className="p-2.5 rounded-xl bg-white/[0.02] border border-white/5">
                  <span className="text-[10px] text-slate-500 uppercase block">{k}</span>
                  <span className="text-slate-300 font-medium">
                    {features[k] !== undefined ? features[k].toFixed(3) : '0.000'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/10 bg-white/[0.01] flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition-all"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
