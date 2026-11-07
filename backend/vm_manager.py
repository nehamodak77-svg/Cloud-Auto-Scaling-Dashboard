# vm_manager.py  (Member 1 - Cloud Infrastructure & VM Provisioning)
#
# This file is our small "cloud". Every VM is a record stored in vms.json,
# so the data is kept even after the program stops.

import json
import os
from datetime import datetime

# Absolute path: no matter where Flask is started from, vms.json is created in the backend folder
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vms.json")
MAX_VMS = 5  # cloud limit: no more than this many VMs can exist


# ---------- helper functions (file read / write) ----------

def load_data():
    """Read all VMs from the file. If the file does not exist, start with an empty cloud."""
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "vms": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Write all VMs back to the file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ---------- main functions ----------

def setup_cloud():
    """Reset the cloud environment (empty vms.json)."""
    save_data({"next_id": 1, "vms": {}})
    print("Cloud environment is ready. Max VMs allowed:", MAX_VMS)


def create_vm(name, cpu=1, memory_mb=1024):
    """Create a new VM and start it. Returns the VM id, or None if the cloud is full."""
    data = load_data()

    if len(data["vms"]) >= MAX_VMS:
        print("Cannot create VM: cloud limit reached.")
        return None

    vm_id = str(data["next_id"])
    data["vms"][vm_id] = {
        "id": vm_id,
        "name": name,
        "cpu": cpu,
        "memory_mb": memory_mb,
        "status": "running",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    data["next_id"] += 1
    save_data(data)
    print("VM created:", name, "(id " + vm_id + ")")
    return vm_id


def start_vm(vm_id):
    """Start a stopped VM."""
    data = load_data()
    if vm_id not in data["vms"]:
        print("VM not found.")
        return False
    if data["vms"][vm_id]["status"] == "running":
        print("VM is already running.")
        return False
    data["vms"][vm_id]["status"] = "running"
    save_data(data)
    print("VM started:", vm_id)
    return True


def stop_vm(vm_id):
    """Stop a running VM."""
    data = load_data()
    if vm_id not in data["vms"]:
        print("VM not found.")
        return False
    if data["vms"][vm_id]["status"] == "stopped":
        print("VM is already stopped.")
        return False
    data["vms"][vm_id]["status"] = "stopped"
    save_data(data)
    print("VM stopped:", vm_id)
    return True


def delete_vm(vm_id):
    """Delete a VM completely."""
    data = load_data()
    if vm_id not in data["vms"]:
        print("VM not found.")
        return False
    del data["vms"][vm_id]
    save_data(data)
    print("VM deleted:", vm_id)
    return True


def get_vm_status(vm_id):
    """Return 'running' or 'stopped' (None if the VM does not exist)."""
    data = load_data()
    if vm_id not in data["vms"]:
        return None
    return data["vms"][vm_id]["status"]


def update_vm_config(vm_id, cpu=None, memory_mb=None):
    """Change the CPU / memory settings of a VM."""
    data = load_data()
    if vm_id not in data["vms"]:
        print("VM not found.")
        return False
    if cpu is not None:
        data["vms"][vm_id]["cpu"] = cpu
    if memory_mb is not None:
        data["vms"][vm_id]["memory_mb"] = memory_mb
    save_data(data)
    print("VM config updated:", vm_id)
    return True


def list_vms():
    """List of all VMs (each VM is a dictionary)."""
    data = load_data()
    return list(data["vms"].values())


def count_running_vms():
    """How many VMs are running right now? (Used by the dashboard.)"""
    count = 0
    for vm in list_vms():
        if vm["status"] == "running":
            count += 1
    return count
