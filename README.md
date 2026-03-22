# 💧 AquaSync – Smart Water Monitoring System

![AquaSync Banner](https://img.shields.io/badge/AquaSync-Smart%20Water%20Monitoring-blue?style=for-the-badge&logo=water)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-Backend-black?style=flat-square&logo=flask)
![ESP32](https://img.shields.io/badge/ESP32-IoT%20Hardware-red?style=flat-square)
![ML](https://img.shields.io/badge/ML-LinearRegression%20%7C%20IsolationForest-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## 📌 Overview

**AquaSync** is an IoT + Machine Learning based system designed to monitor water pipeline pressure, detect leaks in real-time, and predict future failures before they occur.

The system integrates **ESP32-based hardware** with a **Flask ML backend** and **Machine Learning models** to provide intelligent water management, predictive analytics, and an interactive web dashboard for both administrators and citizens.

> 🏙️ Built for smart city infrastructure — specifically targeting municipal water distribution management.

---

## 🚀 Key Features

| Feature | Description |
|---|---|
| 📡 **Real-Time Monitoring** | Continuous pressure monitoring across multiple zones using ESP32 sensors |
| ⚠️ **Leak Detection** | Instant leak detection via pressure drop analysis and hardware buzzer alerts |
| 📊 **Live Dashboard** | Web-based admin dashboard with charts and zone-level status indicators |
| 🤖 **ML Prediction** | Linear Regression model predicts future pressure trends |
| 🚨 **Anomaly Detection** | Isolation Forest model identifies irregular pressure patterns |
| 🧾 **Complaint Management** | Citizens can submit complaints; admins can track and resolve them |
| 📢 **Announcement System** | Admins can broadcast water supply updates to citizens |
| 🕐 **Water Schedule** | Zone-wise water supply schedules with status tracking |
| 🔴 **Visual Indicators** | RGB LEDs and buzzer for real-time hardware-level alerts |

---

## 🧠 Tech Stack

### 🔧 Hardware
- **ESP32 DevKit V1** — Main microcontroller with WiFi capability
- **Water Pressure Sensors** — Analog sensors on pins 34, 35, 32 (Zones 1–3)
- **RGB LEDs** — Red (critical), Yellow (warning), Green (normal)
- **Buzzer** — Audible alert on leak detection

### 🐍 Software (Backend)
| Library | Purpose |
|---|---|
| `Flask` | REST API backend server |
| `flask-cors` | Cross-origin request handling |
| `NumPy` | Numerical computations |
| `scikit-learn` | ML models (LinearRegression, IsolationForest) |

### 🤖 Machine Learning
| Model | Role |
|---|---|
| **Linear Regression** | Predicts future pressure trends from historical data |
| **Isolation Forest** | Detects anomalies — leaks, bursts, surges, sensor failures |

### 🌐 Frontend
- **HTML5 / CSS3 / JavaScript** — Dashboard and citizen portal
- Fetch API for real-time data polling from the Flask backend

### 📡 Communication
- **WiFi (HTTP/REST API)** — ESP32 serves sensor data over local network
- JSON-based data exchange between all components

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AquaSync Data Flow                       │
└─────────────────────────────────────────────────────────────────┘

  [Pressure Sensors]
       │  Analog signal (0–3.3V)
       ▼
  [ESP32 DevKit V1]
    • Reads sensor data
    • Detects leaks (pressure drop > 0.8 bar)
    • Controls LEDs & Buzzer
    • Serves /data endpoint via WiFi
       │  HTTP JSON over WiFi
       ▼
  [Python / Flask ML Backend]  ←──── ml/predict.py (port 5001)
    • Collects pressure history per zone
    • Linear Regression → predicts future pressure
    • Isolation Forest  → detects anomalies
    • Manages complaints, announcements, schedules
       │  REST API (JSON)
       ▼
  [Web Dashboard]              ←──── dashboard/index.html
    • Real-time charts & zone cards
    • Anomaly alerts
    • Complaint management panel
    • Announcement board
    • Water supply schedule

  [Citizen Portal]             ←──── citizen/index.html
    • View announcements
    • Submit complaints
    • Check water schedule
```

---

## 📁 Project Structure

```
AQUASYNC/
│
├── citizen/                        # 👤 Citizen-facing portal
│   └── index.html                  #    Complaint submission & announcements
│
├── dashboard/                      # 🖥️ Admin dashboard
│   └── index.html                  #    Real-time monitoring & management
│
├── firmware/                       # 📟 ESP32 Arduino firmware
│   └── esp32_aquasync/
│       └── esp32_aquasync.ino      #    Main ESP32 sketch
│
├── ml/                             # 🧠 ML backend (Flask)
│   ├── predict.py                  #    Flask app — ML models & API routes
│   ├── complaints.json             #    Persistent complaints store
│   ├── announcements.json          #    Persistent announcements store
│   └── schedule.json               #    Water supply schedule store
│
├── index.html                      # 🏠 Landing / entry page
├── requirements.txt                # 📦 Python dependencies
└── README.md                       # 📖 This file
```

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Arduino IDE (for ESP32 firmware upload)
- ESP32 board support installed in Arduino IDE
- ArduinoJson library installed in Arduino IDE

---

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/ananya-singh21/AQUASYNC.git
cd AQUASYNC
```

### 2️⃣ Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Run the ML Backend

```bash
python ml/predict.py
```

You should see:

```
=======================================================
  AquaSync ML Backend — Dual Model System
=======================================================
  Models: LinearRegression + IsolationForest
  ML:            http://localhost:5001/predict
  Anomalies:     http://localhost:5001/anomaly_status
  Complaints:    http://localhost:5001/complaints
  Announcements: http://localhost:5001/announcements
  Schedule:      http://localhost:5001/schedule
=======================================================
```

### 4️⃣ Upload ESP32 Firmware (Optional — for real hardware)

1. Open **Arduino IDE**
2. Open the file: `firmware/esp32_aquasync/esp32_aquasync.ino`
3. Edit WiFi credentials in the sketch:
   ```cpp
   const char* ssid     = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
4. Select **ESP32 Dev Module** as the board
5. Click **Upload**
6. Open Serial Monitor (115200 baud) to get the ESP32's IP address

### 5️⃣ Open the Dashboard

```
Open: dashboard/index.html in your browser
```

> **Note:** If using real ESP32 hardware, update the `ESP32_IP` variable in `dashboard/index.html` to match the IP address shown in the Serial Monitor.

---

## 🔬 Simulation Mode

AquaSync ships with a **built-in simulation mode** so you can test and demonstrate the system without any physical hardware.

The `simulate_reading()` function in `ml/predict.py` generates realistic pressure data using sinusoidal patterns with random noise:

```python
def simulate_reading():
    p1 = 3.2 + np.sin(t * 0.8) * 0.6 + random.uniform(-0.1, 0.1)
    p2 = 2.8 + np.sin(t * 0.6 + 1) * 0.8 + random.uniform(-0.1, 0.1)
    p3 = 3.1 + np.sin(t * 0.4 + 2) * 0.5 + random.uniform(-0.1, 0.1)
    ...
```

| Mode | Data Source | How to Switch |
|---|---|---|
| **Simulation** (default) | Generated by `simulate_reading()` in `predict.py` | Default — just run `python ml/predict.py` |
| **Real Hardware** | ESP32 sensors over WiFi | Connect ESP32 and point the dashboard to its IP |

---

## 🔄 How It Works

```
Step 1 — Sensor Reading
  ESP32 reads analog voltage from pressure sensors → converts to bar (0–5 bar range)

Step 2 — Leak Detection (Hardware Level)
  If pressure drops > 0.8 bar between readings → leak flag set
  LEDs update: 🔴 Red + 🔊 Buzzer for leaks, 🟡 Yellow for warning, 🟢 Green for normal

Step 3 — Data Transmission
  ESP32 serves readings as JSON at http://<ESP32_IP>/data
  Dashboard fetches this data via HTTP

Step 4 — ML Analysis (Python Backend)
  Flask backend receives or simulates pressure readings
  Appends to per-zone history buffer (max 50 readings)

Step 5 — Linear Regression (Prediction)
  Trains on zone history once ≥5 readings available
  Predicts pressure 10 steps ahead
  Classifies trend: "dropping" / "stable" / "rising"
  Raises alert if predicted pressure < 1.0 bar

Step 6 — Isolation Forest (Anomaly Detection)
  Trains on zone history once ≥15 readings available
  Scores each new reading — flags anomalies (contamination=10%)
  Classifies anomaly type:
    • sudden_drop    → Possible pipe burst or major leak
    • gradual_drop   → Possible blockage or slow leak
    • pressure_surge → Check valve settings
    • critical_low   → Immediate action required
    • irregular      → Unknown irregular pattern

Step 7 — Dashboard Display
  Real-time charts show pressure history per zone
  Anomaly panel highlights active alerts with type & confidence
  Admin can manage complaints and post announcements
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/predict` | Simulated readings + ML predictions + anomaly results |
| `GET` | `/anomaly_status` | Current anomaly summary across all zones |
| `GET` | `/complaints` | List all complaints |
| `POST` | `/complaint` | Submit a new complaint |
| `POST` | `/complaint/<id>/resolve` | Mark a complaint as resolved |
| `GET` | `/announcements` | List all announcements |
| `POST` | `/announcement` | Post a new announcement |
| `DELETE` | `/announcement/<id>` | Delete an announcement |
| `GET` | `/schedule` | Get water supply schedule |
| `POST` | `/schedule` | Update schedule entry |
| `GET` | `/health` | Backend health check |

---

## 🗺️ Monitored Zones

| Zone ID | Area Name |
|---|---|
| z1 | Hotgi Road |
| z2 | Akkalkot Road |
| z3 | Vijapur Road |

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. **Fork** the repository
2. **Create** a new branch: `git checkout -b feature/your-feature-name`
3. **Commit** your changes: `git commit -m "Add: your feature description"`
4. **Push** to your branch: `git push origin feature/your-feature-name`
5. **Open a Pull Request** on GitHub

Please make sure your changes are well-tested and documented before submitting a PR.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 📬 Contact

**Ananya Singh**
- 🔗 GitHub: [@ananya-singh21](https://github.com/ananya-singh21)
- 📁 Repository: [github.com/ananya-singh21/AQUASYNC](https://github.com/ananya-singh21/AQUASYNC)

---

<p align="center">
  Made with ❤️ for Smart Water Management
</p>
