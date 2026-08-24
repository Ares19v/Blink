import type { AppSettings, CalibrationStatus, DatabaseSummary, SessionRecord } from '../types';

const API_BASE = '/api';

export const api = {
  // Monitoring
  async startMonitoring(cameraIndex = 0): Promise<{ status: string; running: boolean }> {
    const res = await fetch(`${API_BASE}/monitoring/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ camera_index: cameraIndex }),
    });
    if (!res.ok) throw new Error('Failed to start monitoring');
    return res.json();
  },

  async stopMonitoring(): Promise<{ status: string; running: boolean; summary: any }> {
    const res = await fetch(`${API_BASE}/monitoring/stop`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to stop monitoring');
    return res.json();
  },

  async getMonitoringStatus(): Promise<{ running: boolean; stats: any }> {
    const res = await fetch(`${API_BASE}/monitoring/status`);
    if (!res.ok) throw new Error('Failed to get monitoring status');
    return res.json();
  },

  // Calibration
  async startCalibration(): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE}/calibration/start`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to start calibration');
    return res.json();
  },

  async stopCalibration(): Promise<{ status: string; ear_threshold: number }> {
    const res = await fetch(`${API_BASE}/calibration/stop`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to stop calibration');
    return res.json();
  },

  async getCalibrationStatus(): Promise<CalibrationStatus> {
    const res = await fetch(`${API_BASE}/calibration/status`);
    if (!res.ok) throw new Error('Failed to get calibration status');
    return res.json();
  },

  // Settings
  async getSettings(): Promise<AppSettings> {
    const res = await fetch(`${API_BASE}/settings`);
    if (!res.ok) throw new Error('Failed to load settings');
    return res.json();
  },

  async updateSettings(settings: AppSettings): Promise<{ status: string; settings: AppSettings }> {
    const res = await fetch(`${API_BASE}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!res.ok) throw new Error('Failed to update settings');
    return res.json();
  },

  // History & Analytics
  async getHistory(limit = 100): Promise<SessionRecord[]> {
    const res = await fetch(`${API_BASE}/history?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to load history');
    return res.json();
  },

  async deleteSession(id: number): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE}/history/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete session');
    return res.json();
  },

  async clearHistory(): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE}/history`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to clear history');
    return res.json();
  },

  async getSummary(): Promise<DatabaseSummary> {
    const res = await fetch(`${API_BASE}/history/summary`);
    if (!res.ok) throw new Error('Failed to load summary statistics');
    return res.json();
  },
};
