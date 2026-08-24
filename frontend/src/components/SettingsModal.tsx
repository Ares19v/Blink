import React, { useState, useEffect } from 'react';
import { X, Settings, Save, Check, Volume2, Clock, Camera, Sliders } from 'lucide-react';
import { api } from '../services/api';
import type { AppSettings } from '../types';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSettingsSaved: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  onSettingsSaved,
}) => {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      api.getSettings().then((s) => setSettings(s)).catch(console.error);
    }
  }, [isOpen]);

  if (!isOpen || !settings) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.updateSettings(settings);
      setSavedSuccess(true);
      onSettingsSaved();
      setTimeout(() => {
        setSavedSuccess(false);
        onClose();
      }, 800);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-cyber-card border border-cyber-border rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-cyber-cardHover text-cyber-cyan border border-cyber-border">
              <Settings className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Application Settings</h3>
              <p className="text-xs text-cyber-muted">Thresholds & Notification Preferences</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-cyber-muted hover:text-white p-1 rounded-lg hover:bg-cyber-cardHover transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          {/* Blink Rate Threshold */}
          <div className="p-3.5 rounded-xl bg-cyber-cardHover border border-cyber-border">
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-white flex items-center gap-2">
                <Sliders className="w-3.5 h-3.5 text-cyber-cyan" />
                Low Blink Rate Alert (BPM)
              </label>
              <span className="text-xs font-mono text-cyber-cyan font-bold">
                {settings.blink_rate_threshold} bpm
              </span>
            </div>
            <input
              type="range"
              min="5"
              max="25"
              step="1"
              value={settings.blink_rate_threshold}
              onChange={(e) =>
                setSettings({ ...settings, blink_rate_threshold: parseFloat(e.target.value) })
              }
              className="w-full accent-cyber-cyan cursor-pointer"
            />
            <p className="text-[11px] text-cyber-muted mt-1">
              Triggers a notification if your rolling rate drops below this value.
            </p>
          </div>

          {/* EAR Threshold */}
          <div className="p-3.5 rounded-xl bg-cyber-cardHover border border-cyber-border">
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-white flex items-center gap-2">
                <Sliders className="w-3.5 h-3.5 text-cyber-cyan" />
                EAR Blink Sensitivity
              </label>
              <span className="text-xs font-mono text-cyber-cyan font-bold">
                {settings.ear_threshold.toFixed(3)}
              </span>
            </div>
            <input
              type="range"
              min="0.10"
              max="0.35"
              step="0.005"
              value={settings.ear_threshold}
              onChange={(e) =>
                setSettings({ ...settings, ear_threshold: parseFloat(e.target.value) })
              }
              className="w-full accent-cyber-cyan cursor-pointer"
            />
            <p className="text-[11px] text-cyber-muted mt-1">
              Eye Aspect Ratio threshold to register a blink (normally 0.20 - 0.32).
            </p>
          </div>

          {/* Notification Cooldown */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3.5 rounded-xl bg-cyber-cardHover border border-cyber-border">
              <label className="text-xs font-semibold text-white flex items-center gap-2 mb-1.5">
                <Clock className="w-3.5 h-3.5 text-blue-400" />
                Alert Cooldown (sec)
              </label>
              <input
                type="number"
                min="10"
                max="600"
                value={settings.notification_cooldown}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    notification_cooldown: parseInt(e.target.value) || 90,
                  })
                }
                className="w-full px-3 py-1.5 rounded-lg bg-cyber-bg border border-cyber-border text-white text-xs font-mono focus:border-cyber-cyan focus:outline-none"
              />
            </div>

            <div className="p-3.5 rounded-xl bg-cyber-cardHover border border-cyber-border">
              <label className="text-xs font-semibold text-white flex items-center gap-2 mb-1.5">
                <Camera className="w-3.5 h-3.5 text-emerald-400" />
                Camera Device Index
              </label>
              <input
                type="number"
                min="0"
                max="5"
                value={settings.camera_index}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    camera_index: parseInt(e.target.value) || 0,
                  })
                }
                className="w-full px-3 py-1.5 rounded-lg bg-cyber-bg border border-cyber-border text-white text-xs font-mono focus:border-cyber-cyan focus:outline-none"
              />
            </div>
          </div>

          {/* Toggles */}
          <div className="grid grid-cols-2 gap-3 pt-1">
            <label className="flex items-center gap-3 p-3 rounded-xl bg-cyber-cardHover border border-cyber-border cursor-pointer hover:border-cyber-border/80">
              <input
                type="checkbox"
                checked={settings.twenty_twenty_twenty_enabled}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    twenty_twenty_twenty_enabled: e.target.checked,
                  })
                }
                className="w-4 h-4 accent-cyber-cyan rounded cursor-pointer"
              />
              <div className="text-xs">
                <p className="font-semibold text-white">20-20-20 Rule</p>
                <p className="text-[10px] text-cyber-muted">Periodic eye break reminder</p>
              </div>
            </label>

            <label className="flex items-center gap-3 p-3 rounded-xl bg-cyber-cardHover border border-cyber-border cursor-pointer hover:border-cyber-border/80">
              <input
                type="checkbox"
                checked={settings.sound_enabled}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    sound_enabled: e.target.checked,
                  })
                }
                className="w-4 h-4 accent-cyber-cyan rounded cursor-pointer"
              />
              <div className="text-xs">
                <p className="font-semibold text-white flex items-center gap-1.5">
                  <Volume2 className="w-3.5 h-3.5 text-cyber-cyan" />
                  Audio Alerts
                </p>
                <p className="text-[10px] text-cyber-muted">Sound beeps on nudges</p>
              </div>
            </label>
          </div>

          {/* Actions */}
          <div className="flex gap-2 pt-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-xl bg-cyber-cardHover border border-cyber-border text-xs text-white hover:bg-cyber-card transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-cyber-cyan text-black font-bold text-xs hover:brightness-110 shadow-lg shadow-cyber-cyan/20 active:scale-95 transition-all"
            >
              {savedSuccess ? (
                <>
                  <Check className="w-4 h-4" />
                  Saved!
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Save Settings
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
