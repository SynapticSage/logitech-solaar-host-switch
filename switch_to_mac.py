#!/usr/bin/env python3
"""Solaar helper: hold Forward Button >=400ms to switch both devices to Mac (Host 3)."""

import sys, time, os, subprocess

TIMESTAMP_FILE = "/tmp/.solaar-fwd-press-ts"
HOLD_THRESHOLD = 0.4  # seconds

MOUSE_NAME = "MX Master 3 Wireless Mouse"
KEYBOARD_NAME = "MX Keys Keyboard"
TARGET_HOST = "3"


def on_pressed():
    with open(TIMESTAMP_FILE, "w") as f:
        f.write(str(time.monotonic()))


def on_released(dry_run=False):
    try:
        with open(TIMESTAMP_FILE) as f:
            press_time = float(f.read().strip())
        os.remove(TIMESTAMP_FILE)
    except (FileNotFoundError, ValueError):
        return

    duration = time.monotonic() - press_time

    if duration >= HOLD_THRESHOLD:
        # Long press -> switch both devices to Mac
        if dry_run:
            print(f"[dry-run] Hold {duration:.3f}s >= {HOLD_THRESHOLD}s: would switch both devices to {TARGET_HOST}")
            print(f"[dry-run] solaar config '{MOUSE_NAME}' change-host '{TARGET_HOST}'")
            print(f"[dry-run] solaar config '{KEYBOARD_NAME}' change-host '{TARGET_HOST}'")
        else:
            # Fire both in parallel via Popen — both HID++ switch commands
            # get sent to Solaar near-simultaneously.
            # Log to /tmp for debugging.
            log = open("/tmp/.solaar-switch.log", "a")
            ts = time.strftime("%H:%M:%S")
            log.write(f"[{ts}] hold detected ({duration:.3f}s), switching...\n")
            log.flush()
            p1 = subprocess.Popen(
                ["solaar", "config", MOUSE_NAME, "change-host", TARGET_HOST],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            p2 = subprocess.Popen(
                ["solaar", "config", KEYBOARD_NAME, "change-host", TARGET_HOST],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            # Wait and log results
            out1, err1 = p1.communicate(timeout=10)
            log.write(f"[{ts}] mouse rc={p1.returncode} out={out1.decode().strip()} err={err1.decode().strip()}\n")
            out2, err2 = p2.communicate(timeout=10)
            log.write(f"[{ts}] keyboard rc={p2.returncode} out={out2.decode().strip()} err={err2.decode().strip()}\n")
            log.close()
    else:
        # Short press -> emit Forward keypress
        if dry_run:
            print(f"[dry-run] Tap {duration:.3f}s < {HOLD_THRESHOLD}s: would emit XF86Forward")
        else:
            emit_forward()


def emit_forward():
    import evdev
    ui = evdev.UInput()
    ui.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_FORWARD, 1)
    ui.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_FORWARD, 0)
    ui.syn()
    ui.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    action = next((a for a in args if not a.startswith("--")), "")

    if action == "pressed":
        on_pressed()
    elif action == "released":
        on_released(dry_run=dry_run)
