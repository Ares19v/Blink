import React, { useState, useEffect } from 'react';
import { X, Sparkles, CheckCircle2, Eye, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import type { CalibrationStatus } from '../types';

interface CalibrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCalibrationComplete: () => void;
}

export const CalibrationModal: React.FC<CalibrationModalProps> = ({
  isOpen,
  onClose,
  onCalibrationComplete,
}) => {
  const [calibrating, setCalibrating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<CalibrationStatus | null>(null);
  const [completedThreshold, setCompletedThreshold] = useState<number | null>(null);

  useEffect(() => {
    let interval: any = null;

    if (calibrating) {
      interval = setInterval(async () => {
        try {
          const st = await api.getCalibrationStatus();
          setStatus(st);
          setProgress(st.progress);

          if (!st.calibrating && st.progress >= 100) {
            setCalibrating(false);
            setCompletedThreshold(st.ear_threshold);
            onCalibrationComplete();
          }
        } catch (e) {
          console.error(e);
        }
      }, 300);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [calibrating, onCalibrationComplete]);

  if (!isOpen) return null;

  const handleStart = async () => {
    setCompletedThreshold(null);
    setProgress(0);
    setCalibrating(true);
    try {
      await api.startCalibration();
    } catch (e) {
      console.error(e);
      setCalibrating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="bg-cyber-card border border-cyber-border rounded-2xl max-w-md w-full p-6 shadow-2xl relative overflow-hidden">
        {/* Decorative Top Accent */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 via-blue-500 to-indigo-500" />

        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-cyber-cyan/10 border border-cyber-cyan/30 text-cyber-cyan">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">EAR Baseline Calibration</h3>
              <p className="text-xs text-cyber-muted">Personalize Eye Aspect Ratio</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-cyber-muted hover:text-white p-1 rounded-lg hover:bg-cyber-cardHover transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        {!calibrating && completedThreshold === null && (
          <div className="space-y-4">
            <div className="rounded-xl bg-cyber-cardHover border border-cyber-border p-4 text-xs text-cyber-text space-y-2">
              <p className="font-semibold text-white">How it works:</p>
              <ul className="list-disc list-inside space-y-1 text-cyber-muted">
                <li>Look directly at the webcam at normal viewing distance.</li>
                <li>Keep your eyes open naturally for 7 seconds.</li>
                <li>Blink calculates your personal resting Eye Aspect Ratio (EAR).</li>
              </ul>
            </div>

            <button
              onClick={handleStart}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-cyber-cyan text-black font-bold text-sm hover:brightness-110 shadow-lg shadow-cyber-cyan/20 active:scale-95 transition-all"
            >
              <Eye className="w-4 h-4" />
              Begin 7-Second Calibration
            </button>
          </div>
        )}

        {/* In Progress */}
        {calibrating && (
          <div className="py-6 text-center space-y-4">
            <div className="relative w-24 h-24 mx-auto flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90">
                <circle
                  cx="48"
                  cy="48"
                  r="40"
                  stroke="#1E293B"
                  strokeWidth="8"
                  fill="transparent"
                />
                <circle
                  cx="48"
                  cy="48"
                  r="40"
                  stroke="#00F5FF"
                  strokeWidth="8"
                  strokeDasharray="251.2"
                  strokeDashoffset={251.2 - (251.2 * progress) / 100}
                  strokeLinecap="round"
                  fill="transparent"
                  className="transition-all duration-300"
                />
              </svg>
              <div className="absolute flex flex-col items-center">
                <span className="text-2xl font-extrabold text-white">{progress}%</span>
              </div>
            </div>

            <div>
              <p className="text-sm font-semibold text-white">Analyzing Eye Geometry...</p>
              <p className="text-xs text-cyber-muted mt-1">
                Samples gathered: {status?.samples_count || 0} frames
              </p>
            </div>
          </div>
        )}

        {/* Completed */}
        {completedThreshold !== null && (
          <div className="py-4 text-center space-y-4">
            <div className="w-14 h-14 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 mx-auto flex items-center justify-center">
              <CheckCircle2 className="w-8 h-8" />
            </div>

            <div>
              <h4 className="text-base font-bold text-white">Calibration Complete!</h4>
              <p className="text-xs text-cyber-muted mt-1">
                New EAR threshold established:
              </p>
              <div className="inline-block mt-3 px-4 py-1.5 rounded-xl bg-cyber-cardHover border border-cyber-cyan/30 text-cyber-cyan font-mono font-bold text-lg">
                {completedThreshold.toFixed(3)}
              </div>
            </div>

            <div className="flex gap-2 pt-2">
              <button
                onClick={handleStart}
                className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl bg-cyber-cardHover border border-cyber-border text-xs text-white hover:border-cyber-cyan/40 transition-all"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Recalibrate
              </button>
              <button
                onClick={onClose}
                className="flex-1 py-2.5 rounded-xl bg-cyber-cyan text-black font-bold text-xs hover:brightness-110 shadow-lg shadow-cyber-cyan/20 transition-all"
              >
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
