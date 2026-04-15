---
name: azpowers-rsi
description: Use when you need to track task metrics, run hypothesis-driven self-improvement, manage A/B tests for agent strategies, or audit RSI decisions
version: 1.0.0
author: AZPowers-Skills v2.2.6 adapter
requires:
  tools: [node]
---

# ClawPowers RSI — Recursive Self-Improvement Engine

Track performance metrics, generate improvement hypotheses, run A/B tests, and audit all RSI decisions.

```javascript
const CPS = 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
```

---

## MetricsCollector

Record task and skill performance metrics to JSON files.

**Constructor:** `new MetricsCollector(taskMetricsPath, skillMetricsPath)`

```javascript
import {
  MetricsCollector
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
import os from 'os';
import path from 'path';

const HOME = path.join(os.homedir(), '.clawpowers', 'metrics');
const metrics = new MetricsCollector(
  path.join(HOME, 'tasks.json'),
  path.join(HOME, 'skills.json')
);

// Record a completed task
await metrics.recordTaskMetrics({
  taskId: 'task-001',
  timestamp: new Date().toISOString(),
  durationMs: 4200,
  stepCount: 5,
  stepsCompleted: 5,
  stepsFailed: 0,
  retryCount: 0,
  skillsUsed: ['azpowers-native', 'azpowers-memory'],
  outcome: 'success',          // 'success' | 'failure' | 'partial'
  memoryEntriesCreated: 2,
});

// Record a skill invocation
await metrics.recordSkillMetrics({
  skillName: 'azpowers-native',
  timestamp: new Date().toISOString(),
  invoked: true,
  succeeded: true,
  durationMs: 850,
  taskId: 'task-001',
  mutationActive: false,
});

// Get task history (most recent N)
const history = await metrics.getTaskHistory(10);
console.log('Recent tasks:', history.length);
console.log('Last outcome:', history[history.length - 1]?.outcome);

// Get aggregated stats for a specific skill
const stats = await metrics.getAggregatedSkillStats('azpowers-native');
console.log('Success rate:', stats.successRate);
console.log('Avg duration ms:', stats.avgDurationMs);
console.log('Total invocations:', stats.totalInvocations);
```

---

## HypothesisEngine

Analyze metrics to generate improvement hypotheses. Requires ≥5 data points.

```javascript
import {
  HypothesisEngine, MetricsCollector
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
import os from 'os';
import path from 'path';

const HOME = path.join(os.homedir(), '.clawpowers', 'metrics');
const metrics = new MetricsCollector(
  path.join(HOME, 'tasks.json'),
  path.join(HOME, 'skills.json')
);

const engine = new HypothesisEngine();

// Get data arrays for analysis
const taskHistory = await metrics.getTaskHistory();
const skillStats = await metrics.getAggregatedSkillStats('azpowers-native');

// Wrap single stat in array for analyze()
const hypotheses = engine.analyze([skillStats], taskHistory);
console.log('Hypotheses generated:', hypotheses.length);
// Returns [] if fewer than 5 data points
hypotheses.forEach(h => {
  console.log(`[${h.type}] ${h.description}`);
  console.log(`  Confidence: ${h.confidence}, Expected delta: ${h.expectedDelta}`);
});
```

---

## MutationEngine

Propose, apply, and roll back skill mutations.

```javascript
import {
  MutationEngine
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
import os from 'os';
import path from 'path';

const mutationEngine = new MutationEngine(
  path.join(os.homedir(), '.clawpowers', 'state')
);

// Propose a mutation
const mutation = await mutationEngine.propose({
  skillName: 'azpowers-native',
  type: 'parameter-tune',
  description: 'Increase WASM thread pool size',
  expectedDelta: 0.15,
  confidence: 0.75,
});
console.log('Mutation proposed:', mutation.mutationId);

// Apply the mutation
await mutationEngine.apply(mutation.mutationId);
console.log('Mutation applied');

// Roll back if performance dropped
await mutationEngine.rollback(mutation.mutationId);
console.log('Mutation rolled back');

// List active mutations
const active = await mutationEngine.listActive();
console.log('Active mutations:', active.length);
```

---

## ABTestManager

Run A/B tests between control (baseline) and variant (mutation) strategies.

```javascript
import {
  ABTestManager, MetricsCollector
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
import os from 'os';
import path from 'path';

const HOME = path.join(os.homedir(), '.clawpowers', 'metrics');
const metrics = new MetricsCollector(
  path.join(HOME, 'tasks.json'),
  path.join(HOME, 'skills.json')
);

const abManager = new ABTestManager();

// Get baseline stats for comparison
const baselineStats = await metrics.getAggregatedSkillStats('azpowers-native');

// Define the mutation being tested
const mutation = {
  mutationId: 'mut-001',
  skillName: 'azpowers-native',
  type: 'parameter-tune',
  description: 'WASM pool increase',
  expectedDelta: 0.1,
  appliedAt: new Date().toISOString(),
  status: 'active',
};

// Start test
const test = abManager.startTest(mutation, baselineStats);
console.log('Test started:', test.testId);

// Record variant result
abManager.recordResult(test.testId, {
  taskId: 'task-abtest-001',
  skillName: 'azpowers-native',
  timestamp: new Date().toISOString(),
  invoked: true,
  succeeded: true,
  durationMs: 3500,
  mutationActive: true,
});

// Check result (winner determined after enough samples)
const result = abManager.getResult(test.testId);
console.log('Winner:', result?.winner ?? 'not determined yet');
```

---

## RSIAuditLog

Append-only log of all RSI decisions for transparency and compliance.

```javascript
import {
  RSIAuditLog
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
import os from 'os';
import path from 'path';

const auditLog = new RSIAuditLog(
  path.join(os.homedir(), '.clawpowers', 'logs', 'rsi-audit.json')
);

// Log an RSI decision
await auditLog.log({
  auditId: `audit-${Date.now()}`,
  timestamp: new Date().toISOString(),
  action: 'mutation-applied',
  mutationId: 'mut-001',
  skillName: 'azpowers-native',
  tier: 't2',
  approved: true,
  rationale: 'WASM pool tuning showed +12% on benchmarks',
  performanceDelta: 0.12,
});

// Query recent decisions
const recent = await auditLog.queryRecent(10);
console.log('Recent RSI decisions:');
recent.forEach(entry => {
  console.log(`  [${entry.action}] ${entry.skillName} — approved: ${entry.approved}`);
});
```

---

## Quick Reference

| Class | Key Methods | Purpose |
|---|---|---|
| `MetricsCollector(taskPath, skillPath)` | `recordTaskMetrics()`, `recordSkillMetrics()`, `getTaskHistory(limit?)`, `getAggregatedSkillStats(skillName)` | Track outcomes |
| `HypothesisEngine()` | `analyze(skillStats[], taskHistory[])` | Generate hypotheses (≥5 data points) |
| `MutationEngine(stateDir)` | `propose()`, `apply(id)`, `rollback(id)`, `listActive()` | Propose/apply/rollback mutations |
| `ABTestManager()` | `startTest(mutation, baseline)`, `recordResult(testId, metric)`, `getResult(testId)` | A/B test strategies |
| `RSIAuditLog(filePath)` | `log(entry)`, `queryRecent(limit)` | Append-only audit trail |

## Notes
- `HypothesisEngine.analyze()` requires ≥5 data points (returns `[]` otherwise)
- All mutations are reversible via `MutationEngine.rollback()`
- RSI audit log is append-only for compliance
- `MetricsCollector` constructor takes two file paths: tasks.json and skills.json
- `ABTestManager.recordResult()` takes a `SkillMetrics` object (not `TaskMetrics`)
