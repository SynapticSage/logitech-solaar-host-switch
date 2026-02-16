# Solaar: Hold Forward Button → Switch to Mac

Switch both your MX Master 3 mouse and MX Keys keyboard to your MacBook by holding the Forward Button for 400ms. Short taps still work as browser-forward.

## How It Works

Two Solaar rules call `switch_to_mac.py` on press and release of the Forward Button:

1. **Press** — records a monotonic timestamp to `/tmp/.solaar-fwd-press-ts`
2. **Release** — computes hold duration:
   - **>= 400ms**: Runs `solaar config` to switch both devices to Host 3
   - **< 400ms**: Emits `XF86Forward` keypress via `evdev.UInput` (normal browser-forward)

## Prerequisites

- **Solaar** (with GUI or daemon running)
- **python3-evdev** — `sudo apt install python3-evdev`
- Forward Button must be **diverted** in Solaar (see Setup step 1)

## Setup

### 1. Divert the Forward Button

Open Solaar GUI → select **MX Master 3 Wireless Mouse** → **Key/Button Diversion** → enable **Forward Button**.

Or edit `~/.config/solaar/config.yaml` directly — change `0x56: 0x0` to `0x56: 0x1` under the mouse's `divert-keys` section, then restart Solaar.

### 2. Install the rules

Copy or symlink the rules file:

```bash
# Option A: symlink (recommended — stays in sync)
ln -sf /media/ryoung/Ark/Code/repos/Cat.Linux/solaar-linux-to-mac-switch-rule/rules.yaml \
       ~/.config/solaar/rules.yaml

# Option B: copy
cp rules.yaml ~/.config/solaar/rules.yaml
```

### 3. Restart Solaar

```bash
# If running as a service
systemctl --user restart solaar

# Or kill and relaunch
killall solaar && solaar &
```

## Configuration

Edit `switch_to_mac.py` to change:

| Variable | Default | Description |
|---|---|---|
| `HOLD_THRESHOLD` | `0.4` | Hold duration in seconds to trigger switch |
| `MOUSE_NAME` | `MX Master 3 Wireless Mouse` | Must match Solaar device name |
| `KEYBOARD_NAME` | `MX Keys Keyboard` | Must match Solaar device name |
| `TARGET_HOST` | `Host 3` | Target host (Host 1, Host 2, or Host 3) |

Device names must match exactly what Solaar uses. Check with: `solaar show`

## Testing

### Dry-run mode

Test without actually switching devices:

```bash
# Hold test (>= 400ms) — should print "would switch"
python3 switch_to_mac.py pressed && sleep 0.5 && python3 switch_to_mac.py released --dry-run

# Tap test (< 400ms) — should print "would emit XF86Forward"
python3 switch_to_mac.py pressed && sleep 0.1 && python3 switch_to_mac.py released --dry-run
```

### Live test

1. Divert Forward Button (step 1 above)
2. Install rules (step 2 above)
3. Restart Solaar (step 3 above)
4. Hold Forward Button on mouse for >400ms → both devices switch to Mac

### Rollback

Un-divert the Forward Button in Solaar GUI to restore default behavior. The rules become inert when the button isn't diverted.

## Troubleshooting

- **Nothing happens on hold**: Check that Forward Button is diverted (`0x56: 0x1` in config)
- **`solaar config` fails**: Verify device names with `solaar show` and update the script
- **Forward key doesn't work on short tap**: Ensure `python3-evdev` is installed and your user has write access to `/dev/uinput` (Solaar's udev rules typically grant this)
- **Permission denied on UInput**: Add your user to the `input` group: `sudo usermod -aG input $USER` then log out/in
