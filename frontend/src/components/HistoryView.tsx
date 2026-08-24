import React, { useState, useEffect } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
} from 'recharts';
import { History, Trash2, RefreshCw, BarChart2, Clock, Zap, Activity } from 'lucide-react';
import { api } from '../services/api';
import type { DatabaseSummary, SessionRecord } from '../types';

export const HistoryView: React.FC = () => {
  const [sessions, setSessions] = useState<SessionRecord[]>([]);
  const [summary, setSummary] = useState<DatabaseSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [histData, sumData] = await Promise.all([api.getHistory(100), api.getSummary()]);
      setSessions(histData);
      setSummary(sumData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDelete = async (id: number) => {
    if (confirm('Delete this session record?')) {
      try {
        await api.deleteSession(id);
        loadData();
      } catch (e) {
        console.error(e);
      }
    }
  };

  const handleClear = async () => {
    if (confirm('Are you sure you want to clear all monitoring history? This cannot be undone.')) {
      try {
        await api.clearHistory();
        loadData();
      } catch (e) {
        console.error(e);
      }
    }
  };

  // Format chart data (reverse so chronological left-to-right)
  const chartData = [...sessions].reverse().map((s, idx) => ({
    session: `#${idx + 1}`,
    date: new Date(s.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    blink_rate: s.avg_blink_rate,
    fatigue_score: s.avg_fatigue_score,
    duration_min: Math.round((s.duration_secs / 60) * 10) / 10,
    blinks: s.total_blinks,
  }));

  const formatSecs = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const hours = Math.floor(mins / 60);
    if (hours > 0) return `${hours}h ${mins % 60}m`;
    return `${mins}m ${Math.round(secs % 60)}s`;
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <BarChart2 className="w-5 h-5 text-cyber-cyan" />
            Session History & Trends
          </h2>
          <p className="text-xs text-cyber-muted">
            Tracking your long-term blink rate performance and digital eye strain
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyber-cardHover border border-cyber-border text-xs text-cyber-text hover:text-white transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          {sessions.length > 0 && (
            <button
              onClick={handleClear}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-400 hover:bg-rose-500/20 transition-all"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear All
            </button>
          )}
        </div>
      </div>

      {/* Summary KPI Cards */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl bg-cyber-card border border-cyber-border">
            <span className="text-xs text-cyber-muted font-medium">Total Tracked Time</span>
            <div className="flex items-center gap-2 mt-1">
              <Clock className="w-4 h-4 text-cyber-cyan" />
              <span className="text-xl font-bold text-white">
                {formatSecs(summary.total_duration_secs)}
              </span>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-cyber-card border border-cyber-border">
            <span className="text-xs text-cyber-muted font-medium">Total Blinks Recorded</span>
            <div className="flex items-center gap-2 mt-1">
              <Activity className="w-4 h-4 text-blue-400" />
              <span className="text-xl font-bold text-white">
                {summary.total_blinks.toLocaleString()}
              </span>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-cyber-card border border-cyber-border">
            <span className="text-xs text-cyber-muted font-medium">Average Blink Rate</span>
            <div className="flex items-center gap-2 mt-1">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span className="text-xl font-bold text-white">
                {summary.overall_avg_blink_rate.toFixed(1)}{' '}
                <span className="text-xs text-cyber-muted font-normal">BPM</span>
              </span>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-cyber-card border border-cyber-border">
            <span className="text-xs text-cyber-muted font-medium">Average Fatigue Score</span>
            <div className="flex items-center gap-2 mt-1">
              <Zap className="w-4 h-4 text-amber-400" />
              <span className="text-xl font-bold text-white">
                {summary.overall_avg_fatigue_score.toFixed(0)}{' '}
                <span className="text-xs text-cyber-muted font-normal">/ 100</span>
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Interactive Charts */}
      {sessions.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Blink Rate & Fatigue Trend */}
          <div className="p-5 rounded-2xl bg-cyber-card border border-cyber-border">
            <h3 className="text-sm font-bold text-white mb-4">
              Blink Rate & Fatigue Trends Across Sessions
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="rateColor" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00F5FF" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#00F5FF" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="fatigueColor" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis dataKey="session" stroke="#64748B" fontSize={11} />
                  <YAxis stroke="#64748B" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#121722',
                      borderColor: '#1E293B',
                      borderRadius: '0.75rem',
                      color: '#fff',
                    }}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="blink_rate"
                    name="Blink Rate (BPM)"
                    stroke="#00F5FF"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#rateColor)"
                  />
                  <Area
                    type="monotone"
                    dataKey="fatigue_score"
                    name="Fatigue (0-100)"
                    stroke="#F59E0B"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#fatigueColor)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Session Duration & Blinks */}
          <div className="p-5 rounded-2xl bg-cyber-card border border-cyber-border">
            <h3 className="text-sm font-bold text-white mb-4">
              Total Blinks per Session
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis dataKey="session" stroke="#64748B" fontSize={11} />
                  <YAxis stroke="#64748B" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#121722',
                      borderColor: '#1E293B',
                      borderRadius: '0.75rem',
                      color: '#fff',
                    }}
                  />
                  <Legend />
                  <Bar
                    dataKey="blinks"
                    name="Total Blinks"
                    fill="#3B82F6"
                    radius={[6, 6, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      ) : (
        <div className="p-12 text-center rounded-2xl bg-cyber-card border border-cyber-border">
          <History className="w-12 h-12 text-cyber-muted mx-auto mb-3 opacity-40" />
          <h3 className="text-base font-semibold text-white">No Sessions Logged Yet</h3>
          <p className="text-xs text-cyber-muted mt-1 max-w-sm mx-auto">
            Start a monitoring session on the Live Dashboard. When you stop, your session analytics will be displayed here automatically.
          </p>
        </div>
      )}

      {/* Session Log Table */}
      {sessions.length > 0 && (
        <div className="rounded-2xl bg-cyber-card border border-cyber-border overflow-hidden">
          <div className="p-4 border-b border-cyber-border">
            <h3 className="text-sm font-bold text-white">Session Log History</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-cyber-cardHover text-cyber-muted uppercase tracking-wider font-semibold border-b border-cyber-border">
                <tr>
                  <th className="px-4 py-3">Date / Time</th>
                  <th className="px-4 py-3">Duration</th>
                  <th className="px-4 py-3">Total Blinks</th>
                  <th className="px-4 py-3">Avg Rate</th>
                  <th className="px-4 py-3">Fatigue Score</th>
                  <th className="px-4 py-3">Avg Duration</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cyber-border text-cyber-text">
                {sessions.map((s) => (
                  <tr key={s.id} className="hover:bg-cyber-cardHover/50 transition-colors">
                    <td className="px-4 py-3 font-mono">
                      {new Date(s.start_time).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 font-mono">{formatSecs(s.duration_secs)}</td>
                    <td className="px-4 py-3 font-bold text-white">{s.total_blinks}</td>
                    <td className="px-4 py-3 font-mono text-cyber-cyan">
                      {s.avg_blink_rate.toFixed(1)} bpm
                    </td>
                    <td className="px-4 py-3 font-mono">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[11px] font-bold ${
                          s.avg_fatigue_score > 70
                            ? 'bg-rose-500/20 text-rose-400'
                            : s.avg_fatigue_score > 35
                            ? 'bg-amber-500/20 text-amber-400'
                            : 'bg-emerald-500/20 text-emerald-400'
                        }`}
                      >
                        {s.avg_fatigue_score.toFixed(0)}/100
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono">{s.avg_blink_duration_ms.toFixed(0)} ms</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleDelete(s.id)}
                        className="p-1.5 rounded-lg text-cyber-muted hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                        title="Delete Session"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
