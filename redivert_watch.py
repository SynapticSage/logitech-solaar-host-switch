#!/usr/bin/env python3
"""Watch for MX Master 3 Forward Button diversion loss and re-apply it.

Solaar persists divert-keys in config but doesn't reliably re-push to the device
after a host switch reconnect. This script polls `solaar show` (which reports actual
device state) and re-applies diversion when it's lost.

Run as: systemd user service, or just `nohup python3 redivert_watch.py &`
"""

import re
import subprocess
import sys
import time

MOUSE_NAME = "MX Master 3 Wireless Mouse"
DIVERT_KEY = "Forward Button"
DIVERT_VALUE = "Diverted"
POLL_INTERVAL = 1  # seconds between checks


def get_actual_diversion():
    """Check actual device diversion state via `solaar show`.

    `solaar show` reports two lines:
      Key/Button Diversion (saved): {... Forward Button:Diverted ...}
      Key/Button Diversion        : {... Forward Button:Regular ...}
    The second line (without 'saved') is the actual device state.
    """
    try:
        result = subprocess.run(
            ["solaar", "show", MOUSE_NAME],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return None

        for line in result.stdout.splitlines():
            # Match the NON-saved line (actual device state)
            if "Key/Button Diversion" in line and "(saved)" not in line:
                if "Forward Button:Diverted" in line:
                    return True
                if "Forward Button:Regular" in line:
                    return False
        return None
    except Exception:
        return None


def redivert():
    """Force Forward Button diversion via solaar CLI."""
    try:
        result = subprocess.run(
            ["solaar", "config", MOUSE_NAME, "divert-keys", DIVERT_KEY, DIVERT_VALUE],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            ts = time.strftime("%H:%M:%S")
            print(f"[{ts}] redivert OK: {result.stdout.strip()}", flush=True)
        else:
            ts = time.strftime("%H:%M:%S")
            print(f"[{ts}] redivert failed: {result.stderr.strip()}", flush=True)
    except Exception as e:
        ts = time.strftime("%H:%M:%S")
        print(f"[{ts}] redivert error: {e}", flush=True)


def main():
    print(f"[redivert_watch] Polling every {POLL_INTERVAL}s for Forward Button diversion loss...", flush=True)

    while True:
        try:
            diverted = get_actual_diversion()

            if diverted is False:
                ts = time.strftime("%H:%M:%S")
                print(f"[{ts}] Forward Button not diverted on device, re-applying...", flush=True)
                redivert()
            elif diverted is None:
                pass  # device offline or unavailable, skip
        except Exception as e:
            ts = time.strftime("%H:%M:%S")
            print(f"[{ts}] poll error (continuing): {e}", flush=True)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[redivert_watch] stopped.", flush=True)
    except Exception as e:
        ts = time.strftime("%H:%M:%S")
        print(f"[{ts}] fatal: {e}", flush=True)
        raise
