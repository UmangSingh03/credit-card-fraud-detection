import React, { useState, useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { Navbar } from './components/Navbar';
import { StatCards } from './components/StatCards';
import { LiveStreamTable } from './components/LiveStreamTable';
import { TransactionModal } from './components/TransactionModal';
import { AlertCenter } from './components/AlertCenter';
import { ModelStudio } from './components/ModelStudio';
import { SimulationControls } from './components/SimulationControls';
import { BatchTester } from './components/BatchTester';
import { TransactionItem, OverviewStats, AlertItem } from './types';
import { ShieldAlert, X } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('live');
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [selectedTx, setSelectedTx] = useState<TransactionItem | null>(null);
  const [toastAlert, setToastAlert] = useState<AlertItem | null>(null);

  const {
    isConnected,
    transactions,
    alerts,
    trainingProgress,
    clearTransactions,
    updateAlertStatus,
  } = useWebSocket();

  // Fetch initial dashboard metrics
  const fetchStats = async () => {
    try {
      const res = await fetch('/api/dashboard/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (e) {
      console.error('Error fetching stats', e);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = window.setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  // Show a toast alert notification when a new alert comes in
  useEffect(() => {
    if (alerts.length > 0) {
      const newest = alerts[0];
      if (newest.status === 'PENDING') {
        setToastAlert(newest);
        const timer = setTimeout(() => setToastAlert(null), 6000);
        return () => clearTimeout(timer);
      }
    }
  }, [alerts]);

  const handleSelectTransactionId = async (txId: string) => {
    try {
      const res = await fetch(`/api/transactions/${txId}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedTx(data);
      }
    } catch (e) {
      console.error('Error fetching transaction detail', e);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0D14] text-slate-100 flex flex-col">
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isConnected={isConnected}
        modelLoaded={!!stats?.active_model?.name && stats.active_model.name !== 'Not Loaded'}
        modelName={stats?.active_model?.name || 'RandomForest'}
        pendingAlertsCount={stats?.alerts?.pending || 0}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* KPI Summary Cards (always visible on top) */}
        <StatCards stats={stats} liveStreamCount={transactions.length} />

        {/* Tab Content */}
        {activeTab === 'live' && (
          <div className="space-y-6">
            <LiveStreamTable
              transactions={transactions}
              onSelectTransaction={(tx) => setSelectedTx(tx)}
              onClear={clearTransactions}
            />
            <SimulationControls
              onTransactionScored={(res) => setSelectedTx(res)}
            />
          </div>
        )}

        {activeTab === 'alerts' && (
          <AlertCenter
            alerts={alerts}
            onSelectTransactionId={handleSelectTransactionId}
            onUpdateAlert={updateAlertStatus}
          />
        )}

        {activeTab === 'models' && (
          <ModelStudio trainingProgress={trainingProgress} />
        )}

        {activeTab === 'batch' && (
          <div className="space-y-6">
            <BatchTester />
            <SimulationControls
              onTransactionScored={(res) => setSelectedTx(res)}
            />
          </div>
        )}
      </main>

      {/* Transaction Details Inspector Modal */}
      <TransactionModal
        transaction={selectedTx}
        onClose={() => setSelectedTx(null)}
      />

      {/* Live Fraud Alert Toast Notification */}
      {toastAlert && (
        <div className="fixed bottom-6 right-6 z-50 animate-bounce">
          <div className="glass-panel p-4 rounded-2xl border-rose-500/40 bg-rose-500/10 shadow-2xl flex items-center space-x-3 text-xs max-w-sm">
            <div className="p-2 rounded-xl bg-rose-500/20 text-rose-400">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <div className="flex items-center space-x-1.5 font-bold text-rose-300">
                <span>NEW FRAUD ALERT</span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-rose-500/20 uppercase">
                  {toastAlert.severity}
                </span>
              </div>
              <p className="text-slate-300 mt-0.5">
                Suspected pattern detected: {toastAlert.alert_reason.replace('_', ' ')}
              </p>
            </div>
            <button
              onClick={() => {
                handleSelectTransactionId(toastAlert.transaction_id);
                setToastAlert(null);
              }}
              className="text-indigo-400 hover:text-indigo-300 font-bold underline"
            >
              Review
            </button>
            <button
              onClick={() => setToastAlert(null)}
              className="text-slate-500 hover:text-slate-300"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
