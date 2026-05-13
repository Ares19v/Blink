# Dockerfile designed for headless CI/CD testing of the Blink logic
FROM python:3.11-slim

# Install system dependencies required by OpenCV and PyQt6 in a headless environment
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use xvfb to fake a display for PyQt6 during tests
CMD xvfb-run -a pytest tests/ -v
