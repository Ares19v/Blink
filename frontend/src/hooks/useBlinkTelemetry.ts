import React, { useEffect, useRef, useState } from 'react';
import type { BlinkTelemetry } from '../types';

const INITIAL_TELEMETRY: BlinkTelemetry = {
  is_monitoring: false,
  is_running: false,
  face_detected: false,
  ear: 0.0,
  ear_threshold: 0.21,
  blink_detected: false,
  blink_duration_ms: 0,
  blink_rate: null,
  fatigue_score: null,
  total_blinks: 0,
  session_duration_sec: 0,
  twenty_countdown_sec: 0,
  calibrating: false,
  calibration_progress: 0,
};

export function useBlinkTelemetry(videoRef?: React.RefObject<HTMLImageElement | null>) {
  const [telemetry, setTelemetry] = useState<BlinkTelemetry>(INITIAL_TELEMETRY);
  const [connected, setConnected] = useState(false);
  const [blinkTrigger, setBlinkTrigger] = useState(false);
  const [fps, setFps] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);
  const lastFrameTime = useRef<number>(Date.now());
  const frameCount = useRef<number>(0);
  const fpsTimer = useRef<number>(Date.now());
  const lastStateUpdate = useRef<number>(Date.now());
  const pendingImageRef = useRef<string>('');
  const rafId = useRef<number | null>(null);

  useEffect(() => {
    let unmounted = false;

    // Dedicated animation frame renderer for maximum fluidity
    function renderFrame() {
      if (videoRef?.current && pendingImageRef.current) {
        videoRef.current.src = pendingImageRef.current;
      }
      if (!unmounted) {
        rafId.current = requestAnimationFrame(renderFrame);
      }
    }
    rafId.current = requestAnimationFrame(renderFrame);

    function connect() {
      if (unmounted) return;

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws/telemetry`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!unmounted) setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const raw = JSON.parse(event.data);
          if (unmounted) return;

          // 1. Direct hardware rendering pipeline (Zero React state overhead)
          if (raw.image) {
            pendingImageRef.current = 'data:image/jpeg;base64,' + raw.image;
          }

          // 2. Accurate rolling FPS counter
          frameCount.current += 1;
          const now = Date.now();
          if (now - fpsTimer.current >= 1000) {
            const calculatedFps = Math.round(
              (frameCount.current * 1000) / (now - fpsTimer.current)
            );
            setFps(calculatedFps);
            frameCount.current = 0;
            fpsTimer.current = now;
          }
          lastFrameTime.current = now;

          // 3. Flash indicator on blink event
          if (raw.blink_detected) {
            setBlinkTrigger(true);
            setTimeout(() => setBlinkTrigger(false), 200);
          }

          // 4. Update React telemetry state without the massive image string
          if (now - lastStateUpdate.current >= 100 || raw.blink_detected) {
            const { image, ...cleanStats } = raw;
            setTelemetry(cleanStats);
            lastStateUpdate.current = now;
          }
        } catch (err) {
          console.error('Failed to parse telemetry message', err);
        }
      };

      ws.onclose = () => {
        if (unmounted) return;
        setConnected(false);
        setFps(0);
        reconnectTimeoutRef.current = setTimeout(connect, 1500);
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      unmounted = true;
      if (rafId.current) cancelAnimationFrame(rafId.current);
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [videoRef]);

  return { telemetry, connected, blinkTrigger, fps };
}
