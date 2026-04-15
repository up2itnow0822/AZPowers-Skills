#!/bin/bash
# AZPowers-Skills × Agent Zero — Verification Script
# Checks all components are correctly set up.

set -o pipefail
PASS=0
FAIL=0
WARN=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_SRC="$(cd "$SCRIPT_DIR/.." && pwd)"
CLP_RUNTIME="$HOME/.clawpowers/runtime"

green()  { echo -e "\033[0;32m  PASS\033[0m $1"; ((PASS++)); }
red()    { echo -e "\033[0;31m  FAIL\033[0m $1"; ((FAIL++)); }
yellow() { echo -e "\033[0;33m  WARN\033[0m $1"; ((WARN++)); }

echo '=== AZPowers-Skills Verification ==='
echo ''

# ── 1. Node version ──────────────────────────────────────────────────────────
NODE_VER=$(node --version 2>/dev/null | sed 's/v//')
NODE_MAJOR=$(echo "$NODE_VER" | cut -d. -f1)
if [ -z "$NODE_VER" ]; then
  red "Node.js not found"
elif [ "$NODE_MAJOR" -lt 20 ]; then
  red "Node.js v${NODE_VER} < v20 (required ≥20)"
else
  green "Node.js v${NODE_VER} (≥20 required)"
fi

# ── 2. clawpowers npm dist ────────────────────────────────────────────────────
NPM_DIST="$CLP_RUNTIME/node_modules/clawpowers/dist/index.js"
LOCAL_DIST="$PLUGIN_SRC/clawpowers-skills-repo/dist/index.js"
if [ -f "$NPM_DIST" ]; then
  SIZE=$(du -k "$NPM_DIST" | cut -f1)
  green "clawpowers dist (npm): $NPM_DIST (${SIZE}KB)"
elif [ -f "$LOCAL_DIST" ]; then
  SIZE=$(du -k "$LOCAL_DIST" | cut -f1)
  yellow "clawpowers dist (local dev): $LOCAL_DIST (${SIZE}KB) — run install.sh for npm install"
else
  red "clawpowers dist NOT FOUND — run scripts/install.sh"
fi

# ── 3. WASM file ─────────────────────────────────────────────────────────────
NPM_WASM="$CLP_RUNTIME/node_modules/clawpowers/native/wasm/pkg-node/clawpowers_wasm.js"
LOCAL_WASM="$PLUGIN_SRC/clawpowers-skills-repo/native/wasm/pkg-node/clawpowers_wasm.js"
if [ -f "$NPM_WASM" ]; then
  green "WASM (npm): clawpowers_wasm.js exists"
elif [ -f "$LOCAL_WASM" ]; then
  yellow "WASM (local dev): clawpowers_wasm.js exists — run install.sh for npm install"
else
  red "WASM file NOT FOUND"
fi

# ── 4. Run smoke test ────────────────────────────────────────────────────────
echo ''
echo 'Running smoke-test.mjs...'
if node "$SCRIPT_DIR/smoke-test.mjs"; then
  green "smoke-test.mjs: all 7 modules passed"
else
  red "smoke-test.mjs: one or more modules failed"
fi

# ── 5. ITP server check (optional) ───────────────────────────────────────────
echo ''
ITP_HEALTH=$(curl -sf http://localhost:8100/health 2>/dev/null)
if [ -n "$ITP_HEALTH" ]; then
  ITP_STATUS=$(echo "$ITP_HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))" 2>/dev/null)
  green "ITP service running on port 8100 (status=${ITP_STATUS})"
else
  yellow "ITP service not running on port 8100 (optional — start with itp-service/start.sh)"
fi

# ── 6. Skills in /a0/usr/skills/ ─────────────────────────────────────────────
echo ''
echo 'AZPowers skills in /a0/usr/skills/:'
SKILL_COUNT=0
for skill in azpowers-memory azpowers-payments azpowers-wallet azpowers-rsi azpowers-swarm azpowers-itp azpowers-native; do
  SKILL_FILE="/a0/usr/skills/$skill/SKILL.md"
  if [ -f "$SKILL_FILE" ]; then
    echo "    ✓ $skill"
    ((SKILL_COUNT++))
  else
    echo "    ✗ $skill — MISSING"
    ((FAIL++))
  fi
done
if [ "$SKILL_COUNT" -eq 7 ]; then
  green "All 7 skills present in /a0/usr/skills/"
else
  red "Only ${SKILL_COUNT}/7 skills found in /a0/usr/skills/"
fi

# ── 7. Plugin directory check ────────────────────────────────────────────────
PLUGIN_DIR=/a0/usr/plugins/azpowers_skills
PLUGIN_YAML="$PLUGIN_DIR/plugin.yaml"
if [ -f "$PLUGIN_YAML" ]; then
  green "Plugin directory present: $PLUGIN_YAML"
else
  red "Plugin NOT FOUND: $PLUGIN_YAML"
fi

# Check for stale flat plugin file
if [ -f /a0/usr/plugins/azpowers_skills.yaml ]; then
  yellow "Stale flat plugin file found: /a0/usr/plugins/azpowers_skills.yaml — remove it"
fi

# ── 8. Extension check ───────────────────────────────────────────────────────
EXT_FILE="$PLUGIN_DIR/extensions/python/agent_system_prompt/end/10_azpowers.py"
if [ -f "$EXT_FILE" ]; then
  green "Extension present: extensions/python/agent_system_prompt/end/10_azpowers.py"
else
  red "Extension NOT FOUND: $EXT_FILE"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo ''
echo '=== Summary ==='
echo "  PASS: $PASS"
echo "  FAIL: $FAIL"
echo "  WARN: $WARN"
echo ''
if [ "$FAIL" -eq 0 ]; then
  echo 'All checks passed! AZPowers-Skills is ready for Agent Zero.'
  exit 0
else
  echo "${FAIL} check(s) failed. See output above for details."
  exit 1
fi
