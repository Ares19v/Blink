import { useState, useRef } from 'react';
import { useBlinkTelemetry } from './hooks/useBlinkTelemetry';
import { api } from './services/api';
import { CalibrationModal } from './components/CalibrationModal';
import { SettingsModal } from './components/SettingsModal';
import { HistoryView } from './components/HistoryView';
import { Camera, X, Play, Square, Settings, BarChart2, Sparkles, Activity } from 'lucide-react';

export function App() {
  const [isCalibrationOpen, setIsCalibrationOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  const videoRef = useRef<HTMLImageElement | null>(null);
  const { telemetry, connected, blinkTrigger, fps } = useBlinkTelemetry(videoRef);

  const handleToggle = async () => {
    try {
      if (telemetry.is_monitoring) {
        await api.stopMonitoring();
      } else {
        await api.startMonitoring();
      }
    } catch (err) {
      console.error('Failed to toggle monitoring', err);
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const getStatusText = () => {
    if (telemetry.calibrating) return '● Calibration in progress (7s)...';
    if (!telemetry.is_monitoring) return '● Not monitoring';
    if (!telemetry.face_detected) return '● Searching for face...';
    if (blinkTrigger || telemetry.blink_detected) return '● BLINK DETECTED!';
    return `● Monitoring — ${fps > 0 ? fps : 30} fps`;
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-[#e0e0e0] font-sans flex flex-col justify-between p-4 md:p-6 selection:bg-[#00f5ff] selection:text-black">
      {/* Top Banner / Sync Indicator */}
      <div className="max-w-[1280px] w-full mx-auto flex items-center justify-between pb-3 text-xs border-b border-[#1a1a1a]">
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              connected ? 'bg-[#00f5ff] animate-pulse' : 'bg-red-500'
            }`}
          />
          <span className="text-[#555555] font-mono tracking-wider">
            {connected ? 'HIGH-SPEED STREAM ACTIVE' : 'SERVER OFFLINE'}
          </span>
        </div>
        <div className="flex items-center gap-4 text-[#555555] font-mono text-[11px]">
          {telemetry.is_monitoring && (
            <span className="flex items-center gap-1 text-[#00f5ff]">
              <Activity className="w-3 h-3" />
              {fps} FPS
            </span>
          )}
          <span>BLINK v2.0 FASTAPI + REACT</span>
        </div>
      </div>

      {/* Main 2-Panel Application Window */}
      <main className="max-w-[1280px] w-full mx-auto my-auto py-4 grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        {/* ========================================================= */}
        {/* LEFT PANEL: Camera Feed (stretch 8 cols)                 */}
        {/* ========================================================= */}
        <section className="lg:col-span-8 bg-[#0f0f0f] border border-[#1a1a1a] rounded-lg p-3 flex flex-col justify-between shadow-xl min-h-[500px]">
          {/* Camera Viewport Area */}
          <div className="relative w-full flex-1 bg-[#080808] rounded-md overflow-hidden flex items-center justify-center border border-[#161616] min-h-[420px]">
            {/* Live Video Frame (Direct Ref for Zero Lag) */}
            <img
              ref={videoRef}
              alt="Blink Camera Feed"
              className={`w-full h-full object-contain max-h-[560px] ${
                telemetry.is_monitoring ? 'block' : 'hidden'
              }`}
            />

            {!telemetry.is_monitoring && (
              <div className="text-center p-8 space-y-3">
                <Camera className="w-12 h-12 text-[#2a2a2a] mx-auto" />
                <p className="text-sm text-[#444444] font-medium leading-relaxed">
                  Camera feed will appear here
                  <br />
                  once monitoring starts.
                </p>
              </div>
            )}

            {/* Flash Indicator on Blink */}
            {telemetry.is_monitoring && (blinkTrigger || telemetry.blink_detected) && (
              <div className="absolute top-4 left-4 px-3 py-1 bg-[#00f5ff] text-black font-bold text-xs tracking-wider rounded font-mono shadow-lg shadow-[#00f5ff]/40 animate-pulse">
                BLINK DETECTED
              </div>
            )}

            {/* FPS Badge */}
            {telemetry.is_monitoring && fps > 0 && (
              <div className="absolute top-4 right-4 px-2.5 py-1 bg-black/60 backdrop-blur-md border border-white/10 text-[11px] font-mono text-[#00f5ff] rounded">
                {fps} FPS
              </div>
            )}
          </div>

          {/* Status Label at Bottom of Camera Panel */}
          <div className="pt-3 text-center">
            <p
              className={`text-xs font-mono tracking-wide ${
                telemetry.is_monitoring ? 'text-[#00f5ff]' : 'text-[#555555]'
              }`}
            >
              {getStatusText()}
            </p>
          </div>
        </section>

        {/* ========================================================= */}
        {/* RIGHT PANEL: Stats & Controls (stretch 4 cols)           */}
        {/* ========================================================= */}
        <section className="lg:col-span-4 bg-[#0d0d0d] border border-[#1a1a1a] rounded-lg p-5 flex flex-col justify-between shadow-xl space-y-4">
          {/* Header Branding */}
          <div className="text-center space-y-1">
            <h1 className="text-[#00f5ff] text-3xl font-bold tracking-[6px] font-mono uppercase">
              BLINK
            </h1>
            <p className="text-[#555555] text-[11px] tracking-[2px] uppercase">
              Eye Health Monitor
            </p>
          </div>

          {/* Big Blink Rate Display */}
          <div className="text-center py-1">
            <div className="text-[#00f5ff] text-6xl font-extrabold tracking-tight font-mono">
              {telemetry.blink_rate !== null ? telemetry.blink_rate.toFixed(1) : '--'}
            </div>
            <p className="text-[#555555] text-xs uppercase tracking-[1px] mt-1">blinks / min</p>
          </div>

          {/* Vertical Stat Cards Stack */}
          <div className="space-y-2">
            {/* EAR Value */}
            <div className="bg-[#111111] border border-[#1e1e1e] rounded-md px-3.5 py-2 flex items-center justify-between">
              <span className="text-[#555555] text-[10px] uppercase tracking-[1px] font-semibold">
                EAR VALUE
              </span>
              <span className="text-[#cccccc] text-sm font-mono font-bold">
                {telemetry.ear > 0
                  ? `${telemetry.ear.toFixed(3)} (Thr: ${telemetry.ear_threshold.toFixed(3)})`
                  : '--'}
              </span>
            </div>

            {/* Fatigue Score */}
            <div className="bg-[#111111] border border-[#1e1e1e] rounded-md px-3.5 py-2 flex items-center justify-between">
              <span className="text-[#555555] text-[10px] uppercase tracking-[1px] font-semibold">
                FATIGUE SCORE
              </span>
              <span
                className={`text-sm font-mono font-bold ${
                  telemetry.fatigue_score !== null
                    ? telemetry.fatigue_score > 70
                      ? 'text-red-400'
                      : telemetry.fatigue_score > 35
                      ? 'text-amber-400'
                      : 'text-[#00f5ff]'
                    : 'text-[#cccccc]'
                }`}
              >
                {telemetry.fatigue_score !== null ? `${telemetry.fatigue_score.toFixed(1)} / 100` : '--'}
              </span>
            </div>

            {/* Avg Blink Duration */}
            <div className="bg-[#111111] border border-[#1e1e1e] rounded-md px-3.5 py-2 flex items-center justify-between">
              <span className="text-[#555555] text-[10px] uppercase tracking-[1px] font-semibold">
                AVG BLINK DURATION
              </span>
              <span className="text-[#cccccc] text-sm font-mono font-bold">
                {telemetry.blink_duration_ms > 0
                  ? `${telemetry.blink_duration_ms.toFixed(0)} ms`
                  : '--'}
              </span>
            </div>

            {/* Total Blinks */}
            <div className="bg-[#111111] border border-[#1e1e1e] rounded-md px-3.5 py-2 flex items-center justify-between">
              <span className="text-[#555555] text-[10px] uppercase tracking-[1px] font-semibold">
                TOTAL BLINKS
              </span>
              <span className="text-[#cccccc] text-sm font-mono font-bold">
                {telemetry.total_blinks}
              </span>
            </div>

            {/* Session Time */}
            <div className="bg-[#111111] border border-[#1e1e1e] rounded-md px-3.5 py-2 flex items-center justify-between">
              <span className="text-[#555555] text-[10px] uppercase tracking-[1px] font-semibold">
                SESSION TIME
              </span>
              <span className="text-[#cccccc] text-sm font-mono font-bold">
                {formatTime(telemetry.session_duration_sec)}
              </span>
            </div>

            {/* Face Detection */}
            <div className="bg-[#111111] border border-[#1e1e1e] rounded-md px-3.5 py-2 flex items-center justify-between">
              <span className="text-[#555555] text-[10px] uppercase tracking-[1px] font-semibold">
                FACE
              </span>
              <span
                className={`text-sm font-mono font-bold ${
                  telemetry.face_detected ? 'text-emerald-400' : 'text-[#777777]'
                }`}
              >
                {telemetry.face_detected ? 'Locked' : 'Not detected'}
              </span>
            </div>
          </div>

          {/* 20-20-20 Rule Countdown */}
          <div className="text-center">
            <p className="text-[#888888] text-[11px] font-mono">
              {telemetry.twenty_countdown_sec > 0
                ? `Next 20-20-20 break in ${formatTime(telemetry.twenty_countdown_sec)}`
                : '20-20-20 Timer Active'}
            </p>
          </div>

          {/* Secondary Buttons Row: Settings / History / Recalibrate */}
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="bg-[#111111] text-[#00f5ff] border border-[#00f5ff] hover:bg-[#0d2a2a] rounded px-2 py-2 text-xs font-semibold flex items-center justify-center gap-1 transition-all"
            >
              <Settings className="w-3.5 h-3.5" />
              Settings
            </button>

            <button
              onClick={() => setIsHistoryOpen(true)}
              className="bg-[#111111] text-[#00f5ff] border border-[#00f5ff] hover:bg-[#0d2a2a] rounded px-2 py-2 text-xs font-semibold flex items-center justify-center gap-1 transition-all"
            >
              <BarChart2 className="w-3.5 h-3.5" />
              History
            </button>

            <button
              onClick={() => setIsCalibrationOpen(true)}
              className="bg-[#111111] text-[#00f5ff] border border-[#00f5ff] hover:bg-[#0d2a2a] rounded px-2 py-2 text-xs font-semibold flex items-center justify-center gap-1 transition-all"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Recalibrate
            </button>
          </div>

          {/* Giant Primary Toggle Button */}
          <div>
            <button
              onClick={handleToggle}
              className={`w-full py-3.5 px-5 rounded font-bold text-sm tracking-wider uppercase flex items-center justify-center gap-2 transition-all ${
                telemetry.is_monitoring
                  ? 'bg-[#1a1a1a] text-[#ff5555] border border-[#ff5555] hover:bg-[#2a0a0a]'
                  : 'bg-[#00f5ff] text-black hover:bg-[#33f7ff] active:bg-[#00c8d4]'
              }`}
            >
              {telemetry.is_monitoring ? (
                <>
                  <Square className="w-4 h-4 fill-current" />
                  Stop Monitoring
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  Start Monitoring
                </>
              )}
            </button>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="max-w-[1280px] w-full mx-auto pt-3 text-center text-[11px] text-[#444444] border-t border-[#1a1a1a] font-mono">
        Blink Eye Health Monitor &copy; {new Date().getFullYear()} — FastAPI + Uvicorn + React + Vite
      </footer>

      {/* History Modal / Drawer */}
      {isHistoryOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#0f0f0f] border border-[#1a1a1a] rounded-xl max-w-4xl w-full p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setIsHistoryOpen(false)}
              className="absolute top-4 right-4 text-[#555555] hover:text-white p-1 rounded transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            <HistoryView />
          </div>
        </div>
      )}

      {/* Calibration Modal */}
      <CalibrationModal
        isOpen={isCalibrationOpen}
        onClose={() => setIsCalibrationOpen(false)}
        onCalibrationComplete={() => {}}
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onSettingsSaved={() => {}}
      />
    </div>
  );
}

export default App;
