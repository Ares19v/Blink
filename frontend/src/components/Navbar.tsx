import React from 'react';
import { Eye, Activity, History, Settings, Sparkles, Power, PowerOff } from 'lucide-react';

interface NavbarProps {
  activeTab: 'dashboard' | 'history';
  setActiveTab: (tab: 'dashboard' | 'history') => void;
  isMonitoring: boolean;
  onToggleMonitoring: () => void;
  onOpenCalibration: () => void;
  onOpenSettings: () => void;
  connected: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  isMonitoring,
  onToggleMonitoring,
  onOpenCalibration,
  onOpenSettings,
  connected,
}) => {
  return (
    <header className="border-b border-cyber-border bg-cyber-bg/80 backdrop-blur-md sticky top-0 z-40 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyber-cyan/30 text-cyber-cyan">
            <Eye className="w-6 h-6 animate-pulse" />
            {isMonitoring && (
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-cyber-cyan rounded-full animate-ping" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-wider text-white">
                BLINK<span className="text-cyber-cyan">.AI</span>
              </h1>
              <span className="text-[10px] px-2 py-0.5 rounded-full font-mono bg-cyber-cyan/10 border border-cyber-cyan/30 text-cyber-cyan">
                v2.0 Web
              </span>
            </div>
            <p className="text-xs text-cyber-muted">Advanced Eye Health & Fatigue Monitor</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 bg-cyber-card border border-cyber-border rounded-xl p-1">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'dashboard'
                ? 'bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/30 shadow-lg shadow-cyber-cyan/10'
                : 'text-cyber-muted hover:text-white hover:bg-cyber-cardHover'
            }`}
          >
            <Activity className="w-4 h-4" />
            Live Dashboard
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'history'
                ? 'bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/30 shadow-lg shadow-cyber-cyan/10'
                : 'text-cyber-muted hover:text-white hover:bg-cyber-cardHover'
            }`}
          >
            <History className="w-4 h-4" />
            History & Analytics
          </button>
        </div>

        {/* Actions & Status */}
        <div className="flex items-center gap-3">
          {/* Calibrate Button */}
          <button
            onClick={onOpenCalibration}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-cyber-card border border-cyber-border text-cyber-text hover:border-cyber-cyan/40 hover:text-cyber-cyan transition-all"
            title="Calibrate resting Eye Aspect Ratio"
          >
            <Sparkles className="w-4 h-4 text-cyber-cyan" />
            <span className="hidden sm:inline">Calibrate EAR</span>
          </button>

          {/* Settings Button */}
          <button
            onClick={onOpenSettings}
            className="p-2 rounded-xl bg-cyber-card border border-cyber-border text-cyber-muted hover:text-white hover:border-cyber-border hover:bg-cyber-cardHover transition-all"
            title="App Settings"
          >
            <Settings className="w-5 h-5" />
          </button>

          {/* Toggle Monitoring Button */}
          <button
            onClick={onToggleMonitoring}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              isMonitoring
                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40 hover:bg-rose-500/30'
                : 'bg-cyber-cyan text-black font-bold shadow-lg shadow-cyber-cyan/20 hover:brightness-110 active:scale-95'
            }`}
          >
            {isMonitoring ? (
              <>
                <PowerOff className="w-4 h-4" />
                Stop
              </>
            ) : (
              <>
                <Power className="w-4 h-4" />
                Start Monitor
              </>
            )}
          </button>

          {/* Connection Pill */}
          <div className="flex items-center gap-1.5 pl-2">
            <span
              className={`w-2 h-2 rounded-full ${
                connected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
              }`}
            />
            <span className="text-[11px] text-cyber-muted hidden md:inline">
              {connected ? 'Sync' : 'Offline'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
