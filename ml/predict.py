from flask import Flask, jsonify, request
from flask_cors import CORS
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
import random
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

COMPLAINTS_FILE    = "complaints.json"
ANNOUNCEMENTS_FILE = "announcements.json"
SCHEDULE_FILE      = "schedule.json"

def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return default

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

DEFAULT_SCHEDULE = {
    "w1": {"name":"Hotgi Road",      "times":["6:00 AM – 8:00 AM","6:00 AM – 8:00 AM","6:00 AM – 8:00 AM","6:00 AM – 8:00 AM","6:00 AM – 8:00 AM","6:00 AM – 9:00 AM","6:00 AM – 9:00 AM"], "status":["normal","normal","normal","normal","normal","normal","normal"]},
    "w2": {"name":"Akkalkot Road",   "times":["7:00 AM – 9:00 AM","7:00 AM – 9:00 AM","7:00 AM – 9:00 AM","7:00 AM – 9:00 AM","7:00 AM – 9:00 AM","7:00 AM – 10:00 AM","7:00 AM – 10:00 AM"], "status":["normal","normal","warning","normal","normal","normal","normal"]},
    "w3": {"name":"Vijapur Road",    "times":["5:30 AM – 7:30 AM","5:30 AM – 7:30 AM","5:30 AM – 7:30 AM","5:30 AM – 7:30 AM","5:30 AM – 7:30 AM","5:30 AM – 8:30 AM","5:30 AM – 8:30 AM"], "status":["normal","normal","normal","normal","normal","normal","normal"]},
    "w4": {"name":"Central Solapur", "times":["6:00 AM – 8:30 AM","6:00 AM – 8:30 AM","6:00 AM – 8:30 AM","6:00 AM – 8:30 AM","6:00 AM – 8:30 AM","6:00 AM – 9:30 AM","6:00 AM – 9:30 AM"], "status":["normal","normal","normal","normal","normal","normal","normal"]},
    "w5": {"name":"Solapur Bazar",   "times":["6:30 AM – 8:30 AM","6:30 AM – 8:30 AM","No Supply","6:30 AM – 8:30 AM","6:30 AM – 8:30 AM","6:30 AM – 9:30 AM","6:30 AM – 9:30 AM"], "status":["normal","normal","critical","normal","normal","normal","normal"]},
    "w6": {"name":"Kegaon",          "times":["7:00 AM – 9:00 AM","7:00 AM – 9:00 AM","7:00 AM – 9:00 AM","7:00 AM – 9:00 AM","7:00 AM – 9:00 AM","7:00 AM – 10:00 AM","7:00 AM – 10:00 AM"], "status":["normal","normal","normal","normal","normal","normal","normal"]},
    "w7": {"name":"Mangalwar Peth",  "times":["6:00 AM – 8:00 AM","6:00 AM – 8:00 AM","6:00 AM – 8:00 AM","Maintenance","6:00 AM – 8:00 AM","6:00 AM – 9:00 AM","6:00 AM – 9:00 AM"], "status":["normal","normal","normal","warning","normal","normal","normal"]},
    "w8": {"name":"Siddheshwar",     "times":["5:00 AM – 7:00 AM","5:00 AM – 7:00 AM","5:00 AM – 7:00 AM","5:00 AM – 7:00 AM","5:00 AM – 7:00 AM","5:00 AM – 8:00 AM","5:00 AM – 8:00 AM"], "status":["normal","normal","normal","normal","normal","normal","normal"]},
}

# ============================================================
# ML MODELS
# ============================================================
flow_history = { "z1": [], "z2": [] }
isolation_models = {}  # one model per zone
t = 0

ZONE_NAMES = {"z1":"Hotgi Road", "z2":"Akkalkot Road"}

def simulate_reading():
    global t
    t += 0.05
    # Simulate realistic flow rates in L/min (YF-S201 range ~2–30 L/min)
    f1 = 18.0 + np.sin(t * 0.8) * 5.0 + random.uniform(-0.5, 0.5)
    f2 = 15.0 + np.sin(t * 0.6 + 1) * 4.0 + random.uniform(-0.5, 0.5)
    return {
        "z1": round(max(1.0, min(30.0, f1)), 2),
        "z2": round(max(1.0, min(30.0, f2)), 2)
    }

def linear_predict(zone_history):
    """Linear Regression — predicts future flow rate trend"""
    if len(zone_history) < 5:
        return None
    X = np.array(range(len(zone_history))).reshape(-1, 1)
    y = np.array(zone_history)
    model = LinearRegression()
    model.fit(X, y)
    predicted = model.predict([[len(zone_history) + 10]])[0]
    trend = zone_history[-1] - zone_history[0]
    return {
        "predicted": round(float(predicted), 2),
        "trend": round(float(trend), 2),
        "direction": "dropping" if trend < -0.2 else "rising" if trend > 0.2 else "stable"
    }

def isolation_detect(zone, zone_history):
    """
    Isolation Forest — detects anomalies in flow rate readings.
    Anomalies indicate: leaks, pipe bursts, unauthorized tapping,
    sudden flow surges, or sensor failures.
    """
    if len(zone_history) < 15:
        return {
            "is_anomaly": False,
            "anomaly_score": 0.0,
            "anomaly_type": "collecting_data",
            "message": "Collecting data for anomaly detection...",
            "confidence": 0
        }

    X = np.array(zone_history).reshape(-1, 1)

    # Train or retrain Isolation Forest
    model = IsolationForest(
        contamination=0.1,   # expect 10% anomalies
        random_state=42,
        n_estimators=100
    )
    model.fit(X)
    isolation_models[zone] = model

    # Score the latest reading
    latest = np.array([[zone_history[-1]]])
    prediction = model.predict(latest)[0]       # -1 = anomaly, 1 = normal
    score = model.score_samples(latest)[0]      # lower = more anomalous

    is_anomaly = prediction == -1

    # Determine anomaly type based on flow rate behavior
    current = zone_history[-1]
    avg = np.mean(zone_history[-10:])
    drop_rate = zone_history[-1] - zone_history[-5] if len(zone_history) >= 5 else 0

    anomaly_type = "normal"
    message = "Flow rate within normal operating range"

    if is_anomaly:
        if drop_rate < -5.0:
            anomaly_type = "sudden_drop"
            message = "⚠ SUDDEN FLOW DROP — Possible pipe burst or leak!"
        elif drop_rate < -2.0:
            anomaly_type = "gradual_drop"
            message = "⚠ Gradual flow decline — Possible blockage or leak"
        elif current > avg + 5.0:
            anomaly_type = "flow_surge"
            message = "⚠ FLOW SURGE — Check valve settings"
        elif current < 3.0:
            anomaly_type = "critical_low"
            message = "🚨 CRITICAL LOW FLOW — Immediate action required"
        else:
            anomaly_type = "irregular"
            message = "⚠ Irregular flow pattern detected"

    confidence = min(100, int(abs(score) * 100))

    return {
        "is_anomaly": bool(is_anomaly),
        "anomaly_score": round(float(score), 4),
        "anomaly_type": anomaly_type,
        "message": message,
        "confidence": confidence
    }

# ============================================================
# ROUTES
# ============================================================

@app.route('/predict')
def get_prediction():
    readings = simulate_reading()

    results = {}
    for zone in ["z1", "z2"]:
        # Add to history
        flow_history[zone].append(readings[zone])
        if len(flow_history[zone]) > 50:
            flow_history[zone].pop(0)

        # Linear Regression prediction
        lr = linear_predict(flow_history[zone])

        # Isolation Forest anomaly detection
        iso = isolation_detect(zone, flow_history[zone])

        result = {
            "current": readings[zone],
            "name": ZONE_NAMES[zone],
        }

        if lr:
            result["predicted"]  = lr["predicted"]
            result["trend"]      = lr["trend"]
            result["direction"]  = lr["direction"]
            result["alert"]      = lr["predicted"] < 5.0
            result["warning"]    = lr["predicted"] < 10.0

        result["anomaly"]        = iso
        results[zone] = result

    return jsonify({
        "predictions": results,
        "readings":    readings,
        "status":      "ok",
        "models":      "LinearRegression + IsolationForest"
    })

@app.route('/anomaly_status')
def anomaly_status():
    """Quick endpoint for dashboard anomaly widget"""
    anomalies = []
    for zone, hist in flow_history.items():
        if len(hist) >= 15:
            iso = isolation_detect(zone, hist)
            if iso["is_anomaly"]:
                anomalies.append({
                    "zone": ZONE_NAMES[zone],
                    "zone_id": zone,
                    "type": iso["anomaly_type"],
                    "message": iso["message"],
                    "confidence": iso["confidence"]
                })
    return jsonify({
        "status": "ok",
        "anomalies": anomalies,
        "total_anomalies": len(anomalies)
    })

# ============================================================
# COMPLAINT ROUTES
# ============================================================
@app.route('/complaint', methods=['POST'])
def submit_complaint():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error"}), 400
    complaints = load_json(COMPLAINTS_FILE, [])
    complaint = {
        "id": len(complaints) + 1,
        "name": data.get("name", "Unknown"),
        "mobile": data.get("mobile", ""),
        "ward": data.get("ward", ""),
        "type": data.get("type", ""),
        "description": data.get("description", ""),
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "status": "pending"
    }
    complaints.append(complaint)
    save_json(COMPLAINTS_FILE, complaints)
    print(f"New complaint from {complaint['name']} - Ward {complaint['ward']}")
    return jsonify({"status": "success", "complaint_id": complaint["id"]})

@app.route('/complaints', methods=['GET'])
def get_complaints():
    complaints = load_json(COMPLAINTS_FILE, [])
    return jsonify({
        "status": "ok",
        "complaints": complaints,
        "total": len(complaints),
        "pending":  len([c for c in complaints if c["status"] == "pending"]),
        "resolved": len([c for c in complaints if c["status"] == "resolved"])
    })

@app.route('/complaint/<int:complaint_id>/resolve', methods=['POST'])
def resolve_complaint(complaint_id):
    complaints = load_json(COMPLAINTS_FILE, [])
    for c in complaints:
        if c["id"] == complaint_id:
            c["status"] = "resolved"
            c["resolved_at"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            save_json(COMPLAINTS_FILE, complaints)
            return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 404

# ============================================================
# ANNOUNCEMENT ROUTES
# ============================================================
@app.route('/announcements', methods=['GET'])
def get_announcements():
    return jsonify({"status": "ok", "announcements": load_json(ANNOUNCEMENTS_FILE, [])})

@app.route('/announcement', methods=['POST'])
def post_announcement():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error"}), 400
    announcements = load_json(ANNOUNCEMENTS_FILE, [])
    announcement = {
        "id": len(announcements) + 1,
        "title": data.get("title", ""),
        "body": data.get("body", ""),
        "type": data.get("type", "info"),
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "posted_by": data.get("posted_by", "SMC Engineer")
    }
    announcements.insert(0, announcement)
    save_json(ANNOUNCEMENTS_FILE, announcements)
    print(f"New announcement: {announcement['title']}")
    return jsonify({"status": "success", "id": announcement["id"]})

@app.route('/announcement/<int:ann_id>', methods=['DELETE'])
def delete_announcement(ann_id):
    announcements = load_json(ANNOUNCEMENTS_FILE, [])
    announcements = [a for a in announcements if a["id"] != ann_id]
    save_json(ANNOUNCEMENTS_FILE, announcements)
    return jsonify({"status": "success"})

# ============================================================
# SCHEDULE ROUTES
# ============================================================
@app.route('/schedule', methods=['GET'])
def get_schedule():
    return jsonify({"status": "ok", "schedule": load_json(SCHEDULE_FILE, DEFAULT_SCHEDULE)})

@app.route('/schedule', methods=['POST'])
def update_schedule():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error"}), 400
    schedule = load_json(SCHEDULE_FILE, DEFAULT_SCHEDULE)
    ward = data.get("ward")
    day_index = data.get("day_index")
    new_time = data.get("time")
    new_status = data.get("status")
    if ward and ward in schedule:
        if day_index is not None and new_time:
            schedule[ward]["times"][day_index] = new_time
        if day_index is not None and new_status:
            schedule[ward]["status"][day_index] = new_status
        save_json(SCHEDULE_FILE, schedule)
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

# ============================================================
# HEALTH
# ============================================================
@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "models": "LinearRegression + IsolationForest",
        "zones_tracked": len([z for z in flow_history if len(flow_history[z]) > 0])
    })

if __name__ == '__main__':
    print("=" * 55)
    print("  AquaSync ML Backend — Dual Model System")
    print("=" * 55)
    print("  Models: LinearRegression + IsolationForest")
    print("  ML:            http://localhost:5001/predict")
    print("  Anomalies:     http://localhost:5001/anomaly_status")
    print("  Complaints:    http://localhost:5001/complaints")
    print("  Announcements: http://localhost:5001/announcements")
    print("  Schedule:      http://localhost:5001/schedule")
    print("=" * 55)
    app.run(port=5001, debug=False)
# ```

# ---

# **Ctrl+S → stop Flask → run again:**
# ```
# python predict.py
# ```

# You should see:
# ```
# =======================================================
#   AquaSync ML Backend — Dual Model System
# =======================================================
#   Models: LinearRegression + IsolationForest