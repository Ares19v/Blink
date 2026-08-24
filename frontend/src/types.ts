export interface BlinkTelemetry {
  is_monitoring: boolean;
  is_running?: boolean;
  face_detected: boolean;
  ear: number;
  ear_threshold: number;
  blink_detected: boolean;
  blink_duration_ms: number;
  blink_rate: number | null;
  fatigue_score: number | null;
  total_blinks: number;
  session_duration_sec: number;
  twenty_countdown_sec: number;
  calibrating: boolean;
  calibration_progress: number;
  image?: string;
}


export interface AppSettings {
  camera_index: number;
  blink_rate_threshold: number;
  notification_cooldown: number;
  ear_threshold: number;
  twenty_twenty_twenty_enabled: boolean;
  twenty_twenty_twenty_interval_sec: number;
  sound_enabled: boolean;
  calibrated: boolean;
}

export interface SessionRecord {
  id: number;
  start_time: string;
  end_time: string;
  duration_secs: number;
  total_blinks: number;
  avg_blink_rate: number;
  avg_fatigue_score: number;
  avg_blink_duration_ms: number;
  ear_threshold: number;
}

export interface DatabaseSummary {
  total_sessions: number;
  total_duration_secs: number;
  total_blinks: number;
  overall_avg_blink_rate: number;
  overall_avg_fatigue_score: number;
}

export interface CalibrationStatus {
  calibrating: boolean;
  progress: number;
  ear_threshold: number;
  samples_count: number;
  current_mean?: number;
}
