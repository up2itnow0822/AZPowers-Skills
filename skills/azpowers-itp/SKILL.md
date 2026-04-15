---
name: azpowers-itp
description: Use when sending messages between agents to save tokens — encode agent messages with ITP compression, decode received ITP messages
version: 1.0.0
author: AZPowers-Skills v2.2.6 adapter
requires:
  tools: [node]
---

# ClawPowers ITP — Agent Message Compression

The Identical Twins Protocol (ITP) compresses agent-to-agent messages using a codebook of operation shorthand, saving tokens on every inter-agent call.

**ITP Service:** FastAPI on port 8100. Skills work without it (graceful degradation).

```javascript
const A0PS = 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
```

---

## Check ITP Server Health

Always check if ITP service is running before encoding. If not running, start it.

```bash
# Check health
curl -s http://localhost:8100/health
# Expected: {"status":"ok","version":"1.0.0","codebook_entries":32,...}

# Start ITP service if not running
cd /a0/usr/projects/adapt_azpowers-skills_to_a0/itp-service && bash start.sh
```

---

## itpEncode

Encode an agent message with ITP compression. Gracefully returns original message if server is down.

```javascript
import {
  itpEncode
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

// Encode a message (calls ITP service at localhost:8100)
// If service is down, returns original message unchanged (graceful degradation)
const result = await itpEncode(
  'Please analyze and synthesize the performance report for the trading system',
  'agent-director'  // optional: source agent name
);

if (result.wasCompressed) {
  console.log('Encoded:', result.encoded);
  // e.g. "ITP:ANL+SYN+PERF+RPT+TRD"
  console.log('Savings:', result.savingsPct + '%');
  console.log('Original tokens:', result.originalTokens);
  console.log('Compressed tokens:', result.compressedTokens);
} else {
  console.log('Not compressed (message below threshold or service down)');
  console.log('Message:', result.encoded); // original returned as-is
}
```

---

## itpDecode

Decode an ITP-compressed message received from another agent.

```javascript
import {
  itpDecode
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

// Decode a message — if not ITP format, returns original unchanged
const result = await itpDecode('ITP:ANL+SYN+PERF+RPT');

console.log('Was ITP:', result.wasItp);   // true
console.log('Decoded:', result.decoded);  // 'analyze synthesize performance report'
console.log('Original:', result.original);

// Non-ITP messages pass through safely
const plain = await itpDecode('Hello, just a normal message');
console.log('Was ITP:', plain.wasItp);   // false
console.log('Decoded:', plain.decoded);  // 'Hello, just a normal message'
```

---

## itpHealthCheck

Check if ITP service is available.

```javascript
import {
  itpHealthCheck
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

const isUp = await itpHealthCheck();
console.log('ITP service available:', isUp); // true | false

// Conditional encoding pattern
async function sendMessage(message, targetAgent) {
  const healthy = await itpHealthCheck();
  if (healthy) {
    const encoded = await itpEncode(message, 'my-agent');
    return encoded.encoded; // compressed or original
  }
  return message; // passthrough when service down
}
```

---

## encodeTaskDescription

Encode a swarm task description for inter-agent transmission.

```javascript
import {
  encodeTaskDescription
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

const task = {
  taskId: 'swarm-task-001',
  description: 'Analyze and optimize the trading system performance metrics',
  complexity: 'complex',
};

// Encode the task description for transmission to worker agent
const encoded = await encodeTaskDescription(task);
console.log('Encoded task description:', encoded);
// Returns compressed description if ITP service available, otherwise original
```

---

## decodeSwarmResult

Decode a swarm result received from a worker agent.

```javascript
import {
  decodeSwarmResult
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

// Decode a result that may have been ITP-encoded by the worker
const rawResult = 'ITP:ANL+STS/OK+DAT/JSON'; // received from worker
const decoded = await decodeSwarmResult(rawResult);
console.log('Decoded result:', decoded);
// 'analyze success json data'
```

---

## ITP Codebook Reference

Messages matching these phrases are compressed to their codes:

| Code | Phrase | Code | Phrase |
|---|---|---|---|
| `ANL` | analyze | `SYN` | synthesize |
| `OPT` | optimize | `DBG` | debug |
| `RPT` | report | `PLN` | plan |
| `EXE` | execute | `REV` | review |
| `TST` | test | `DOC` | document |
| `SRH` | search | `VAL` | validate |
| `GEN` | generate | `TRN` | transform |
| `AGG` | aggregate | `SVC` | service |
| `DIR` | director | `WKR` | worker |
| `MON` | monitor | `AGT` | agent |
| `ORC` | orchestrator | `STS/OK` | success |
| `STS/ERR` | error | `STS/UPD` | update |
| `STS/PEND` | pending | `STS/ACK` | acknowledged |
| `DAT/JSON` | json data | `DAT/TXT` | text data |
| `TRD` | trading | `PERF` | performance |
| `SYS` | system | `MEM` | memory |
| `PAY` | payment | `WLT` | wallet |
| `RSI` | self-improvement | | |

Encoded format: `ITP:<code1>+<code2>+...`

Compression activates only when savings exceed 10%.

---

## Start ITP Service (Reference)

```bash
# Start (idempotent — safe to call if already running)
bash /a0/usr/projects/adapt_azpowers-skills_to_a0/itp-service/start.sh

# Check stats
curl -s http://localhost:8100/tools/stats | python -m json.tool

# View codebook
curl -s http://localhost:8100/tools/codebook | python -m json.tool

# View recent history
curl -s 'http://localhost:8100/tools/history?limit=5' | python -m json.tool
```

---

## Quick Reference

| Function | Signature | Purpose |
|---|---|---|
| `itpEncode(message, sourceAgent?)` | `(string, string?) -> EncodeResult` | Compress message |
| `itpDecode(message)` | `(string) -> DecodeResult` | Decompress message |
| `itpHealthCheck()` | `() -> boolean` | Check service availability |
| `encodeTaskDescription(task)` | `(SwarmTask) -> string` | Encode swarm task |
| `decodeSwarmResult(result)` | `(string) -> string` | Decode swarm result |

## Notes
- All ITP functions degrade gracefully when server is down — they never throw
- ITP service PID stored in `/tmp/itp-service.pid`, logs in `/tmp/itp-service.log`
- Combines well with `azpowers-swarm` for token-efficient parallel agent workloads
- Only compresses when savings > 10% (avoids compressing already-short messages)
