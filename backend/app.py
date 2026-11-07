# app.py - Flask API
#
# This file connects the three modules (vm_manager, monitor, autoscaler)
# and exposes them as a JSON API for the React dashboard.
#
# Run:  python app.py      (http://localhost:5001)

import os
import threading
import time
from collections import deque

from flask import Flask, jsonify, request, send_from_directory

import monitor
import vm_manager as vmm
from autoscaler import AutoScaler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "..", "frontend", "dist")  # created after npm run build

app = Flask(__name__, static_folder=None)

# Lock, so two requests at the same time cannot corrupt vms.json
lock = threading.Lock()

# ---------- in-memory state (reset when the server restarts) ----------
scaler = AutoScaler()
metrics = deque(maxlen=60)   # last 60 readings for the charts
last_reading = {"vms": []}   # to show per-VM CPU/memory in the table


# ---------- CORS (for development) ----------
# Not needed when you use the Vite proxy, but if React calls Flask directly from
# another port the browser blocks it. These headers allow the request.
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


@app.route("/api/<path:_any>", methods=["OPTIONS"])
def preflight(_any):
    return ("", 204)


# ---------- helpers ----------
def bad_request(message, code=400):
    return jsonify({"error": message}), code


def ensure_cloud():
    """On the first run, set up the cloud and create one starter VM."""
    if not os.path.exists(vmm.DATA_FILE):
        vmm.setup_cloud()
        vmm.create_vm("web-1")


def build_state():
    """The dashboard needs everything in a single response - it is built here."""
    readings = {r["vm_id"]: r for r in last_reading["vms"]}

    vms = []
    for vm in vmm.list_vms():
        row = dict(vm)
        r = readings.get(vm["id"])
        running = vm["status"] == "running"
        row["cpu_usage"] = r["cpu_usage"] if (r and running) else None
        row["memory_usage"] = r["memory_usage"] if (r and running) else None
        vms.append(row)

    decisions = []
    for d in reversed(list(scaler.history)[-30:]):
        item = dict(d)
        item["clock"] = time.strftime("%H:%M:%S", time.localtime(d["time"]))
        decisions.append(item)

    return {
        "vms": vms,
        "running_vms": vmm.count_running_vms(),
        "total_vms": len(vms),
        "cloud_limit": vmm.MAX_VMS,
        "workload": monitor.get_workload_level(),
        "users": monitor.generate_workload(),
        "avg_cpu": monitor.average(last_reading["vms"], "cpu_usage"),
        "avg_memory": monitor.average(last_reading["vms"], "memory_usage"),
        "settings": scaler.settings(),
        "metrics": list(metrics),
        "decisions": decisions,
    }


def respond_state():
    return jsonify(build_state())


def scale_up_one():
    """Start a stopped VM first (cheaper), otherwise create a new VM."""
    for vm in vmm.list_vms():
        if vm["status"] == "stopped":
            vmm.start_vm(vm["id"])
            return f"started stopped VM {vm['name']}"
    new_id = vmm.create_vm("AutoVM")
    return f"created AutoVM (id {new_id})" if new_id else None


def scale_down_one():
    """Remove the last running VM (at least one always remains)."""
    running = [vm for vm in vmm.list_vms() if vm["status"] == "running"]
    if len(running) > 1:
        vmm.delete_vm(running[-1]["id"])
        return f"deleted VM {running[-1]['name']}"
    return None


# ---------- routes ----------
@app.get("/api/state")
def get_state():
    with lock:
        ensure_cloud()
        return respond_state()


@app.post("/api/tick")
def tick():
    """
    One monitoring cycle: take readings -> (if autoscale is ON) make a decision -> change VMs.
    The frontend calls this every 2 seconds.
    """
    body = request.get_json(silent=True) or {}
    autoscale = bool(body.get("autoscale"))

    with lock:
        ensure_cloud()
        readings = monitor.monitor_resources()
        last_reading["vms"] = readings
        running = vmm.count_running_vms()
        avg_cpu = monitor.average(readings, "cpu_usage")
        avg_mem = monitor.average(readings, "memory_usage")

        if autoscale:
            if running == 0:
                # No VM is running: start one to maintain the minimum
                note = scale_up_one()
                scaler.history.append({
                    "action": "scale_up", "new_vm_count": 1, "cpu": 0.0, "time": time.time(),
                    "reason": f"No running VMs, restoring minimum ({note})",
                })
            else:
                decision = scaler.decide(avg_cpu, running)
                if decision["action"] == "scale_up":
                    note = scale_up_one()
                    if note is None:
                        decision["action"] = "no_change"
                        decision["new_vm_count"] = running
                        decision["reason"] += " (cloud limit reached, VM not created)"
                    else:
                        decision["reason"] += f" ({note})"
                elif decision["action"] == "scale_down":
                    note = scale_down_one()
                    if note is None:
                        decision["action"] = "no_change"
                        decision["new_vm_count"] = running
                    else:
                        decision["reason"] += f" ({note})"

        metrics.append({
            "t": time.strftime("%H:%M:%S"),
            "cpu": avg_cpu,
            "memory": avg_mem,
            "vms": vmm.count_running_vms(),
            "users": monitor.generate_workload(),
        })
        return respond_state()


@app.post("/api/workload")
def set_workload():
    level = (request.get_json(silent=True) or {}).get("level")
    if not monitor.set_workload_level(level):
        return bad_request("level must be low, medium or high")
    with lock:
        ensure_cloud()
        return respond_state()


@app.post("/api/vms")
def create_vm():
    body = request.get_json(silent=True) or {}
    name = str(body.get("name", "")).strip() or "vm"
    try:
        cpu = int(body.get("cpu", 1))
        memory_mb = int(body.get("memory_mb", 1024))
    except (TypeError, ValueError):
        return bad_request("cpu and memory_mb must be numbers")
    if cpu < 1 or memory_mb < 128:
        return bad_request("cpu must be >= 1 and memory_mb >= 128")

    with lock:
        ensure_cloud()
        if vmm.create_vm(name, cpu, memory_mb) is None:
            return bad_request(f"Cloud limit reached (max {vmm.MAX_VMS} VMs)", 409)
        return respond_state()


@app.post("/api/vms/<vm_id>/start")
def start_vm(vm_id):
    with lock:
        if vmm.get_vm_status(vm_id) is None:
            return bad_request("VM not found", 404)
        vmm.start_vm(vm_id)
        return respond_state()


@app.post("/api/vms/<vm_id>/stop")
def stop_vm(vm_id):
    with lock:
        if vmm.get_vm_status(vm_id) is None:
            return bad_request("VM not found", 404)
        vmm.stop_vm(vm_id)
        return respond_state()


@app.delete("/api/vms/<vm_id>")
def delete_vm(vm_id):
    with lock:
        if not vmm.delete_vm(vm_id):
            return bad_request("VM not found", 404)
        return respond_state()


@app.put("/api/vms/<vm_id>/config")
def update_config(vm_id):
    body = request.get_json(silent=True) or {}
    try:
        cpu = int(body["cpu"])
        memory_mb = int(body["memory_mb"])
    except (KeyError, TypeError, ValueError):
        return bad_request("cpu and memory_mb are required numbers")
    if cpu < 1 or memory_mb < 128:
        return bad_request("cpu must be >= 1 and memory_mb >= 128")

    with lock:
        if not vmm.update_vm_config(vm_id, cpu, memory_mb):
            return bad_request("VM not found", 404)
        return respond_state()


@app.put("/api/settings")
def update_settings():
    """Change the auto-scaler settings (a new AutoScaler object is created)."""
    global scaler
    body = request.get_json(silent=True) or {}
    try:
        new_settings = {
            "scale_up_threshold": float(body["scale_up_threshold"]),
            "scale_down_threshold": float(body["scale_down_threshold"]),
            "min_vms": int(body["min_vms"]),
            "max_vms": int(body["max_vms"]),
            "cooldown_seconds": float(body["cooldown_seconds"]),
            "consecutive_checks": int(body["consecutive_checks"]),
        }
    except (KeyError, TypeError, ValueError):
        return bad_request("All six settings are required and must be numbers")

    if new_settings["max_vms"] > vmm.MAX_VMS:
        return bad_request(f"max_vms cannot exceed the cloud limit ({vmm.MAX_VMS})")

    try:
        candidate = AutoScaler(**new_settings)
    except ValueError as err:
        return bad_request(str(err))

    with lock:
        candidate.history = scaler.history  # keep the old history
        scaler = candidate
        ensure_cloud()
        return respond_state()


@app.post("/api/reset")
def reset():
    """Reset the whole cloud: delete all VMs, create one starter VM, clear the history."""
    global scaler
    with lock:
        vmm.setup_cloud()
        vmm.create_vm("web-1")
        monitor.set_workload_level("low")
        metrics.clear()
        last_reading["vms"] = []
        scaler = AutoScaler(**scaler.settings())
        return respond_state()


# ---------- production: serve the built React app ----------
@app.get("/")
def index():
    if os.path.isdir(DIST_DIR):
        return send_from_directory(DIST_DIR, "index.html")
    return jsonify({"message": "API is running. Start the React dev server (npm run dev) "
                               "or build it (npm run build) to see the dashboard."})


@app.get("/<path:path>")
def static_files(path):
    if os.path.isdir(DIST_DIR) and os.path.exists(os.path.join(DIST_DIR, path)):
        return send_from_directory(DIST_DIR, path)
    return bad_request("Not found", 404)


if __name__ == "__main__":
    with lock:
        ensure_cloud()
    # debug=True: the server restarts automatically when the code changes.
    # use_reloader=False because the reloader runs two processes, which can
    # confuse the in-memory history.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5001)), debug=True, use_reloader=False)
