#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing logitech-host-switch from: $SCRIPT_DIR"

# 1. Install Solaar rules (generate with actual path)
RULES_SRC="$SCRIPT_DIR/rules.yaml"
RULES_DST="$HOME/.config/solaar/rules.yaml"

mkdir -p "$(dirname "$RULES_DST")"
if [ -L "$RULES_DST" ]; then
    echo "Removing existing symlink: $RULES_DST"
    rm -f "$RULES_DST"
elif [ -e "$RULES_DST" ]; then
    echo "Backing up existing rules.yaml to rules.yaml.bak"
    cp "$RULES_DST" "${RULES_DST}.bak"
fi
sed "s|__INSTALL_DIR__|$SCRIPT_DIR|g" "$RULES_SRC" > "$RULES_DST"
echo "Installed rules: $RULES_DST"

# 2. Install systemd user service
SERVICE_SRC="$SCRIPT_DIR/logitech-redivert.service"
SERVICE_DST="$HOME/.config/systemd/user/logitech-redivert.service"

mkdir -p "$(dirname "$SERVICE_DST")"
if [ -L "$SERVICE_DST" ]; then
    rm -f "$SERVICE_DST"
fi
sed "s|__INSTALL_DIR__|$SCRIPT_DIR|g" "$SERVICE_SRC" > "$SERVICE_DST"
echo "Installed service: $SERVICE_DST"

# 3. Enable and start the service
systemctl --user daemon-reload
systemctl --user enable logitech-redivert.service
systemctl --user restart logitech-redivert.service
echo "Service enabled and started."

echo ""
echo "Done! Next steps:"
echo "  1. Edit $SCRIPT_DIR/config.yaml with your device settings"
echo "  2. Divert Forward Button in Solaar GUI"
echo "  3. Restart Solaar: killall solaar; nohup solaar >/dev/null 2>&1 &"
echo ""
echo "Check service status: systemctl --user status logitech-redivert"
echo "View watcher log:     journalctl --user -u logitech-redivert -f"
