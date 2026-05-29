# EVAL — Blink

> **Evaluation Date:** 2026-05-29  
> **Evaluator:** Automated Portfolio Review  
> **Maturity Level:** Production-Ready

---

## 1. Project Purpose & Problem Statement

Digital eye strain is a well-documented occupational health concern for knowledge workers who spend extended hours at screens. Reduced blink rate (normal: 15–20 bpm; screen use: often drops to 3–5 bpm) causes dry eyes, fatigue, and long-term discomfort. Blink is a locally-processed, privacy-first desktop application that monitors blink rate via webcam using computer vision, calculates a composite fatigue score in real time, and delivers actionable nudges before strain sets in.

Unlike cloud-dependent wellness apps, Blink processes all video locally — no frames or biometric data leave the machine. The target user is any developer, writer, or office worker who wants a passive health monitor without surveillance tradeoffs.

---

## 2. Technical Architecture

Blink is a multi-threaded Python desktop application with strict thread isolation to keep the PyQt6 UI responsive during 30 FPS computer vision inference.

**Thread 0 — Main Event Loop (PyQt6):** The `MainWindow` hosts the UI, manages `BlinkMonitor` (a rolling-window state machine), and persists session statistics to SQLite via `database.py`.

**Thread 1 — Camera & CV (QThread):** `CameraThread` polls `cv2.VideoCapture` continuously. Each frame is passed to `BlinkDetector`, which runs the MediaPipe Tasks API (FaceLandmarker model). A `pyqtSignal` safely transmits a 5-tuple `(frame, blink_bool, ear_float, face_bool, duration_ms)` across the thread boundary without locking.

**Daemon Thread — Notifications:** Asynchronous OS-level toast notifications and audio alerts (beep) are dispatched from daemon threads to avoid stalling the video pipeline.

**Computer Vision Logic:** Eye Aspect Ratio (EAR) computed from 6 MediaPipe facial landmarks per eye (Soukupová & Cech, 2016). EAR drops below the user's calibrated threshold for 2+ consecutive frames ? blink registered. Adaptive calibration runs for 7 seconds at startup to account for individual facial geometry variation.

**Fatigue Score Heuristic (0–100):** A weighted composite computed over a 60-second rolling `deque`:
- 40% blink rate penalty (optimal >12 bpm)
- 40% blink duration penalty (optimal >100ms)
- 20% EAR variance penalty (high variance = squinting/heavy eyelids)

**20-20-20 Rule:** Built-in timer fires every 20 minutes with a distinct double-beep audio cue.

**Distribution:** PyInstaller compiles Blink into a standalone `.exe` via `build.bat`, eliminating the Python runtime requirement for end users.

---

## 3. Strengths

- **Rigorous multithreaded architecture:** `QThread` + `pyqtSignal` for thread-safe cross-boundary communication is the correct PyQt6 pattern. Daemon threads for notifications are correctly implemented to avoid UI blocking.
- **Adaptive EAR calibration:** Personalized per-session baseline rather than a hardcoded threshold — properly accounts for face variation.
- **Composite fatigue score is multi-dimensional:** Synthesizing blink rate, duration, and EAR variance rather than a single metric reduces false positives.
- **Privacy-first design:** Explicit documentation that no video or biometrics are transmitted; processing is entirely local.
- **SQLite session persistence + Matplotlib analytics:** Historical trend visualization across sessions adds longitudinal value.
- **Pytest unit tests:** Decoupled unit tests for mathematical/logic layers exist in `tests/`.
- **CI/CD + headless testing via Docker:** Dockerfile uses `xvfb` for X11 simulation in CI — correctly handles the PyQt6/webcam headless challenge.
- **PyInstaller distribution:** One-click `.exe` deployment is appropriate for the non-developer target user.

---

## 4. Limitations & Known Gaps

- **MediaPipe accuracy degrades in low light:** No adaptive lighting detection or fallback for poor webcam conditions.
- **Single-camera assumption:** No support for external webcams or camera selection; defaults to index 0.
- **EAR threshold calibration is session-only:** The calibrated baseline is not persisted across sessions, requiring a 7-second re-calibration every launch.
- **Fatigue score weights are empirical/hardcoded:** The 40/40/20 weighting has no documented physiological basis or user study validation.
- **No cross-platform support:** The README targets Windows. The PyQt6 framework is cross-platform but the distribution `.exe` and `.bat` scripts are Windows-only.
- **Limited test coverage scope:** Tests cover mathematical/logic layers; no tests for the CV pipeline, database layer, or GUI components.
- **No remote monitoring or reporting:** Sessions are local-only; no export to PDF/CSV for sharing with occupational health providers.

---

## 5. Code Quality Assessment

The codebase follows clean separation: `core/` for CV logic, `gui/` for the PyQt6 window, `models/` for MediaPipe assets. The multithreaded architecture is correctly implemented and documented in the README with a Mermaid diagram showing data flow clearly.

**Documentation:** Excellent — includes EAR formula with LaTeX notation, fatigue score breakdown, Mermaid architecture diagram, and the science section explaining the computer vision approach.

**Testing:** Pytest tests for mathematical layers exist; headless CI with Docker xvfb is a sophisticated solution for a GUI application.

**Linting:** Flake8 + Black configured in CI.

**Distribution:** PyInstaller `.exe` build is present and documented.

---

## 6. Maturity Breakdown

| Dimension | Score | Notes |
|-----------|-------|-------|
| Functionality | 8/10 | Core detection, fatigue scoring, and alerts work; limitations in edge conditions |
| Code Quality | 8/10 | Proper threading, clean separation, Pytest coverage on core logic |
| Documentation | 9/10 | Science explained, architecture diagrammed, EAR formula documented |
| Scalability | 4/10 | Single-user local desktop app by design; no server-side components |
| Security | 9/10 | No network transmission; entirely local processing |
| **Overall** | **7.6/10** | **Solid production-grade Python desktop app with real CV science** |

---

## 7. Suggested Next Steps

1. **Persist calibrated EAR threshold across sessions** in `config.json` to eliminate the mandatory 7-second re-calibration on every launch.
2. **Add low-light detection and notification** using the webcam's average luminance, prompting users to improve lighting before calibration degrades.
3. **Expand test coverage** to include the `BlinkDetector` logic layer with mocked MediaPipe output, and add a session data export feature (CSV/PDF) for health record sharing.

---

## 8. Verdict

Blink is a well-engineered, privacy-respecting health monitoring application that demonstrates real competence in Python multithreading, computer vision integration, and PyQt6 GUI development. The EAR-based blink detection with per-session adaptive calibration is scientifically grounded, and the multithreaded architecture correctly avoids the common mistake of blocking the UI thread with CV inference. The main practical gaps are the re-calibration requirement on every launch and the absence of low-light handling — both very solvable — rather than any fundamental architectural shortcomings.
