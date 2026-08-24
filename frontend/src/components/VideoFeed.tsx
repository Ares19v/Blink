import React, { useState } from 'react';
import { Camera, Eye, AlertCircle, ScanFace, Play, Sparkles } from 'lucide-react';
import type { BlinkTelemetry } from '../types';

interface VideoFeedProps {
  telemetry: BlinkTelemetry;
  blinkTrigger: boolean;
  onStart: () => void;
  onCalibrate: () => void;
}

export const VideoFeed: React.FC<VideoFeedProps> = ({
  telemetry,
  blinkTrigger,
  onStart,
  onCalibrate,
}) => {
  const [streamError, setStreamError] = useState(false);

  return (
    <div className="relative rounded-2xl overflow-hidden bg-cyber-card border border-cyber-border shadow-xl flex flex-col items-center justify-center min-h-[380px] lg:min-h-[440px]">
      {telemetry.is_monitoring ? (
        <div className="relative w-full h-full flex items-center justify-center bg-black">
          {/* MJPEG Stream */}
          <img
            src={`/api/video_feed?t=${telemetry.is_monitoring}`}
            alt="Live Camera Video Feed"
            className="w-full h-full object-contain max-h-[500px]"
            onError={() => setStreamError(true)}
            onLoad={() => setStreamError(false)}
          />

          {/* HUD Overlay Header */}
          <div className="absolute top-4 left-4 right-4 flex items-center justify-between pointer-events-none">
            {/* Live Indicator */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-black/60 backdrop-blur-md border border-white/10 text-xs font-mono">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
              <span className="text-white font-semibold tracking-wider uppercase">LIVE REC</span>
              <span className="text-cyber-muted">30 FPS</span>
            </div>

            {/* Face Status Pill */}
            <div
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg backdrop-blur-md border text-xs font-mono transition-all ${
                telemetry.face_detected
                  ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-400'
                  : 'bg-amber-950/60 border-amber-500/40 text-amber-400'
              }`}
            >
              <ScanFace className="w-3.5 h-3.5" />
              <span>{telemetry.face_detected ? 'FACE LOCKED' : 'SEARCHING FACE'}</span>
            </div>
          </div>

          {/* Blink Flash / Indicator */}
          <div
            className={`absolute bottom-4 left-4 flex items-center gap-2 px-3 py-1.5 rounded-lg backdrop-blur-md border transition-all ${
              blinkTrigger || telemetry.blink_detected
                ? 'bg-cyan-950/90 border-cyber-cyan text-cyber-cyan scale-110 shadow-lg shadow-cyber-cyan/30'
                : 'bg-black/60 border-white/10 text-cyber-muted'
            }`}
          >
            <Eye className="w-4 h-4" />
            <span className="font-mono text-xs font-bold">
              {blinkTrigger || telemetry.blink_detected ? 'BLINK DETECTED!' : 'EAR MON'}
            </span>
          </div>

          {/* Live EAR Meter on bottom-right */}
          <div className="absolute bottom-4 right-4 px-3 py-1.5 rounded-lg bg-black/70 backdrop-blur-md border border-white/10 text-xs font-mono flex items-center gap-3">
            <span className="text-cyber-muted">EAR:</span>
            <span className="text-cyber-cyan font-bold">{telemetry.ear.toFixed(3)}</span>
            <span className="text-gray-500">/ Thr: {telemetry.ear_threshold.toFixed(3)}</span>
          </div>

          {streamError && (
            <div className="absolute inset-0 bg-black/80 flex flex-col items-center justify-center text-center p-6">
              <AlertCircle className="w-12 h-12 text-rose-500 mb-3" />
              <p className="text-white font-medium">Camera Feed Connection Failed</p>
              <p className="text-xs text-cyber-muted mt-1">
                Ensure your camera is plugged in and permissions are granted.
              </p>
            </div>
          )}
        </div>
      ) : (
        /* Standby State */
        <div className="p-8 text-center flex flex-col items-center justify-center w-full h-full">
          <div className="w-20 h-20 rounded-2xl bg-cyber-cardHover border border-cyber-border flex items-center justify-center text-cyber-cyan/50 mb-5 relative group">
            <Camera className="w-10 h-10 group-hover:text-cyber-cyan transition-colors" />
            <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-cyan-500/20 to-blue-500/20 blur opacity-75" />
          </div>

          <h3 className="text-lg font-semibold text-white mb-2">Camera Feed Standby</h3>
          <p className="text-sm text-cyber-muted max-w-md mb-6">
            Start monitoring to initiate real-time facial landmark tracking and Eye Aspect Ratio (EAR) fatigue scoring.
          </p>

          <div className="flex flex-wrap items-center gap-3 justify-center">
            <button
              onClick={onStart}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-cyber-cyan text-black font-bold text-sm hover:brightness-110 shadow-lg shadow-cyber-cyan/20 active:scale-95 transition-all"
            >
              <Play className="w-4 h-4 fill-black" />
              Start Monitoring
            </button>
            <button
              onClick={onCalibrate}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyber-cardHover border border-cyber-border text-white text-sm hover:border-cyber-cyan/40 hover:text-cyber-cyan transition-all"
            >
              <Sparkles className="w-4 h-4 text-cyber-cyan" />
              Run 7s Calibration
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
