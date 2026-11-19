import React from 'react';
import { Shield, ShieldAlert, Cpu, Activity, Database, CheckCircle2, AlertTriangle, Radio } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isConnected: boolean;
  modelLoaded: boolean;
  modelName: string;
  pendingAlertsCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  isConnected,
  modelLoaded,
  modelName,
  pendingAlertsCount,
}) => {
  const tabs = [
    { id: 'live', label: 'Live Monitor', icon: Activity },
    { id: 'alerts', label: 'Alert Triage', icon: ShieldAlert, badge: pendingAlertsCount },
    { id: 'models', label: 'ML Models & Benchmark', icon: Cpu },
    { id: 'batch', label: 'Batch & Simulation', icon: Database },
  ];

  return (
    <header className="border-b border-white/10 bg-[#0B0F19]/80 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-[1px] shadow-lg shadow-indigo-500/20">
              <div className="h-full w-full bg-[#0D121F] rounded-[11px] flex items-center justify-center">
                <Shield className="h-5 w-5 text-indigo-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-base tracking-tight text-white">AEGIS<span className="text-indigo-400">GUARD</span></span>
                <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  AI v2.4
                </span>
              </div>
              <p className="text-[11px] text-slate-400 leading-none">Real-Time Fraud Prevention System</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex space-x-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                  {tab.badge !== undefined && tab.badge > 0 && (
                    <span className={`text-xs px-1.5 py-0.2 rounded-full font-bold ${
                      isActive ? 'bg-white text-indigo-700' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    }`}>
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* System Status Indicators */}
          <div className="flex items-center space-x-3 text-xs">
            {/* Live Socket Status */}
            <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full border ${
              isConnected
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-rose-500/10 text-rose-400 border-rose-500/20 animate-pulse'
            }`}>
              <Radio className="h-3 w-3" />
              <span className="font-medium">{isConnected ? 'LIVE STREAM' : 'DISCONNECTED'}</span>
            </div>

            {/* Model Status */}
            <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full border ${
              modelLoaded
                ? 'bg-indigo-500/10 text-indigo-300 border-indigo-500/20'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
            }`}>
              {modelLoaded ? <CheckCircle2 className="h-3 w-3 text-indigo-400" /> : <AlertTriangle className="h-3 w-3 text-amber-400" />}
              <span className="font-mono">{modelLoaded ? modelName : 'No Model'}</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
