#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing solaar-switch from: $SCRIPT_DIR"

# 1. Install Solaar rules (symlink)
RULES_SRC="$SCRIPT_DIR/rules.yaml"
RULES_DST="$HOME/.config/solaar/rules.yaml"

# Update rules.yaml with the actual install path
sed -i "s|__INSTALL_DIR__|$SCRIPT_DIR|g" "$RULES_SRC"

mkdir -p "$(dirname "$RULES_DST")"
if [ -e "$RULES_DST" ] && [ ! -L "$RULES_DST" ]; then
    echo "Backing up existing rules.yaml to rules.yaml.bak"
    cp "$RULES_DST" "${RULES_DST}.bak"
fi
ln -sf "$RULES_SRC" "$RULES_DST"
echo "Symlinked rules: $RULES_DST -> $RULES_SRC"

# 2. Install systemd user service
SERVICE_SRC="$SCRIPT_DIR/solaar-redivert.service"
SERVICE_DST="$HOME/.config/systemd/user/solaar-redivert.service"

# Generate service file with actual path
mkdir -p "$(dirname "$SERVICE_DST")"
sed "s|__INSTALL_DIR__|$SCRIPT_DIR|g" "$SERVICE_SRC" > "$SERVICE_DST"
echo "Installed service: $SERVICE_DST"

# 3. Enable and start the service
systemctl --user daemon-reload
systemctl --user enable solaar-redivert.service
systemctl --user start solaar-redivert.service
echo "Service enabled and started."

echo ""
echo "Done! Next steps:"
echo "  1. Edit $SCRIPT_DIR/config.yaml with your device settings"
echo "  2. Divert Forward Button in Solaar GUI"
echo "  3. Restart Solaar: killall solaar; nohup solaar >/dev/null 2>&1 &"
echo ""
echo "Check service status: systemctl --user status solaar-redivert"
echo "View watcher log:     journalctl --user -u solaar-redivert -f"
