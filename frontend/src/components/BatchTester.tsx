import React, { useState } from 'react';
import { Upload, FileText, CheckCircle2, AlertTriangle, ArrowRight, ShieldAlert, Sparkles } from 'lucide-react';

export const BatchTester: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [results, setResults] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setErrorMsg(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setErrorMsg(null);
    setResults(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/transactions/upload-csv', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        setErrorMsg(data.detail || 'Failed to process CSV file');
      } else {
        setResults(data);
      }
    } catch (e: any) {
      setErrorMsg(e.message || 'Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <div className="glass-panel p-8 rounded-3xl border border-white/10 text-center relative overflow-hidden">
        <div className="max-w-md mx-auto space-y-4">
          <div className="h-16 w-16 mx-auto rounded-3xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Upload className="h-8 w-8" />
          </div>

          <div>
            <h3 className="text-lg font-bold text-white">Batch CSV Scoring Engine</h3>
            <p className="text-xs text-slate-400 mt-1">
              Upload credit card transactions formatted with Time, Amount, and V1–V28 columns.
            </p>
          </div>

          <div className="flex items-center justify-center">
            <label className="cursor-pointer px-5 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/15 text-xs font-semibold text-white transition-all flex items-center space-x-2">
              <FileText className="h-4 w-4 text-indigo-400" />
              <span>{file ? file.name : 'Select CSV File'}</span>
              <input type="file" accept=".csv" onChange={handleFileChange} className="hidden" />
            </label>
          </div>

          {file && (
            <div className="pt-2">
              <button
                onClick={handleUpload}
                disabled={loading}
                className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-xs tracking-wide shadow-md shadow-indigo-600/30 transition-all"
              >
                {loading ? 'Evaluating Batch...' : `Score ${file.name}`}
              </button>
            </div>
          )}

          {errorMsg && (
            <p className="text-xs text-rose-400 flex items-center justify-center space-x-1">
              <AlertTriangle className="h-4 w-4 mr-1" />
              <span>{errorMsg}</span>
            </p>
          )}
        </div>
      </div>

      {/* Results View */}
      {results && (
        <div className="glass-panel rounded-3xl overflow-hidden border border-white/10 p-6 space-y-4 animate-fadeIn">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                <span>Batch Scoring Results ({results.processed_rows} records scored)</span>
              </h3>
              <p className="text-xs text-slate-400">File: {results.filename}</p>
            </div>
          </div>

          {/* Table */}
          <div className="max-h-96 overflow-y-auto font-mono text-xs">
            <table className="w-full text-left">
              <thead className="bg-[#0e1320] text-slate-400 text-[11px] uppercase tracking-wider sticky top-0 z-10 font-sans border-b border-white/5">
                <tr>
                  <th className="py-2.5 px-4">Tx ID</th>
                  <th className="py-2.5 px-4 text-right">Amount</th>
                  <th className="py-2.5 px-4">Risk Category</th>
                  <th className="py-2.5 px-4 text-right">Fraud Prob</th>
                  <th className="py-2.5 px-4 text-right">Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {(results.results || []).slice(0, 50).map((r: any) => {
                  const risk = r.prediction?.risk_category || 'LOW';
                  const prob = r.prediction?.fraud_probability;
                  return (
                    <tr key={r.transaction_id} className="hover:bg-white/[0.03]">
                      <td className="py-2 px-4 text-slate-300 font-medium">
                        {r.transaction_id.slice(0, 10)}...
                      </td>
                      <td className="py-2 px-4 text-right font-bold text-white">
                        ${(r.amount || 0).toFixed(2)}
                      </td>
                      <td className="py-2 px-4">
                        <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold font-sans ${
                          risk === 'HIGH'
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                            : risk === 'MEDIUM'
                            ? 'bg-amber-500/20 text-amber-300'
                            : 'bg-emerald-500/20 text-emerald-300'
                        }`}>
                          {risk}
                        </span>
                      </td>
                      <td className="py-2 px-4 text-right text-slate-300">
                        {prob !== null && prob !== undefined ? `${(prob * 100).toFixed(1)}%` : 'N/A'}
                      </td>
                      <td className="py-2 px-4 text-right text-slate-400">
                        {r.prediction?.latency_ms?.toFixed(2)}ms
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
