#!/usr/bin/env python3
"""Solaar helper: hold Forward Button >=400ms to switch both devices to another host.

Sends HID++ change-host commands directly to the Unifying receiver's hidraw device,
bypassing Solaar's CLI/D-Bus path which silently fails for the triggering device.

Configuration is loaded from config.yaml in the same directory.
"""

import sys, time, os, struct
import config_loader

cfg = config_loader.load()

TIMESTAMP_FILE = "/tmp/.solaar-fwd-press-ts"
HOLD_THRESHOLD = cfg["hold_threshold"]

RECEIVER_HIDRAW = cfg["receiver_hidraw"]

MOUSE_DEV_NUM = cfg["mouse"]["dev_number"]
KEYBOARD_DEV_NUM = cfg["keyboard"]["dev_number"]

MOUSE_CHANGE_HOST_IDX = cfg["mouse"]["change_host_feature_index"]
KEYBOARD_CHANGE_HOST_IDX = cfg["keyboard"]["change_host_feature_index"]

TARGET_HOST_INDEX = cfg["target_host_index"]

# HID++ constants
HIDPP_LONG_MESSAGE_ID = 0x11
WRITE_FNID = 0x10  # change-host write function


def hidpp_change_host(hidraw_fd, dev_number, feature_index, host_index):
    """Send a HID++ 2.0 change-host write command directly to the receiver."""
    request_id = (feature_index << 8) | WRITE_FNID | 0x08
    data = struct.pack('!BB', (request_id >> 8) & 0xFF, request_id & 0xFF)
    data += struct.pack('B', host_index)
    data = data.ljust(18, b'\x00')
    msg = struct.pack('!BB', HIDPP_LONG_MESSAGE_ID, dev_number) + data
    os.write(hidraw_fd, msg)


def switch_both(dry_run=False):
    """Send change-host to both mouse and keyboard via raw HID++."""
    log = open("/tmp/.solaar-switch.log", "a")
    ts = time.strftime("%H:%M:%S")

    if dry_run:
        log.write(f"[{ts}] [dry-run] would send HID++ change-host to mouse and keyboard\n")
        print(f"[dry-run] would send HID++ change-host(host={TARGET_HOST_INDEX}) to {RECEIVER_HIDRAW}")
        log.close()
        return

    log.write(f"[{ts}] sending HID++ change-host via {RECEIVER_HIDRAW}...\n")
    log.flush()

    try:
        fd = os.open(RECEIVER_HIDRAW, os.O_RDWR)
        hidpp_change_host(fd, KEYBOARD_DEV_NUM, KEYBOARD_CHANGE_HOST_IDX, TARGET_HOST_INDEX)
        log.write(f"[{ts}] keyboard HID++ sent\n")
        log.flush()
        hidpp_change_host(fd, MOUSE_DEV_NUM, MOUSE_CHANGE_HOST_IDX, TARGET_HOST_INDEX)
        log.write(f"[{ts}] mouse HID++ sent\n")
        os.close(fd)
    except Exception as e:
        log.write(f"[{ts}] error: {e}\n")

    log.close()


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
        switch_both(dry_run=dry_run)
    else:
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
