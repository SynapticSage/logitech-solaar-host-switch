#!/usr/bin/env python3
"""Watch for Forward Button diversion loss and re-apply it.

Solaar persists divert-keys in config but doesn't reliably re-push to the device
after a host switch reconnect. This script polls `solaar show` (which reports actual
device state) and re-applies diversion when it's lost.

Configuration is loaded from config.yaml in the same directory.
"""

import subprocess
import time

import config_loader

cfg = config_loader.load()

MOUSE_NAME = cfg["mouse"]["name"]
DIVERT_KEY = cfg["redivert"]["key"]
POLL_INTERVAL = cfg["redivert"]["poll_interval"]


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
            if "Key/Button Diversion" in line and "(saved)" not in line:
                if f"{DIVERT_KEY}:Diverted" in line:
                    return True
                if f"{DIVERT_KEY}:Regular" in line:
                    return False
        return None
    except Exception:
        return None


def redivert():
    """Force key diversion via solaar CLI."""
    try:
        result = subprocess.run(
            ["solaar", "config", MOUSE_NAME, "divert-keys", DIVERT_KEY, "Diverted"],
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
    print(f"[redivert_watch] Watching {MOUSE_NAME} / {DIVERT_KEY}, poll every {POLL_INTERVAL}s", flush=True)

    while True:
        try:
            diverted = get_actual_diversion()

            if diverted is False:
                ts = time.strftime("%H:%M:%S")
                print(f"[{ts}] {DIVERT_KEY} not diverted on device, re-applying...", flush=True)
                redivert()
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
