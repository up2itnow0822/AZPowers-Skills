# AZPowers-Skills → Agent Zero Adaptation Plan

**Version:** 1.0  
**Date:** 2026-04-14  
**CPS Version:** 2.2.6  
**Status:** In Progress

## Analysis Summary

### CPS Build Status ✅
- Node v22.22.0 available (CPS requires ≥20)
- `npm install` → 202 packages installed
- `npm run build` → dist/index.js (107 KB ESM), dist/index.d.ts (50 KB) — **BUILD PASSES**
- WASM pre-built: `native/wasm/pkg-node/clawpowers_wasm.js` (487 KB .wasm) — **Tier 2 ready**
- Rust/native .node addon: NOT built (no Cargo/Rust toolchain in Docker) — **Tier 3 TS fallback will activate**
- ITP Python server: **NOT included** in repo — must be created from API spec in SKILL.md

### CPS Capabilities Inventory

| Module | Classes/Functions | A0 Skill Priority |
|--------|------------------|-------------------|
| Memory | WorkingMemoryManager, EpisodicMemory, ProceduralMemory, CheckpointManager, ContextInjector | HIGH |
| Payments | detect402, SpendingPolicy, PaymentExecutor, createPaymentHeader | HIGH |
| Wallet | WalletManager, generateWallet, importWallet, signMessage | HIGH |
| RSI | MetricsCollector, HypothesisEngine, MutationEngine, ABTestManager, RSIAuditLog, AutoResearcher | MEDIUM |
| Swarm | ConcurrencyManager, TokenPool, classifyTasks, selectModel | MEDIUM |
| ITP | encode, decode, healthCheck, encodeTaskDescription, decodeSwarmResult | HIGH (token savings) |
| Native | computeSha256, digestForWalletAddress, keccak256, deriveEthereumAddress, signEcdsa | INTERNAL (used by above) |

### Runtime Tier Assessment
- **Tier 1 (Rust .node):** UNAVAILABLE — no Rust toolchain in A0 Docker container
- **Tier 2 (WASM):** AVAILABLE — pre-built `pkg-node/clawpowers_wasm.js` works with Node v22
- **Tier 3 (TypeScript):** ALWAYS AVAILABLE — full fallback for all operations
- **Expected tier:** WASM (Tier 2) after build, providing: sha256, keccak256, fee calc, vector compression, write firewall, canonical store

## Output Structure

```
/a0/usr/projects/adapt_clawpowers-skills_to_a0/
├── PLAN.md                          ← This file
├── README.md                        ← User-facing documentation
├── itp-service/                     ← ITP FastAPI Python service
│   ├── itp_server.py                ← FastAPI app (port 8100)
│   ├── requirements.txt             ← fastapi, uvicorn, httpx
│   └── start.sh                     ← Launch script
├── a0-skills/                       ← A0 SKILL.md files
│   ├── azpowers-memory/
│   │   └── SKILL.md                 ← 3-tier memory system
│   ├── azpowers-payments/
│   │   └── SKILL.md                 ← x402 payments + spending policy
│   ├── azpowers-wallet/
│   │   └── SKILL.md                 ← Ethereum wallet ops
│   ├── azpowers-rsi/
│   │   └── SKILL.md                 ← RSI self-improvement engine
│   ├── azpowers-swarm/
│   │   └── SKILL.md                 ← Parallel swarm coordination
│   ├── azpowers-itp/
│   │   └── SKILL.md                 ← ITP message compression
│   └── azpowers-native/
│       └── SKILL.md                 ← Native/WASM crypto & hashing
├── a0-plugin/                       ← A0 YAML plugin for auto-injection
│   └── azpowers_skills.yaml       ← Plugin manifest + system prompt injection
├── scripts/
│   ├── install.sh                   ← One-shot: npm install + build CPS
│   ├── verify.sh                    ← Verify all tiers, run smoke tests
│   └── smoke-test.mjs               ← Node.js smoke test for all modules
└── tests/
    ├── test_itp_server.py            ← ITP service tests
    └── smoke_test_skills.sh         ← Shell-based skill load verification
```

## Installation Path

CPS will be installed as a **local npm package** linked from the repo:
```
/a0/usr/projects/adapt_clawpowers-skills_to_a0/clawpowers-skills-repo/  ← source (built)
```

Skills invoke CPS via Node.js scripts that import from the built dist:
```javascript
import { WorkingMemoryManager } from '/a0/usr/projects/adapt_clawpowers-skills_to_a0/clawpowers-skills-repo/dist/index.js'
```

## Implementation Phases

### Phase 0: Environment & Build Verification ✅ COMPLETE
- [x] Node v22.22.0 confirmed
- [x] `npm install` successful (202 packages)
- [x] `npm run build` successful — dist/index.js, dist/index.d.ts
- [x] WASM pre-built confirmed in native/wasm/pkg-node/
- [x] CPS source analysis complete

### Phase 1: ITP Service 🔧
**Priority:** High (enables token savings for all agent communications)  
**Deliverable:** `itp-service/itp_server.py`  

Create FastAPI service implementing:
- `POST /tools/encode` — compress agent messages with codebook
- `POST /tools/decode` — decompress ITP messages
- `GET /health` — health check
- `GET /tools/stats` — compression analytics
- `GET /tools/codebook` — codebook contents
- `GET /tools/history` — message history

Codebook must include:
- Agent operations: ANL (analyze), SYN (synthesize), OPT (optimize), DBG (debug), RPT (report)
- Agent roles: SVC (service), DIR (director), WKR (worker), MON (monitor)
- Status: STS/OK, STS/ERR, STS/UPD, STS/PEND
- Data: DAT/JSON, DAT/TXT, DAT/BIN
- Directions: → (to), ← (from), ↔ (bidirectional)

### Phase 2: A0 SKILL.md Files 🔧
**Priority:** High  
**Deliverable:** 7 SKILL.md files in `a0-skills/`

Each skill must follow A0 format:
```yaml
---
name: clawpowers-<module>
description: <when to trigger>
version: 1.0.0
author: AZPowers-Skills v2.2.6 adapter
requires:
  tools: [node]
---
```

**Skills to create:**
1. `azpowers-memory` — Working/Episodic/Procedural memory ops, checkpoints, context injection
2. `azpowers-payments` — x402 detection, spending policy, payment execution
3. `azpowers-wallet` — Wallet generation, import, signing, EVM address derivation
4. `azpowers-rsi` — Metrics collection, hypothesis testing, mutation engine, A/B tests
5. `azpowers-swarm` — Task classification, concurrency management, token pool management
6. `azpowers-itp` — Message encoding/decoding via ITP service
7. `azpowers-native` — Crypto primitives (sha256, keccak256, ECDSA) with tier status

### Phase 3: A0 Plugin 🔧
**Priority:** Medium  
**Deliverable:** `a0-plugin/azpowers_skills.yaml`

YAML plugin that:
- Injects ClawPowers capability summary into agent system prompt
- Declares available skills and their trigger phrases
- Registers ITP service startup in session hooks

### Phase 4: Scripts & Documentation 🔧
**Priority:** Medium  
**Deliverables:** install.sh, verify.sh, smoke-test.mjs, README.md

- `scripts/install.sh` — Full setup: build CPS, create ~/.clawpowers/ runtime dir
- `scripts/verify.sh` — Tier detection, WASM check, ITP health check, skill load test
- `scripts/smoke-test.mjs` — Node.js test all CPS exports: memory, payments, wallet, rsi, swarm, itp, native
- `README.md` — User-facing: what CPS is, A0 integration, quick start, skill reference

## Key Design Decisions

1. **No CPS source modification** — All adaptation is external wrapper code
2. **WASM tier as primary** — No Rust toolchain required, WASM pre-built works on Node v22
3. **ITP service is optional** — Skills work without ITP (graceful degradation per CPS design)
4. **~/.clawpowers/ runtime** — CPS will use its default home dir for persistent state
5. **Skills use absolute paths** — Import CPS from absolute path to built dist/
6. **Local install** — CPS linked locally, not published to npm

## Acceptance Criteria

- [x] `scripts/install.sh` runs without errors
- [x] `scripts/verify.sh` shows WASM tier active
- [x] `scripts/smoke-test.mjs` passes all 7 module tests
- [x] ITP service starts and `/health` returns `{"status": "ok"}`
- [x] All 7 skills loadable via `skills_tool:load clawpowers-<module>`
- [x] Memory skill: creates WorkingMemoryManager, stores/retrieves entry
- [x] Wallet skill: generates Ethereum address
- [x] Payments skill: detects x402 response
- [x] RSI skill: creates MetricsCollector, records outcome
- [x] Swarm skill: classifies task complexity
- [x] ITP skill: encodes/decodes message via service
- [x] Native skill: reports active tier (expect WASM)
- [x] README.md complete with quick start guide
