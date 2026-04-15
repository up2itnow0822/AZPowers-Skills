---
name: azpowers-native
description: Use when you need cryptographic operations — SHA-256 hashing, Keccak-256 (Ethereum), secp256k1 ECDSA signing/verification, or EVM address derivation
version: 1.0.0
author: AZPowers-Skills v2.2.6 adapter
requires:
  tools: [node]
---

# ClawPowers Native — Cryptographic Primitives

SHA-256, Keccak-256 (Ethereum), secp256k1 ECDSA signing/verification, EVM address derivation, fee calculation — with automatic tier selection.

**Tier architecture:**
- **Tier 1 (Rust .node):** Unavailable in A0 Docker (no Rust toolchain)
- **Tier 2 (WASM):** Active — pre-built `clawpowers_wasm.js` via `pkg-node/`
- **Tier 3 (TypeScript):** Always available fallback

```javascript
const CPS = 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
```

---

## getActiveTier / isWasmAvailable

Check which cryptographic acceleration tier is active.

```javascript
import {
  getActiveTier, isWasmAvailable, isNativeAvailable
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

// Get active tier: 'native' | 'wasm' | 'ts'
const tier = await getActiveTier();
console.log('Active tier:', tier); // Expected: 'wasm' in A0 Docker

// Check WASM availability
const wasmOk = await isWasmAvailable();
console.log('WASM available:', wasmOk); // true

// Check native .node addon (Rust)
const nativeOk = await isNativeAvailable();
console.log('Native available:', nativeOk); // false in Docker
```

---

## getCapabilitySummary

Show all available modules per tier.

```javascript
import {
  getCapabilitySummary
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

const summary = await getCapabilitySummary();
console.log(JSON.stringify(summary, null, 2));
// Example output:
// {
//   "activeTier": "wasm",
//   "wasm": {
//     "available": true,
//     "modules": ["sha256", "keccak256", "secp256k1", "fee", ...]
//   },
//   "native": { "available": false },
//   "ts": { "available": true, "modules": ["all"] }
// }
```

---

## computeSha256

Hash content with SHA-256.

```javascript
import {
  computeSha256
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

// Returns hex string (64 chars)
const hash = await computeSha256('hello world');
console.log('SHA-256:', hash);
// b94d27b9934d3e08a52e52d7da7dabfac484efe04294e576f4c...

// Hash a JSON payload
const payload = JSON.stringify({ action: 'transfer', amount: '1.5', to: '0xabc' });
const payloadHash = await computeSha256(payload);
console.log('Payload hash:', payloadHash);
```

---

## digestForWalletAddress / keccak256Digest

Keccak-256 hashing for Ethereum address derivation.

```javascript
import {
  digestForWalletAddress, keccak256Digest
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

// Keccak-256 digest optimized for wallet address derivation
// Input: hex-encoded public key bytes
const pubKeyHex = 'your_uncompressed_public_key_hex_without_04_prefix';
const digest = await digestForWalletAddress(pubKeyHex);
console.log('Address digest:', digest);
// Take last 20 bytes + 0x prefix = Ethereum address

// Raw keccak256 on arbitrary content
const raw = await keccak256Digest('arbitrary content to hash');
console.log('Keccak-256:', raw);
```

---

## deriveEthereumAddress

Derive an EVM address from a private key (no file I/O).

```javascript
import {
  deriveEthereumAddress
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

// Derive Ethereum address from private key hex
const privateKeyHex = 'your_64_char_hex_private_key';
const address = await deriveEthereumAddress(privateKeyHex);
console.log('EVM address:', address);
// e.g. '0xAbCd1234...' (0x + 40 hex chars)

// Verify address format
const isValidAddress = /^0x[0-9a-fA-F]{40}$/.test(address);
console.log('Valid EVM address format:', isValidAddress); // true
```

---

## signEcdsa / verifyEcdsa

Sign and verify with secp256k1 ECDSA (same curve as Ethereum).

```javascript
import {
  signEcdsa, verifyEcdsa
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

const privateKeyHex = 'your_64_char_hex_private_key';
const message = 'agent task authorization';

// Sign message (returns hex signature)
const signature = await signEcdsa(message, privateKeyHex);
console.log('Signature:', signature);

// Verify signature with public key
const publicKeyHex = 'your_public_key_hex';
const valid = await verifyEcdsa(message, signature, publicKeyHex);
console.log('Signature valid:', valid); // true
```

---

## tokenAmountFromHuman / calculateFee

Convert human-readable token amounts and calculate transaction fees.

```javascript
import {
  tokenAmountFromHuman, calculateFee
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

// Convert human amount to token units (e.g. USDC has 6 decimals)
const units = await tokenAmountFromHuman('1.5', 6);
console.log('Token units:', units); // 1500000n (BigInt)

const usdcAmount = await tokenAmountFromHuman('0.001', 6);
console.log('0.001 USDC in units:', usdcAmount); // 1000n

// Calculate transaction fee
const fee = await calculateFee({
  amount: '1000000',    // in token units
  feeBps: 30,          // fee in basis points (30 = 0.30%)
});
console.log('Fee:', fee);
console.log('Fee amount:', fee.feeAmount);
console.log('Net amount:', fee.netAmount);
```

---

## Full Tier Check + Crypto Example

```javascript
import {
  getActiveTier, getCapabilitySummary,
  computeSha256, deriveEthereumAddress, signEcdsa, verifyEcdsa
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

// 1. Check tier
const tier = await getActiveTier();
console.log('=== Crypto Tier:', tier, '===');

// 2. Hash some content
const hash = await computeSha256('ClawPowers agent identity');
console.log('Content hash:', hash);

// 3. Derive address from known test key
const testKey = 'ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80';
const address = await deriveEthereumAddress(testKey);
console.log('Address:', address);
console.log('Valid format:', /^0x[0-9a-fA-F]{40}$/.test(address));
```

---

## Quick Reference

| Function | Returns | Purpose |
|---|---|---|
| `getActiveTier()` | `'native'\|'wasm'\|'ts'` | Active acceleration tier |
| `isWasmAvailable()` | `boolean` | WASM tier check |
| `isNativeAvailable()` | `boolean` | Rust native check |
| `getCapabilitySummary()` | `object` | Full tier + module inventory |
| `computeSha256(content)` | `string` (hex) | SHA-256 hash |
| `digestForWalletAddress(pubKey)` | `string` (hex) | Keccak-256 for address |
| `keccak256Digest(content)` | `string` (hex) | Raw keccak-256 |
| `deriveEthereumAddress(privKey)` | `string` (0x...) | EVM address from private key |
| `signEcdsa(message, privKey)` | `string` (hex sig) | secp256k1 sign |
| `verifyEcdsa(message, sig, pubKey)` | `boolean` | secp256k1 verify |
| `tokenAmountFromHuman(amount, decimals)` | `BigInt` | Human → token units |
| `calculateFee({amount, feeBps})` | `FeeResult` | Fee calculation |

## Notes
- In A0 Docker: Tier 2 (WASM) is active — WASM provides keccak256, sha256, secp256k1, fee calc
- Tier 3 (TypeScript) activates automatically if WASM load fails
- For wallet generation with file persistence, use `azpowers-wallet` skill instead
- Test key `ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80` is the Hardhat default account 0

## Tier 1 (Rust Native) — Easy Button

For maximum performance in trading, Polymarket, or Parallel Swarm workloads, upgrade from WASM to native Rust (~3–10× faster):

```bash
bash scripts/install-tier1.sh
```

This installs Rust to `/a0/usr/.rust/` (persists across container restarts), builds the `clawpowers-ffi` .node addon, and automatically promotes CPS to Tier 1.

Verify after install:
```javascript
import { getActiveTier } from 'clawpowers';
console.log(getActiveTier()); // 'native'
```
