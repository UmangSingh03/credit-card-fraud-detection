import React, { useState, useEffect } from 'react';
import { SimulationStatus } from '../types';
import { Play, Pause, Square, Gauge, Sliders, Zap, Check, AlertTriangle } from 'lucide-react';

interface SimulationControlsProps {
  onTransactionScored?: (result: any) => void;
}

export const SimulationControls: React.FC<SimulationControlsProps> = ({ onTransactionScored }) => {
  const [status, setStatus] = useState<SimulationStatus>({
    state: 'STOPPED',
    interval_seconds: 1.0,
    batch_size: 1,
    total_streamed: 0,
    total_fraud_detected: 0,
  });

  const [interval, setInterval] = useState<number>(1.0);
  const [batchSize, setBatchSize] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);

  // Manual test transaction form
  const [testAmount, setTestAmount] = useState<number>(149.99);
  const [testV14, setTestV14] = useState<number>(-4.5); // Often strongly negative in fraud cases
  const [testV4, setTestV4] = useState<number>(3.2);   // Often positive in fraud cases
  const [scoringLoading, setScoringLoading] = useState<boolean>(false);
  const [scoreResult, setScoreResult] = useState<any>(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/simulation/status');
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (e) {
      console.error('Error fetching sim status', e);
    }
  };

  useEffect(() => {
    fetchStatus();
    const intervalId = window.setInterval(fetchStatus, 3000);
    return () => clearInterval(intervalId);
  }, []);

  const handleStart = async () => {
    setLoading(true);
    try {
      await fetch('/api/simulation/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ interval_seconds: interval, batch_size: batchSize }),
      });
      await fetchStatus();
    } finally {
      setLoading(false);
    }
  };

  const handlePause = async () => {
    setLoading(true);
    try {
      await fetch('/api/simulation/pause', { method: 'POST' });
      await fetchStatus();
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      await fetch('/api/simulation/stop', { method: 'POST' });
      await fetchStatus();
    } finally {
      setLoading(false);
    }
  };

  const handleSingleScore = async () => {
    setScoringLoading(true);
    setScoreResult(null);
    try {
      // Build a synthetic feature vector using realistic standard values
      const features: Record<string, number> = {
        Time: Math.floor(Math.random() * 100000),
        Amount: testAmount,
      };
      for (let i = 1; i <= 28; i++) {
        features[`V${i}`] = (Math.random() - 0.5) * 0.5;
      }
      features['V14'] = testV14;
      features['V4'] = testV4;

      const res = await fetch('/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...features, explain: true }),
      });
      const data = await res.json();
      setScoreResult(data);
      if (onTransactionScored) onTransactionScored(data);
    } catch (e: any) {
      console.error('Scoring error', e);
    } finally {
      setScoringLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Real-Time Transaction Streamer Control */}
      <div className="glass-panel p-6 rounded-3xl border border-white/10 space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <Sliders className="h-4 w-4 text-indigo-400" />
              <span>Real-Time Transaction Streamer</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Replays transactions from Kaggle European credit card dataset in real-time.
            </p>
          </div>

          <span className={`text-[10px] font-extrabold uppercase px-3 py-1 rounded-full ${
            status.state === 'RUNNING'
              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 animate-pulse'
              : status.state === 'PAUSED'
              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
              : 'bg-slate-500/20 text-slate-400 border border-white/10'
          }`}>
            {status.state}
          </span>
        </div>

        {/* Buttons */}
        <div className="flex items-center space-x-3">
          <button
            onClick={handleStart}
            disabled={loading || status.state === 'RUNNING'}
            className="flex-1 py-3 px-4 rounded-2xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white font-bold text-xs tracking-wide flex items-center justify-center space-x-2 shadow-lg shadow-indigo-600/30 transition-all"
          >
            <Play className="h-4 w-4" />
            <span>{status.state === 'PAUSED' ? 'Resume Stream' : 'Start Stream'}</span>
          </button>

          <button
            onClick={handlePause}
            disabled={loading || status.state !== 'RUNNING'}
            className="py-3 px-4 rounded-2xl bg-amber-600/30 hover:bg-amber-600/50 text-amber-300 border border-amber-500/30 disabled:opacity-40 font-bold text-xs flex items-center justify-center space-x-2 transition-all"
          >
            <Pause className="h-4 w-4" />
            <span>Pause</span>
          </button>

          <button
            onClick={handleStop}
            disabled={loading || status.state === 'STOPPED'}
            className="py-3 px-4 rounded-2xl bg-rose-600/20 hover:bg-rose-600/40 text-rose-300 border border-rose-500/30 disabled:opacity-40 font-bold text-xs flex items-center justify-center space-x-2 transition-all"
          >
            <Square className="h-4 w-4" />
            <span>Stop</span>
          </button>
        </div>

        {/* Sliders */}
        <div className="space-y-4 pt-2">
          <div>
            <div className="flex justify-between text-xs text-slate-300 font-semibold mb-1">
              <span>Stream Interval: {interval}s</span>
              <span className="text-slate-500">{(1 / interval).toFixed(1)} tx/second</span>
            </div>
            <input
              type="range"
              min="0.1"
              max="3.0"
              step="0.1"
              value={interval}
              onChange={(e) => setInterval(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs text-slate-300 font-semibold mb-1">
              <span>Batch Size: {batchSize} {batchSize === 1 ? 'transaction' : 'transactions'} / tick</span>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              step="1"
              value={batchSize}
              onChange={(e) => setBatchSize(parseInt(e.target.value))}
              className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-3 pt-2 font-mono text-xs">
          <div className="p-3 rounded-2xl bg-white/[0.02] border border-white/5">
            <span className="text-[10px] text-slate-500 uppercase block font-sans">Streamed Transactions</span>
            <span className="text-base font-bold text-white">{status.total_streamed.toLocaleString()}</span>
          </div>
          <div className="p-3 rounded-2xl bg-white/[0.02] border border-white/5">
            <span className="text-[10px] text-slate-500 uppercase block font-sans">Detected High Risk</span>
            <span className="text-base font-bold text-rose-400">{status.total_fraud_detected.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Manual Transaction Scoring Lab */}
      <div className="glass-panel p-6 rounded-3xl border border-white/10 space-y-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <Zap className="h-4 w-4 text-cyan-400" />
            <span>Interactive Transaction Scoring Lab</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Craft custom transactions to stress-test the model and review instantaneous SHAP explanations.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-[11px] font-semibold text-slate-400 block mb-1">Amount ($)</label>
            <input
              type="number"
              value={testAmount}
              onChange={(e) => setTestAmount(parseFloat(e.target.value) || 0)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="text-[11px] font-semibold text-slate-400 block mb-1">V14 (Fraud indicator)</label>
            <input
              type="number"
              step="0.5"
              value={testV14}
              onChange={(e) => setTestV14(parseFloat(e.target.value) || 0)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="text-[11px] font-semibold text-slate-400 block mb-1">V4 (Variance)</label>
            <input
              type="number"
              step="0.5"
              value={testV4}
              onChange={(e) => setTestV4(parseFloat(e.target.value) || 0)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <button
          onClick={handleSingleScore}
          disabled={scoringLoading}
          className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-bold text-xs tracking-wide shadow-md shadow-cyan-600/20 transition-all flex items-center justify-center space-x-1.5"
        >
          <Zap className="h-3.5 w-3.5" />
          <span>{scoringLoading ? 'Evaluating Model...' : 'Score Custom Transaction'}</span>
        </button>

        {/* Result Card */}
        {scoreResult && (
          <div className={`p-4 rounded-2xl border transition-all animate-fadeIn ${
            scoreResult.prediction?.risk_category === 'HIGH'
              ? 'bg-rose-500/10 border-rose-500/30'
              : scoreResult.prediction?.risk_category === 'MEDIUM'
              ? 'bg-amber-500/10 border-amber-500/30'
              : 'bg-emerald-500/10 border-emerald-500/30'
          }`}>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white">Scoring Result</span>
              <span className={`text-[11px] font-extrabold uppercase px-2 py-0.5 rounded ${
                scoreResult.prediction?.risk_category === 'HIGH'
                  ? 'bg-rose-500/20 text-rose-300'
                  : scoreResult.prediction?.risk_category === 'MEDIUM'
                  ? 'bg-amber-500/20 text-amber-300'
                  : 'bg-emerald-500/20 text-emerald-300'
              }`}>
                {scoreResult.prediction?.risk_category} RISK
              </span>
            </div>
            <div className="mt-2 grid grid-cols-3 gap-2 font-mono text-xs">
              <div>
                <span className="text-[10px] text-slate-400 block font-sans">Probability</span>
                <span className="text-white font-bold">
                  {((scoreResult.prediction?.fraud_probability || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block font-sans">Anomaly</span>
                <span className="text-cyan-400 font-semibold">
                  {scoreResult.prediction?.anomaly_score?.toFixed(3) || '0.000'}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block font-sans">Latency</span>
                <span className="text-slate-300">
                  {scoreResult.prediction?.latency_ms?.toFixed(2)} ms
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
