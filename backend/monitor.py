# monitor.py  (Member 2 - Monitoring & Workload Simulation)
#
# Instead of real traffic, we simulate "users".
# Workload level -> users -> CPU / memory usage of each running VM.

import random

import vm_manager

LEVEL_TO_USERS = {"low": 10, "medium": 100, "high": 500}

CURRENT_WORKLOAD_LEVEL = "low"


def set_workload_level(level):
    """Change the workload. Returns True for a valid level, otherwise False."""
    global CURRENT_WORKLOAD_LEVEL
    if level in LEVEL_TO_USERS:
        CURRENT_WORKLOAD_LEVEL = level
        return True
    return False


def get_workload_level():
    return CURRENT_WORKLOAD_LEVEL


def generate_workload():
    """Number of simulated users for the current level."""
    return LEVEL_TO_USERS[CURRENT_WORKLOAD_LEVEL]


def monitor_resources():
    """
    Create one reading for every running VM.
    More users and fewer VMs means higher usage (the load is shared between VMs).
    """
    users = generate_workload()
    running_vms = [vm for vm in vm_manager.list_vms() if vm["status"] == "running"]

    if len(running_vms) == 0:
        return []

    readings = []
    for vm in running_vms:
        cpu = users / (len(running_vms) * 5) + random.uniform(-5, 5)
        mem = users / (len(running_vms) * 10) + random.uniform(-5, 5)
        readings.append({
            "vm_id": vm["id"],
            "vm_name": vm["name"],
            "cpu_usage": round(max(0, min(100, cpu)), 2),
            "memory_usage": round(max(0, min(100, mem)), 2),
        })
    return readings


def average(readings, key):
    """Average of one field across the list of readings."""
    if not readings:
        return 0.0
    return round(sum(r[key] for r in readings) / len(readings), 2)
