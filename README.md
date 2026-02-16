# Solaar: Hold Forward Button to Switch Hosts

Switch both your Logitech mouse and keyboard to another host by holding the Forward Button for 400ms. Short taps preserve normal browser-forward behavior.

Built for multi-host setups where you want one-button switching from Linux to Mac (or any other host), complementing Logitech Options+ on the Mac side for switching back.

## How It Works

```
Hold Forward Button (>=400ms)
  -> switch_to_mac.py sends raw HID++ change-host commands
  -> both keyboard and mouse switch to the target host

Tap Forward Button (<400ms)
  -> switch_to_mac.py emits XF86Forward keypress via evdev
  -> normal browser-forward behavior preserved
```

Two Solaar rules intercept the Forward Button press and release events, calling `switch_to_mac.py` for each. The script measures hold duration using monotonic timestamps.

Host switching bypasses Solaar's CLI entirely — HID++ commands are written directly to the Unifying receiver's hidraw device for speed and reliability.

A companion `redivert_watch.py` daemon runs in the background to fix a Solaar bug where key diversion is lost after a host-switch reconnect.

## Requirements

- **Solaar** (with GUI or daemon running)
- **Python 3** with **PyYAML** (`sudo apt install python3-yaml`)
- **python3-evdev** (`sudo apt install python3-evdev`) — for Forward key passthrough on short taps

## Quick Start

```bash
git clone https://github.com/YOUR_USER/solaar-linux-to-mac-switch-rule.git
cd solaar-linux-to-mac-switch-rule

# 1. Edit config.yaml with your device settings (see Configuration below)
nano config.yaml

# 2. Divert the Forward Button in Solaar GUI:
#    Select your mouse -> Key/Button Diversion -> enable Forward Button

# 3. Run the installer
./install.sh

# 4. Restart Solaar
killall solaar; nohup solaar >/dev/null 2>&1 &
```

## Configuration

All device-specific settings live in `config.yaml`. Edit this file before running `install.sh`.

### Finding Your Device Settings

Run `solaar show` to find:

| Config Field | How to Find |
|---|---|
| `receiver_hidraw` | First "Device path" line in `solaar show` output |
| `mouse.name` | Device name shown by Solaar (e.g., "MX Master 3 Wireless Mouse") |
| `mouse.dev_number` | Number before the device name (e.g., "2: MX Master 3" -> `2`) |
| `mouse.change_host_feature_index` | Feature list index for CHANGE_HOST (e.g., feature `10`) |
| `keyboard.name` | Keyboard device name |
| `keyboard.dev_number` | Number before the keyboard name |
| `keyboard.change_host_feature_index` | Feature list index for CHANGE_HOST on keyboard |
| `target_host_index` | `0` = Host 1, `1` = Host 2, `2` = Host 3 |
| `hold_threshold` | Seconds to hold before triggering (default `0.4`) |

### Example `solaar show` Output

```
Unifying Receiver
  Device path  : /dev/hidraw0        <-- receiver_hidraw
  1: MX Keys Keyboard                <-- keyboard dev_number=1
    9: CHANGE HOST  {1814}           <-- keyboard change_host_feature_index=9
  2: MX Master 3 Wireless Mouse      <-- mouse dev_number=2
    10: CHANGE HOST  {1814}          <-- mouse change_host_feature_index=10
```

## Files

| File | Purpose |
|---|---|
| `config.yaml` | Device-specific settings |
| `switch_to_mac.py` | Hold detection + raw HID++ host switch |
| `redivert_watch.py` | Daemon that re-applies Forward Button diversion after reconnect |
| `rules.yaml` | Solaar rule definitions (symlinked by installer) |
| `config_loader.py` | Shared config file loader |
| `solaar-redivert.service` | systemd user service template |
| `install.sh` | Installer (symlinks rules, installs service) |

## Manual Setup (Without install.sh)

### 1. Divert the Forward Button

In Solaar GUI: select your mouse -> **Key/Button Diversion** -> enable **Forward Button**.

### 2. Install Rules

Edit `rules.yaml` — replace `__INSTALL_DIR__` with the full path to this directory, then symlink:

```bash
ln -sf /path/to/solaar-linux-to-mac-switch-rule/rules.yaml ~/.config/solaar/rules.yaml
```

### 3. Start the Redivert Watcher

```bash
# One-off
python3 /path/to/redivert_watch.py &

# Or install the systemd service manually
cp solaar-redivert.service ~/.config/systemd/user/
# Edit the service file: replace __INSTALL_DIR__ with actual path
systemctl --user daemon-reload
systemctl --user enable --now solaar-redivert
```

### 4. Restart Solaar

```bash
killall solaar; nohup solaar >/dev/null 2>&1 &
```

## Testing

```bash
# Dry-run hold test (>=400ms)
cd /path/to/solaar-linux-to-mac-switch-rule
python3 switch_to_mac.py pressed && sleep 0.5 && python3 switch_to_mac.py released --dry-run

# Dry-run tap test (<400ms)
python3 switch_to_mac.py pressed && sleep 0.1 && python3 switch_to_mac.py released --dry-run

# Check redivert service
systemctl --user status solaar-redivert
journalctl --user -u solaar-redivert -f

# Check switch log
cat /tmp/.solaar-switch.log
```

## Troubleshooting

- **Nothing happens on hold**: Check Forward Button is diverted — `solaar show YOUR_MOUSE | grep Diversion`
- **Only keyboard switches (not mouse)**: Verify `receiver_hidraw`, `dev_number`, and `change_host_feature_index` in `config.yaml` match `solaar show` output
- **Forward key doesn't work on short tap**: Ensure `python3-evdev` is installed and your user can write to `/dev/uinput`
- **Permission denied on hidraw**: Solaar's udev rules should grant access. Check: `ls -la /dev/hidraw*`
- **Redivert watcher not running**: `systemctl --user status solaar-redivert`
- **Switch works once then stops**: The redivert watcher should fix this automatically. Check its logs.

## Rollback

Un-divert the Forward Button in Solaar GUI to restore default behavior. The rules become inert when the button isn't diverted.

```bash
# Disable the service
systemctl --user disable --now solaar-redivert

# Remove the rules symlink
rm ~/.config/solaar/rules.yaml
```

## Why Raw HID++ Instead of `solaar config`?

The `solaar config change-host` CLI command goes through D-Bus to the running Solaar GUI. For the device that *triggered* the Solaar rule (the mouse), this path silently fails — the command reports success but the HID++ write doesn't reach the device. Writing directly to the receiver's hidraw device bypasses this entirely and is both faster and more reliable.
