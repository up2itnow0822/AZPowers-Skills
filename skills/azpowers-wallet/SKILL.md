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

---

## A0T Token — Agent Zero Native Token

A0T is the native governance and utility token of Agent Zero, deployed on **Base** (Ethereum L2).

```javascript
// A0T token constants
const A0T = {
  name:     'Agent Zero Token',
  symbol:   'A0T',
  contract: '0xCc4ADB618253ED0d4d8A188fB901d70C54735e03',
  chain:    'base',
  chainId:  8453,
  decimals: 18,
  supply:   1_000_000,
  dex:      ['Aerodrome', 'Uniswap'],
  info:     'https://www.agent-zero.ai/p/token/',
};
```

### Generate a Base wallet for A0T

```javascript
import { generateWallet } from 'file://~/.clawpowers/runtime/node_modules/clawpowers/dist/index.js';
import os from 'os';
import path from 'path';

// Generate wallet on Base (A0T's network)
const wallet = await generateWallet({
  chain: 'base',
  dataDir: path.join(os.homedir(), '.clawpowers', 'wallet'),
});

console.log('A0T wallet address:', wallet.address);
console.log('Network: Base (chainId 8453)');
console.log('Ready to send/receive A0T at:', wallet.address);
```

### Sign governance messages with your A0T wallet

```javascript
import { generateWallet, signMessage } from 'file://~/.clawpowers/runtime/node_modules/clawpowers/dist/index.js';
import os from 'os';
import path from 'path';

const wallet = await generateWallet({
  chain: 'base',
  dataDir: path.join(os.homedir(), '.clawpowers', 'wallet'),
});

// Sign a governance vote or identity proof
const vote = JSON.stringify({ proposal: 'enable-rag-memory', vote: 'yes', timestamp: Date.now() });
const signed = await signMessage(vote, wallet.keyFile, '');

console.log('Governance vote signed by:', signed.address);
console.log('Signature:', signed.signature);
// Submit signed.address + signed.signature to governance contract
```

### Check A0T balance (requires ethers.js)

```bash
# Install ethers.js if not present
npm install ethers --prefix ~/.clawpowers/runtime
```

```javascript
import { ethers } from 'file://~/.clawpowers/runtime/node_modules/ethers/dist/ethers.min.mjs';

const A0T_CONTRACT = '0xCc4ADB618253ED0d4d8A188fB901d70C54735e03';
const BASE_RPC     = 'https://mainnet.base.org';
const ERC20_ABI    = [
  'function balanceOf(address) view returns (uint256)',
  'function decimals() view returns (uint8)',
  'function symbol() view returns (string)',
];

const provider = new ethers.JsonRpcProvider(BASE_RPC);
const token    = new ethers.Contract(A0T_CONTRACT, ERC20_ABI, provider);

async function getA0TBalance(address) {
  const [raw, decimals, symbol] = await Promise.all([
    token.balanceOf(address),
    token.decimals(),
    token.symbol(),
  ]);
  const balance = ethers.formatUnits(raw, decimals);
  console.log(`Balance: ${balance} ${symbol}`);
  return balance;
}

// Example: check balance of any address
await getA0TBalance('0xYourWalletAddressHere');
```

### A0T Token Use Cases for Agents

| Use Case | Description |
|---|---|
| **Governance voting** | Sign proposals with wallet key, submit to governance contract |
| **Venice AI access** | A0T holders get free private AI API key |
| **Staking / locking** | Lock A0T for enhanced governance weight |
| **Agent identity** | Use wallet address as verifiable agent identity on Base |
| **x402 payments** | Combine with `azpowers-payments` for A0T-denominated service payments |

### Resources

- Token info: https://www.agent-zero.ai/p/token/
- BaseScan: https://basescan.org/token/0xCc4ADB618253ED0d4d8A188fB901d70C54735e03
- Uniswap: https://app.uniswap.org/swap?chain=base&outputCurrency=0xCc4ADB618253ED0d4d8A188fB901d70C54735e03
- Aerodrome: https://aerodrome.finance
