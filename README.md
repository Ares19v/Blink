# Blink — Eye Health Monitor

Blink is a Python desktop application that monitors your blink rate via webcam and sends OS-level notifications when your blinking drops below a healthy threshold.

## 🚀 Features
- **Real-time Blink Detection**: Uses MediaPipe FaceLandmarker and Eye Aspect Ratio (EAR) for high-accuracy tracking.
- **Blink Rate Monitoring**: Maintains a rolling 60-second window to calculate blinks per minute.
- **Smart Notifications**: Sends an OS toast notification and plays a subtle beep when you're not blinking enough.
- **Privacy Focused**: No data leaves your machine. Processing is done entirely locally.
- **Modern UI**: A sleek, dark-themed dashboard built with PyQt6.
- **System Tray Integration**: Runs quietly in the background.

## 🛠️ Tech Stack
- **Python**
- **MediaPipe** (Computer Vision)
- **OpenCV** (Video Capture)
- **PyQt6** (GUI)
- **Plyer** (Notifications)

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Ares19v/Blink.git
   cd Blink
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## 🧠 How it Works
The application uses the **Eye Aspect Ratio (EAR)** algorithm. By calculating the ratio of distances between vertical and horizontal landmarks of the eyes, it can detect when an eye is closed (blink). If the average blink rate falls below 12 blinks per minute (a common threshold for digital eye strain), it alerts the user.

## 📄 License
MIT
