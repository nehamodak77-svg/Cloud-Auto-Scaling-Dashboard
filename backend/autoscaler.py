# autoscaler.py  (Member 3 - Auto-scaling decision logic)
#
# AutoScaler only makes the DECISION (scale up / scale down / no change).
# Creating or removing VMs is done by app.py.

import time
from collections import deque

SCALE_UP_THRESHOLD = 70.0     # CPU % above this -> add a VM
SCALE_DOWN_THRESHOLD = 30.0   # CPU % below this -> remove a VM
MIN_VMS = 1                   # always keep at least this many VMs
MAX_VMS = 5                   # never go above this many VMs
COOLDOWN_SECONDS = 20         # wait time between two scaling actions (60 in the notebook)
CONSECUTIVE_CHECKS = 3        # readings in a row needed before acting


class AutoScaler:
    """Decides when to add or remove a VM."""

    def __init__(
        self,
        scale_up_threshold=SCALE_UP_THRESHOLD,
        scale_down_threshold=SCALE_DOWN_THRESHOLD,
        min_vms=MIN_VMS,
        max_vms=MAX_VMS,
        cooldown_seconds=COOLDOWN_SECONDS,
        consecutive_checks=CONSECUTIVE_CHECKS,
    ):
        if scale_down_threshold >= scale_up_threshold:
            raise ValueError("Scale-down threshold must be lower than the scale-up threshold")
        if min_vms < 1 or max_vms < min_vms:
            raise ValueError("Rule: 1 <= min VMs <= max VMs")
        if consecutive_checks < 1 or cooldown_seconds < 0:
            raise ValueError("Consecutive checks must be >= 1 and cooldown must be >= 0")

        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.min_vms = min_vms
        self.max_vms = max_vms
        self.cooldown_seconds = cooldown_seconds
        self.consecutive_checks = consecutive_checks

        self._high_count = 0           # how many high readings in a row
        self._low_count = 0            # how many low readings in a row
        self._last_action_time = None  # when the last scaling happened
        self.history = deque(maxlen=100)

    def settings(self):
        return {
            "scale_up_threshold": self.scale_up_threshold,
            "scale_down_threshold": self.scale_down_threshold,
            "min_vms": self.min_vms,
            "max_vms": self.max_vms,
            "cooldown_seconds": self.cooldown_seconds,
            "consecutive_checks": self.consecutive_checks,
        }

    def decide(self, cpu_percent, current_vms, now=None):
        """Make one decision. Returns a dict: action, new_vm_count, reason, cpu, time."""
        if now is None:
            now = time.time()

        # Step 1: update the "in a row" counters
        if cpu_percent > self.scale_up_threshold:
            self._high_count += 1
            self._low_count = 0
        elif cpu_percent < self.scale_down_threshold:
            self._low_count += 1
            self._high_count = 0
        else:
            self._high_count = 0
            self._low_count = 0

        action = "no_change"
        reason = f"CPU {cpu_percent:.1f}% is in the normal range"

        # Step 2: cooldown check
        in_cooldown = (
            self._last_action_time is not None
            and (now - self._last_action_time) < self.cooldown_seconds
        )

        # Step 3: scale-up logic
        if self._high_count > 0:
            if current_vms >= self.max_vms:
                reason = f"CPU high ({cpu_percent:.1f}%) but already at max VMs ({self.max_vms})"
            elif self._high_count < self.consecutive_checks:
                reason = (f"CPU high ({cpu_percent:.1f}%), waiting for confirmation "
                          f"({self._high_count}/{self.consecutive_checks})")
            elif in_cooldown:
                reason = f"CPU high ({cpu_percent:.1f}%) but cooldown is active"
            else:
                action = "scale_up"
                reason = f"CPU {cpu_percent:.1f}% above {self.scale_up_threshold}% -> add a VM"

        # Step 4: scale-down logic
        elif self._low_count > 0:
            if current_vms <= self.min_vms:
                reason = f"CPU low ({cpu_percent:.1f}%) but already at min VMs ({self.min_vms})"
            elif self._low_count < self.consecutive_checks:
                reason = (f"CPU low ({cpu_percent:.1f}%), waiting for confirmation "
                          f"({self._low_count}/{self.consecutive_checks})")
            elif in_cooldown:
                reason = f"CPU low ({cpu_percent:.1f}%) but cooldown is active"
            else:
                action = "scale_down"
                reason = f"CPU {cpu_percent:.1f}% below {self.scale_down_threshold}% -> remove a VM"

        # Step 5: apply the result
        new_count = current_vms
        if action == "scale_up":
            new_count = current_vms + 1
        elif action == "scale_down":
            new_count = current_vms - 1

        if action != "no_change":
            self._last_action_time = now
            self._high_count = 0
            self._low_count = 0

        decision = {
            "action": action,
            "new_vm_count": new_count,
            "reason": reason,
            "cpu": round(cpu_percent, 1),
            "time": now,
        }
        self.history.append(decision)
        return decision
