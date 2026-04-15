# AZPowers-Skills × Agent Zero

Adapter layer integrating [AZPowers-Skills](https://github.com/clawpowers/clawpowers-skills) v2.2.6 into [Agent Zero](https://github.com/frdel/agent-zero) as loadable skills and a system-prompt plugin.

---

## What is AZPowers-Skills?

AZPowers-Skills (CPS) is a TypeScript/Node.js library of agent capability modules:

- **3-tier persistent memory** — Working, Episodic, Procedural memory with checkpoints
- **x402 payment handling** — HTTP 402 detection, spending limits, payment execution
- **Ethereum wallet operations** — WASM-accelerated key generation and signing
- **Recursive Self-Improvement (RSI)** — Metrics, hypotheses, A/B tests, audit log
- **Swarm coordination** — Task classification, concurrency, token budgets
- **ITP message compression** — Save tokens on inter-agent messages
- **Native crypto** — SHA-256, Keccak-256, secp256k1 ECDSA, EVM address derivation

CPS uses a **3-tier acceleration model**: Rust native (.node) → WASM → TypeScript fallback. In Agent Zero's Docker environment, **WASM (Tier 2)** is active.

---

## Quick Start

```bash
# 1. Build CPS and create runtime directories
bash /a0/usr/projects/adapt_clawpowers-skills_to_a0/scripts/install.sh

# 2. (Optional) Start ITP compression service
bash /a0/usr/projects/adapt_clawpowers-skills_to_a0/itp-service/start.sh

# 3. Load a skill in Agent Zero
# In any agent context:
skills_tool:load azpowers-memory
```

---

## Available Skills

All 7 skills are installed in `/a0/usr/skills/` and discoverable via `skills_tool:search`.

| Skill Name | Description | Key Classes / Functions |
|---|---|---|
| `azpowers-memory` | Persistent memory across sessions | `WorkingMemoryManager`, `EpisodicMemory`, `ProceduralMemory`, `CheckpointManager`, `ContextInjector` |
| `azpowers-payments` | HTTP 402 payment handling | `detect402`, `SpendingPolicy`, `PaymentExecutor`, `createPaymentHeader` |
| `azpowers-wallet` | Ethereum/EVM wallet operations | `generateWallet`, `importWallet`, `signMessage`, `WalletManager` |
| `azpowers-rsi` | Self-improvement engine | `MetricsCollector`, `HypothesisEngine`, `MutationEngine`, `ABTestManager`, `RSIAuditLog` |
| `azpowers-swarm` | Parallel task coordination | `classifyHeuristic`, `classifyTasks`, `selectModel`, `ConcurrencyManager`, `TokenPool` |
| `azpowers-itp` | Inter-agent message compression | `itpEncode`, `itpDecode`, `itpHealthCheck`, `encodeTaskDescription`, `decodeSwarmResult` |
| `azpowers-native` | Cryptographic primitives | `computeSha256`, `keccak256Digest`, `deriveEthereumAddress`, `signEcdsa`, `verifyEcdsa` |

---

## Usage Examples

### Persistent Memory

```javascript
import { WorkingMemoryManager, EpisodicMemory } from 'file:///a0/usr/projects/adapt_clawpowers-skills_to_a0/clawpowers-skills-repo/dist/index.js';
import os from 'os'; import path from 'path';

// Working memory (in-process, current task)
const mgr = new WorkingMemoryManager();
const goal = { taskId: 'task-1', description: 'Analyze logs', constraints: [], successCriteria: ['report done'], createdAt: new Date().toISOString(), source: 'cli' };
const mem = mgr.create('task-1', goal);
mgr.addIntermediateOutput('step-1', 'logs analyzed');
console.log(mgr.getSnapshot().intermediateOutputs);

// Episodic memory (persistent across sessions)
const episodic = new EpisodicMemory(path.join(os.homedir(), '.clawpowers', 'memory', 'episodic.json'));
await episodic.add({ taskId: 'task-1', timestamp: new Date().toISOString(), description: 'Analyzed logs', outcome: 'success', lessonsLearned: ['Check timestamps first'], skillsUsed: ['azpowers-native'], durationMs: 3200, tags: ['logs'] });
const history = await episodic.readAll();
console.log('Memory entries:', history.length);
```

### Wallet Generation

```javascript
import { generateWallet, getActiveTier } from 'file:///a0/usr/projects/adapt_clawpowers-skills_to_a0/clawpowers-skills-repo/dist/index.js';
import os from 'os'; import path from 'path';

console.log('Tier:', await getActiveTier()); // 'wasm'

const wallet = await generateWallet({
  chain: 'base',
  dataDir: path.join(os.homedir(), '.clawpowers', 'wallet'),
});
console.log('Address:', wallet.address); // 0x...
```

### HTTP 402 Payment Detection

```javascript
import { detect402 } from 'file:///a0/usr/projects/adapt_clawpowers-skills_to_a0/clawpowers-skills-repo/dist/index.js';

// Simulate detecting a payment-required API response
const response = await fetch('https://api.paid-service.example.com/data');
const paymentRequired = detect402(response);
if (paymentRequired) {
  console.log('Payment needed:', paymentRequired.amount, paymentRequired.currency);
}
```

### Native Tier Check

```javascript
import { getActiveTier, isWasmAvailable, computeSha256 } from 'file:///a0/usr/projects/adapt_clawpowers-skills_to_a0/clawpowers-skills-repo/dist/index.js';

const tier = await getActiveTier();      // 'wasm' in A0 Docker
const wasm = await isWasmAvailable();    // true
const hash = await computeSha256('hello world');
console.log(`Tier: ${tier}, WASM: ${wasm}, hash: ${hash.slice(0,16)}...`);
```

---

## ITP Service

The **Identical Twins Protocol (ITP)** is an optional FastAPI service on port 8100 that compresses agent-to-agent messages using a shorthand codebook, saving tokens on every inter-agent communication.

### Start the service

```bash
bash /a0/usr/projects/adapt_clawpowers-skills_to_a0/itp-service/start.sh
# Service is idempotent — safe to call if already running
```

### Usage

```javascript
import { itpEncode, itpDecode, itpHealthCheck } from 'file:///a0/usr/projects/adapt_clawpowers-skills_to_a0/clawpowers-skills-repo/dist/index.js';

// All functions degrade gracefully if service is down
const isUp = await itpHealthCheck();
const result = await itpEncode('Please analyze and synthesize the performance report', 'agent-1');
// result.wasCompressed = true, result.encoded = 'ITP:ANL+SYN+PERF+RPT'
```

### Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Health check + stats |
| `/tools/encode` | POST | Compress message |
| `/tools/decode` | POST | Decompress message |
| `/tools/stats` | GET | Compression analytics |
| `/tools/codebook` | GET | View codebook |
| `/tools/history` | GET | Recent message history |

### ITP Codebook (partial)

`ANL`=analyze, `SYN`=synthesize, `OPT`=optimize, `DBG`=debug, `RPT`=report, `PLN`=plan, `EXE`=execute, `REV`=review, `TST`=test, `DOC`=document, `SRH`=search, `VAL`=validate, `GEN`=generate, `TRN`=transform, `AGG`=aggregate, `STS/OK`=success, `STS/ERR`=error, `DAT/JSON`=json data, `PERF`=performance, `TRD`=trading, `SYS`=system

Encoded format: `ITP:<code1>+<code2>+...` (only when savings > 10%)

---

## Tier Architecture

CPS automatically selects the best available cryptographic acceleration tier at runtime:

```
Tier 1 — Rust native (.node addon)
  └── Requires: Rust toolchain + cargo build
  └── A0 Docker: UNAVAILABLE (no Rust toolchain)
  └── Provides: maximum performance

Tier 2 — WASM (WebAssembly)
  └── Requires: pre-built clawpowers_wasm.js (included in repo)
  └── A0 Docker: ACTIVE ✓
  └── Location: native/wasm/pkg-node/clawpowers_wasm.js (487KB)
  └── Provides: keccak256, sha256, secp256k1, fee calc, vector compression

Tier 3 — TypeScript fallback
  └── Requires: nothing (pure JS/TS)
  └── Always available as final fallback
  └── Provides: all operations, lower performance
```

Check active tier:
```javascript
import { getActiveTier, getCapabilitySummary } from 'file:///a0/usr/projects/adapt_clawpowers-skills_to_a0/clawpowers-skills-repo/dist/index.js';
console.log(await getActiveTier());          // 'wasm'
console.log(await getCapabilitySummary());   // full tier inventory
```

---

## Project Structure

```
/a0/usr/projects/adapt_clawpowers-skills_to_a0/
├── PLAN.md                          — Implementation plan
├── README.md                        — This file
├── itp-service/                     — ITP FastAPI compression service
│   ├── itp_server.py                — FastAPI app (port 8100)
│   ├── requirements.txt
│   └── start.sh
├── a0-skills/                       — Canonical SKILL.md files
│   └── clawpowers-{module}/SKILL.md
├── a0-plugin/                       — A0 plugin YAML
│   └── azpowers_skills.yaml
└── scripts/
    ├── install.sh                   — Build CPS + setup runtime dirs
    ├── smoke-test.mjs               — Node.js test all 7 modules
    └── verify.sh                    — Full verification script

# Deployed to Agent Zero:
/a0/usr/skills/clawpowers-{module}/SKILL.md    — Loadable by skills_tool
/a0/usr/plugins/azpowers_skills.yaml          — Auto-injected into prompts
```

---

## Verification

```bash
# Run full verification (checks Node, dist, WASM, smoke test, skills, plugin)
bash /a0/usr/projects/adapt_clawpowers-skills_to_a0/scripts/verify.sh

# Run smoke test only (7 module tests)
node /a0/usr/projects/adapt_clawpowers-skills_to_a0/scripts/smoke-test.mjs

# Check ITP service health
curl http://localhost:8100/health
```

---

## License

AZPowers-Skills is released under the **Business Source License 1.1 (BSL-1.1)**.

- Free for non-commercial and evaluation use
- Commercial use requires a license from ClawPowers
- See `clawpowers-skills-repo/LICENSE` and `clawpowers-skills-repo/LICENSING.md` for details

This adapter layer (files in this directory, excluding the `clawpowers-skills-repo/` subdirectory) is provided as-is for integration purposes.

---

## CPS Version

- **CPS Version:** 2.2.6
- **CPS Path:** `/a0/usr/projects/adapt_clawpowers-skills_to_a0/clawpowers-skills-repo/`
- **Built dist:** `dist/index.js` (107KB ESM) + `dist/index.d.ts` (50KB)
- **WASM:** `native/wasm/pkg-node/clawpowers_wasm.js` (487KB)
- **Node requirement:** ≥20 (running: v22.22.0)
