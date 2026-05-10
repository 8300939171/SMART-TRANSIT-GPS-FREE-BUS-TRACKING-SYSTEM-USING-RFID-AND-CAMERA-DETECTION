from flask import Flask, request, jsonify, render_template
from datetime import datetime
import requests

app = Flask(__name__)

# ---------------- DATA ----------------
registered_buses = {
    "HR99GX0777": {"status": "AVAILABLE"},
    "HR98AA0000": {"status": "AVAILABLE"}
}

bus_data = {}

ADMIN_PIN = "1234"

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template("home.html")

# ---------------- ADMIN ----------------
@app.route('/admin')
def admin():
    return render_template("admin.html")

# ---------------- LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():
    if request.json.get("pin") == ADMIN_PIN:
        return jsonify({"status": "success"})
    return jsonify({"status": "fail"})

# ---------------- START BUS ----------------
@app.route('/start_bus', methods=['POST'])
def start_bus():
    bus_id = request.json.get("bus_id")
    if bus_id not in registered_buses:
        return jsonify({"error": "invalid bus"}), 400

    registered_buses[bus_id]["status"] = "RUNNING"
    registered_buses[bus_id]["start_time"] = str(datetime.now())

    return jsonify({"status": "started", "bus_id": bus_id})

# ---------------- STOP BUS ----------------
@app.route('/stop_bus', methods=['POST'])
def stop_bus():
    bus_id = request.json.get("bus_id")

    if bus_id not in registered_buses:
        return jsonify({"error": "invalid bus"}), 400

    registered_buses[bus_id]["status"] = "AVAILABLE"
    return jsonify({"status": "stopped", "bus_id": bus_id})

# ---------------- DEVICE UPDATE ----------------
@app.route('/update', methods=['POST'])
def update():
    data = request.json
    bus_id = data.get("bus_id") or data.get("bus_no")

    if registered_buses.get(bus_id, {}).get("status") != "RUNNING":
        return jsonify({"ignored": True})

    bus_data[bus_id] = {
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "location": data.get("location"),
        "time": str(datetime.now())
    }

    return jsonify({"status": "updated"})

# ---------------- BUS DATA ----------------
@app.route('/buses')
def buses():
    return jsonify({
        "registered": registered_buses,
        "live": bus_data
    })

# ---------------- ETA ----------------
@app.route('/eta', methods=['POST'])
def eta():
    data = request.json

    try:
        url = f"http://router.project-osrm.org/route/v1/driving/" \
              f"{data['user_lon']},{data['user_lat']};{data['bus_lon']},{data['bus_lat']}?overview=false"

        res = requests.get(url).json()
        route = res["routes"][0]

        return jsonify({
            "distance": f"{route['distance']/1000:.2f} km",
            "eta": f"{route['duration']/60:.1f} min"
        })

    except:
        return jsonify({"distance": "N/A", "eta": "N/A"})

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
