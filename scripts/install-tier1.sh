#!/usr/bin/env bash
# =============================================================================
# AZPowers-Skills — Tier 1 Rust Native Acceleration Installer
# =============================================================================
# Installs Rust to a persistent location inside the Agent Zero data volume
# (/a0/usr/.rust/) so it survives container restarts, then builds the
# clawpowers .node addon for maximum performance.
#
# Use cases: Crypto trading agents, Polymarket bots, Parallel Swarm workloads
# that benefit from native secp256k1, Keccak-256, ECDSA, and vector compression.
#
# After running: getActiveTier() returns 'native' instead of 'wasm'
# Performance: ~3–10× faster crypto ops vs WASM Tier 2
#
# Usage:
#   bash scripts/install-tier1.sh              # install + build
#   bash scripts/install-tier1.sh --verify     # check current tier only
#   bash scripts/install-tier1.sh --build-only # skip rustup, just rebuild
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CPS_REPO="$PROJECT_DIR/clawpowers-skills-repo"

# ── Persistent Rust installation inside the A0 volume ─────────────────────────
# /a0/usr/ is mounted as a Docker volume — Rust installed here survives restarts.
RUST_HOME="/a0/usr/.rust"
export RUSTUP_HOME="$RUST_HOME/rustup"
export CARGO_HOME="$RUST_HOME/cargo"
export PATH="$CARGO_HOME/bin:$PATH"

# Colors
GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; RED=$'\033[0;31m'; NC=$'\033[0m'
info()    { echo -e "${GREEN}[tier1]${NC} $*"; }
warn()    { echo -e "${YELLOW}[tier1]${NC} $*"; }
error()   { echo -e "${RED}[tier1]${NC} $*"; }

# ── --verify shortcut ──────────────────────────────────────────────────────────
if [[ "${1:-}" == "--verify" ]]; then
  info "Checking active CPS tier..."
  if command -v node >/dev/null 2>&1 && [[ -f "$CPS_REPO/dist/index.js" ]]; then
    node --input-type=module <<'JSEOF'
import { getActiveTier, isNativeAvailable, isWasmAvailable, getCapabilitySummary } from '/a0/usr/projects/adapt_clawpowers-skills_to_a0/clawpowers-skills-repo/dist/index.js';
console.log('Active tier :', getActiveTier());
console.log('Native (.node):', isNativeAvailable());
console.log('WASM         :', isWasmAvailable());
console.log('Summary      :', JSON.stringify(getCapabilitySummary(), null, 2));
JSEOF
  else
    warn "CPS dist not found — run install.sh first"
  fi
  exit 0
fi

# ── Step 1: Install Rust (or reuse existing) ───────────────────────────────────
install_rust() {
  if command -v rustc >/dev/null 2>&1; then
    RUST_VER=$(rustc --version)
    info "Rust already active: $RUST_VER"
    return 0
  fi

  info "Installing Rust to persistent location: $RUST_HOME"
  info "  RUSTUP_HOME=$RUSTUP_HOME"
  info "  CARGO_HOME=$CARGO_HOME"

  mkdir -p "$RUSTUP_HOME" "$CARGO_HOME"

  # Download and run rustup (non-interactive, stable toolchain)
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs |     sh -s -- -y       --no-modify-path       --default-toolchain stable       --profile minimal       2>&1 | grep -v '^$'

  # Verify
  if ! command -v rustc >/dev/null 2>&1; then
    error "Rust install failed — rustc not found after install"
    exit 1
  fi

  info "Rust installed: $(rustc --version)"

  # Write environment activation file for future sessions
  ACTIVATE_FILE="/a0/usr/.rust/env.sh"
  cat > "$ACTIVATE_FILE" << ENVEOF
# AZPowers-Skills Tier 1 — Rust environment
# Source this file or add to ~/.bashrc for persistence across sessions:
#   source /a0/usr/.rust/env.sh
export RUSTUP_HOME="$RUSTUP_HOME"
export CARGO_HOME="$CARGO_HOME"
export PATH="$CARGO_HOME/bin:PATH"
ENVEOF
  info "Environment saved to $ACTIVATE_FILE"
  info "To persist across new terminals: echo 'source /a0/usr/.rust/env.sh' >> ~/.bashrc"
}

if [[ "${1:-}" != "--build-only" ]]; then
  install_rust
fi

# ── Step 2: Ensure CPS repo is present ────────────────────────────────────────
if [[ ! -d "$CPS_REPO/native/ffi" ]]; then
  error "CPS repo not found at $CPS_REPO"
  error "Run scripts/install.sh first to set up the CPS repository"
  exit 1
fi

# ── Step 3: Build the .node addon ─────────────────────────────────────────────
info "Building Tier 1 native .node addon..."
info "  Source: $CPS_REPO/native/ffi"

cd "$CPS_REPO"

# Install build dependencies for napi-rs
info "Installing build dependencies..."
apt-get install -y --no-install-recommends   build-essential pkg-config libssl-dev   >/dev/null 2>&1 || warn "apt-get failed — build tools may already be present"

# Build the full native workspace
info "Running cargo build --release (this takes 3–10 minutes on first build)..."
cd "$CPS_REPO/native"
cargo build --release --workspace 2>&1 |   grep -E 'Compiling|Finished|error|warning.*unused' |   tail -20 || {
    error "Cargo build failed"
    exit 1
  }

# ── Step 4: Copy .node to where CPS loader expects it ─────────────────────────
# napi-rs cdylib output is libclawpowers_ffi.so on Linux
FFI_SO="$CPS_REPO/native/target/release/libclawpowers_ffi.so"
FFI_NODE_DEST="$CPS_REPO/native/ffi/index.node"

if [[ -f "$FFI_SO" ]]; then
  cp "$FFI_SO" "$FFI_NODE_DEST"
  info "Copied: $FFI_SO → $FFI_NODE_DEST"
else
  # napi-rs may also output directly as .node
  NAPI_NODE="$CPS_REPO/native/target/release/clawpowers_ffi.node"
  if [[ -f "$NAPI_NODE" ]]; then
    cp "$NAPI_NODE" "$FFI_NODE_DEST"
    info "Copied: $NAPI_NODE → $FFI_NODE_DEST"
  else
    error "Build output not found — expected one of:"
    error "  $FFI_SO"
    error "  $NAPI_NODE"
    ls "$CPS_REPO/native/target/release/" | grep -E '\.so|\.node' | head -10 || true
    exit 1
  fi
fi

# ── Step 5: Verify Tier 1 is now active ───────────────────────────────────────
info "Verifying Tier 1 activation..."
TIER=$(node --input-type=module << 'JSEOF' 2>/dev/null
import { getActiveTier, isNativeAvailable } from '/a0/usr/projects/adapt_clawpowers-skills_to_a0/clawpowers-skills-repo/dist/index.js';
console.log(getActiveTier() + '|' + isNativeAvailable());
JSEOF
)

ACTIVE="${TIER%%|*}"
NATIVE_OK="${TIER##*|}"

if [[ "$ACTIVE" == "native" && "$NATIVE_OK" == "true" ]]; then
  info ""
  info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  info " ✅  Tier 1 ACTIVE — Native Rust acceleration"
  info "     .node path: $FFI_NODE_DEST"
  info "     Active tier: $ACTIVE"
  info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  info ""
  info "Capabilities now running in native Rust:"
  info "  • secp256k1 ECDSA wallet generation & signing"
  info "  • Keccak-256 + SHA-256 hashing"
  info "  • EVM / MetaMask-compatible address derivation"
  info "  • Native canonical store (sled backend)"
  info "  • Vector compression (trading/swarm workloads)"
  info "  • x402 payment header construction"
  info "  • Write security firewall"
  info ""
  info "The .node binary is persistent at:"
  info "  $FFI_NODE_DEST"
  info ""
  info "Rust toolchain is persistent at:"
  info "  $RUST_HOME"
  info ""
  info "To activate Rust in new terminals:"
  info "  source /a0/usr/.rust/env.sh"
else
  warn "Tier 1 not active after build (active=$ACTIVE, native=$NATIVE_OK)"
  warn "The .node may need to be reloaded — try restarting the Node process"
  warn "Check build output for errors"
  exit 1
fi
