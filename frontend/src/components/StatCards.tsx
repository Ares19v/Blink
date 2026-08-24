import React from 'react';
import { Activity, Zap, Clock, Timer } from 'lucide-react';
import type { BlinkTelemetry } from '../types';

interface StatCardsProps {
  telemetry: BlinkTelemetry;
}

export const StatCards: React.FC<StatCardsProps> = ({ telemetry }) => {
  // Format seconds to mm:ss
  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const getFatigueColor = (score: number | null) => {
    if (score === null) return { text: 'text-cyber-muted', bg: 'bg-gray-800', label: 'Measuring...' };
    if (score < 35) return { text: 'text-emerald-400', bg: 'bg-emerald-500/20', border: 'border-emerald-500/40', label: 'Fully Rested' };
    if (score < 70) return { text: 'text-amber-400', bg: 'bg-amber-500/20', border: 'border-amber-500/40', label: 'Moderate Strain' };
    return { text: 'text-rose-400', bg: 'bg-rose-500/20', border: 'border-rose-500/40', label: 'High Fatigue' };
  };

  const fatigueInfo = getFatigueColor(telemetry.fatigue_score);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Blink Rate Card */}
      <div className="rounded-2xl bg-cyber-card border border-cyber-border p-5 relative overflow-hidden flex flex-col justify-between hover:border-cyber-cyan/30 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-cyber-muted uppercase tracking-wider">
            Blink Rate
          </span>
          <div className="p-2 rounded-xl bg-cyber-cardHover text-cyber-cyan">
            <Activity className="w-4 h-4" />
          </div>
        </div>

        <div className="my-2">
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-white tracking-tight">
              {telemetry.blink_rate !== null ? telemetry.blink_rate.toFixed(1) : '--'}
            </span>
            <span className="text-xs text-cyber-muted font-mono">BPM</span>
          </div>
          <p className="text-xs text-cyber-muted mt-1">
            {telemetry.blink_rate !== null
              ? telemetry.blink_rate >= 12
                ? 'Healthy blinking frequency'
                : 'Low blink rate — consider blinking'
              : 'Collecting 10s baseline...'}
          </p>
        </div>

        <div className="w-full bg-cyber-border rounded-full h-1.5 mt-3 overflow-hidden">
          <div
            className="bg-cyber-cyan h-full rounded-full transition-all duration-500"
            style={{
              width: `${Math.min(100, ((telemetry.blink_rate || 0) / 25) * 100)}%`,
            }}
          />
        </div>
      </div>

      {/* 2. Fatigue Score Card */}
      <div className="rounded-2xl bg-cyber-card border border-cyber-border p-5 relative overflow-hidden flex flex-col justify-between hover:border-cyber-cyan/30 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-cyber-muted uppercase tracking-wider">
            Fatigue Score
          </span>
          <div className="p-2 rounded-xl bg-cyber-cardHover text-amber-400">
            <Zap className="w-4 h-4" />
          </div>
        </div>

        <div className="my-2">
          <div className="flex items-baseline gap-2">
            <span className={`text-3xl font-extrabold tracking-tight ${fatigueInfo.text}`}>
              {telemetry.fatigue_score !== null ? telemetry.fatigue_score.toFixed(0) : '--'}
            </span>
            <span className="text-xs text-cyber-muted font-mono">/ 100</span>
          </div>
          <div className="flex items-center gap-1.5 mt-1">
            <span className={`w-2 h-2 rounded-full ${fatigueInfo.bg}`} />
            <span className={`text-xs font-medium ${fatigueInfo.text}`}>{fatigueInfo.label}</span>
          </div>
        </div>

        <div className="w-full bg-cyber-border rounded-full h-1.5 mt-3 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              telemetry.fatigue_score && telemetry.fatigue_score > 70
                ? 'bg-rose-500'
                : telemetry.fatigue_score && telemetry.fatigue_score > 35
                ? 'bg-amber-400'
                : 'bg-emerald-400'
            }`}
            style={{
              width: `${Math.min(100, telemetry.fatigue_score || 0)}%`,
            }}
          />
        </div>
      </div>

      {/* 3. Blinks & Duration Card */}
      <div className="rounded-2xl bg-cyber-card border border-cyber-border p-5 relative overflow-hidden flex flex-col justify-between hover:border-cyber-cyan/30 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-cyber-muted uppercase tracking-wider">
            Total Blinks & Dur.
          </span>
          <div className="p-2 rounded-xl bg-cyber-cardHover text-blue-400">
            <Clock className="w-4 h-4" />
          </div>
        </div>

        <div className="my-2">
          <div className="flex items-baseline justify-between">
            <div>
              <span className="text-3xl font-extrabold text-white tracking-tight">
                {telemetry.total_blinks}
              </span>
              <span className="text-xs text-cyber-muted ml-1 font-mono">blinks</span>
            </div>
            <div className="text-right">
              <span className="text-lg font-bold text-cyber-cyan">
                {telemetry.blink_duration_ms > 0 ? telemetry.blink_duration_ms.toFixed(0) : '--'}
              </span>
              <span className="text-xs text-cyber-muted ml-1 font-mono">ms</span>
            </div>
          </div>
          <p className="text-xs text-cyber-muted mt-1">
            Session: {formatTime(telemetry.session_duration_sec)}
          </p>
        </div>

        <div className="flex items-center justify-between text-[11px] text-cyber-muted border-t border-cyber-border/60 pt-2 mt-1">
          <span>EAR Thr: {telemetry.ear_threshold.toFixed(2)}</span>
          <span>Live EAR: {telemetry.ear.toFixed(2)}</span>
        </div>
      </div>

      {/* 4. 20-20-20 Break Card */}
      <div className="rounded-2xl bg-cyber-card border border-cyber-border p-5 relative overflow-hidden flex flex-col justify-between hover:border-cyber-cyan/30 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-cyber-muted uppercase tracking-wider">
            20-20-20 Break
          </span>
          <div className="p-2 rounded-xl bg-cyber-cardHover text-emerald-400">
            <Timer className="w-4 h-4" />
          </div>
        </div>

        <div className="my-2">
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-white tracking-tight">
              {formatTime(telemetry.twenty_countdown_sec)}
            </span>
            <span className="text-xs text-cyber-muted font-mono">remaining</span>
          </div>
          <p className="text-xs text-cyber-muted mt-1">
            Look 20ft away for 20s every 20m
          </p>
        </div>

        <div className="w-full bg-cyber-border rounded-full h-1.5 mt-3 overflow-hidden">
          <div
            className="bg-emerald-400 h-full rounded-full transition-all duration-500"
            style={{
              width: `${Math.max(0, Math.min(100, (telemetry.twenty_countdown_sec / 1200) * 100))}%`,
            }}
          />
        </div>
      </div>
    </div>
  );
};
