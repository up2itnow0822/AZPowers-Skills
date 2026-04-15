---
name: azpowers-wallet
description: Use when you need to generate an Ethereum/EVM wallet, import from private key, or sign messages for agent identity or payment authorization
version: 1.0.0
author: AZPowers-Skills v2.2.6 adapter
requires:
  tools: [node]
---

# ClawPowers Wallet — Ethereum/EVM Wallet Operations

Generate, import, and manage Ethereum wallets with WASM-accelerated cryptography (keccak256, secp256k1).

**Active tier:** WASM (Tier 2) — uses pre-built `clawpowers_wasm.js` for keccak256 and secp256k1

**WalletConfig:** `{ chain: 'base' | 'ethereum' | 'polygon', dataDir: string }`

```javascript
const A0PS = 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
```

---

## generateWallet

Create a new Ethereum wallet (address + public key + key file).

```javascript
import {
  generateWallet
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
import os from 'os';
import path from 'path';

// Generate a new wallet on the 'base' chain
const wallet = await generateWallet({
  chain: 'base',
  dataDir: path.join(os.homedir(), '.clawpowers', 'wallet'),
});

console.log('Address:', wallet.address);     // 0x + 40 hex chars
console.log('Chain:', wallet.chain);          // 'base'
console.log('Key file:', wallet.keyFile);     // path to saved key file
console.log('Created at:', wallet.createdAt);

// Verify address format
const valid = /^0x[0-9a-fA-F]{40}$/.test(wallet.address);
console.log('Valid EVM address:', valid); // true
```

---

## importWallet

Import an existing Ethereum wallet from a hex private key.

```javascript
import {
  importWallet
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
import os from 'os';
import path from 'path';

// Import from raw hex private key (64 hex chars, no 0x prefix needed)
const privateKey = 'ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80';

const wallet = await importWallet(privateKey, {
  chain: 'ethereum',
  dataDir: path.join(os.homedir(), '.clawpowers', 'wallet'),
});

console.log('Imported address:', wallet.address);
// 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 (Hardhat account 0)
```

---

## signMessage

Sign a string message with a wallet key file (for identity proof or payment auth).

```javascript
import {
  signMessage, generateWallet
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
import os from 'os';
import path from 'path';

// First generate a wallet
const wallet = await generateWallet({
  chain: 'base',
  dataDir: path.join(os.homedir(), '.clawpowers', 'wallet'),
});

// Sign a message — returns SignedMessage {signature, messageHash, address}
const signed = await signMessage('Hello from agent', wallet.keyFile, '');
console.log('Signature:', signed.signature);
console.log('Message hash:', signed.messageHash);
console.log('Signer address:', signed.address);
```

---

## WalletManager

Higher-level class that wraps generateWallet / importWallet / signMessage.

```javascript
import {
  WalletManager
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
import os from 'os';
import path from 'path';

const manager = new WalletManager({
  chain: 'base',
  dataDir: path.join(os.homedir(), '.clawpowers', 'wallet'),
});

// Generate and auto-save wallet
const wallet = await manager.generate();
console.log('Generated address:', wallet.address);

// Import from private key
const imported = await manager.import('ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80');
console.log('Imported address:', imported.address);

// Sign a message via manager (passphrase = '' if unencrypted)
const signature = await manager.sign('agent identity proof', wallet, '');
console.log('Signature:', signature);
```

---

## Tier Info

The wallet operations use the best available cryptographic tier:

```javascript
import {
  getActiveTier, isWasmAvailable, getCapabilitySummary
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

const tier = await getActiveTier();
console.log('Active tier:', tier);
// Expected in A0 Docker: 'wasm' (Tier 2)

const wasmOk = await isWasmAvailable();
console.log('WASM available:', wasmOk); // true

const summary = await getCapabilitySummary();
console.log('Capabilities:', JSON.stringify(summary, null, 2));
```

---

## Quick Reference

| Function/Class | Signature | Purpose |
|---|---|---|
| `generateWallet(config)` | `({chain, dataDir})` | Create new Ethereum wallet |
| `importWallet(privateKey, config)` | `(string, {chain, dataDir})` | Import from hex private key |
| `signMessage(message, keyFile, passphrase)` | `(string, string, string)` | Sign string message |
| `WalletManager(config)` | `({chain, dataDir})` | Higher-level wallet manager |
| `deriveEthereumAddress(privateKey)` | `(string)` | Derive address only (no file I/O) |

## Notes
- `WalletConfig`: `{ chain: 'base' | 'ethereum' | 'polygon', dataDir: string }`
- Key files stored in `dataDir/` (JSON keystore format)
- In A0 Docker: WASM tier active (Tier 2) — keccak256 via pre-built WASM
- No Rust native addon required
- For raw cryptographic operations only, see `azpowers-native` skill
