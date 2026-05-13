<div align="center">
  <h1>Blink 👁️</h1>
  <p><b>Advanced Eye Health Monitor & Fatigue Tracker</b></p>
  
  <a href="https://github.com/Ares19v/Blink/actions/workflows/ci.yml">
    <img src="https://github.com/Ares19v/Blink/actions/workflows/ci.yml/badge.svg" alt="CI/CD Build Status">
  </a>
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</div>

---

Blink is a locally-processed, privacy-first desktop application that monitors your blink rate via webcam to prevent digital eye strain. It uses computer vision (MediaPipe) to track your Eye Aspect Ratio (EAR) and nudges you when your eyes need a break.

## ✨ Features

- **Adaptive Calibration**: Automatically measures your unique resting eye aspect ratio on startup to ensure accurate tracking for every face shape.
- **Blink Duration Analysis**: Tracks not just how often you blink, but *how long* each blink lasts (detecting incomplete/partial blinks).
- **Fatigue Score Engine**: Calculates a real-time Eye Fatigue Score (0-100) combining your blink rate, duration, and EAR variance.
- **20-20-20 Rule Timer**: Built-in break reminders to look 20 feet away for 20 seconds every 20 minutes.
- **Session History & Analytics**: All data is persisted locally in SQLite, visualized via built-in Matplotlib history charts.
- **Smart Notifications**: Non-intrusive OS toast notifications with configurable audio cues.
- **Customizable**: Tweak settings via a dedicated UI panel (or directly via `config.json`).
- **Privacy First**: 100% local processing. No internet connection required after the initial model download.

## 🚀 Quick Start (Windows)

We provide one-click scripts for Windows users:

1. **Clone the repository**:
   ```cmd
   git clone https://github.com/Ares19v/Blink.git
   cd Blink
   ```
2. **Install**: Double-click `INSTALL.bat`. This will install dependencies and create a desktop shortcut.
3. **Run**: Double-click `Run_Project.bat` (or use the desktop shortcut).

## 🛠️ Manual Installation & Development

```bash
# Create a virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

## 🐳 Docker (CI/CD & Headless Testing)

While Blink is a desktop GUI application (which requires direct webcam access and a display), we provide a Docker setup for automated headless testing and CI/CD validation.

```bash
docker-compose up --build
```
This will build the image, install dependencies, and run the `pytest` suite in an isolated container.

## 🧪 Running Tests

The core logic (EAR calculation, state machines, and statistics) is fully decoupled from the GUI and covered by Pytest.

```bash
pytest tests/ -v
```

## 🏗️ Building an Executable

You can easily compile Blink into a single `.exe` file using PyInstaller:

```cmd
build.bat
```
The standalone executable will be located in the `dist/` folder.

## 📄 License
MIT License.
