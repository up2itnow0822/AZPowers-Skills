#!/bin/bash
# AZPowers-Skills — Installation Script
# Installs clawpowers npm package and sets up runtime directories.
# Path-independent: works from any clone location.
set -e

# Resolve script and plugin dirs relative to this script's location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CLP_RUNTIME="$HOME/.clawpowers/runtime"

echo '=== AZPowers-Skills Installation ==='
echo "Plugin dir: $PLUGIN_DIR"

# Step 1: Create ~/.clawpowers runtime directories
echo '[1/3] Creating ~/.clawpowers runtime directories...'
mkdir -p "$HOME/.clawpowers"/{memory,metrics,logs,wallet,state/checkpoints,data,skills}
echo '  -> ~/.clawpowers/ ready'

# Step 2: Install clawpowers npm package
echo '[2/3] Installing clawpowers@2.2.6 from npm...'
mkdir -p "$CLP_RUNTIME"
npm install clawpowers@2.2.6 --prefix "$CLP_RUNTIME"
echo "  -> clawpowers@2.2.6 installed at $CLP_RUNTIME"

# Step 3: Install ITP service Python dependencies
ITP_REQ="$PLUGIN_DIR/itp-service/requirements.txt"
if [ -f "$ITP_REQ" ]; then
  echo '[3/3] Installing ITP service Python dependencies...'
  pip install -q -r "$ITP_REQ"
  echo '  -> ITP service deps installed'
else
  echo '[3/3] No itp-service/requirements.txt found — skipping'
fi

echo ''
echo 'AZPowers-Skills installed successfully!'
echo ''
echo 'Next steps:'
echo "  1. Start ITP service:  bash $PLUGIN_DIR/itp-service/start.sh"
echo "  2. Run smoke test:     node $PLUGIN_DIR/scripts/smoke-test.mjs"
echo "  3. Run verify:         bash $PLUGIN_DIR/scripts/verify.sh"
