---
name: azpowers-memory
description: Use when you need persistent memory across sessions — store/retrieve working memory entries, episodic events, procedural knowledge, or manage checkpoints
version: 1.0.0
author: AZPowers-Skills v2.2.6 adapter
requires:
  tools: [node]
---

# ClawPowers Memory — 3-Tier Persistent Memory System

Provides Working Memory, Episodic Memory, Procedural Memory, Checkpoints, and Context Injection via A0P-S v2.2.6.

Runtime home: `~/.clawpowers/` (auto-created by A0P-S)

```javascript
const A0PS = 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
```

---

## WorkingMemoryManager

In-process working memory for the current task (no file I/O).

```javascript
// Run with: node --input-type=module
import {
  WorkingMemoryManager
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

const mgr = new WorkingMemoryManager();

// Create working memory for a task
const goal = {
  taskId: 'task-001',
  description: 'Analyze system performance',
  constraints: [],
  successCriteria: ['Report generated'],
  createdAt: new Date().toISOString(),
  source: 'cli',
};
const mem = mgr.create('task-001', goal);
console.log('Working memory created:', mem.taskId);

// Store intermediate output
// Store intermediate output for a step
mgr.addIntermediateOutput('step-1', 'analysis complete');

// Get snapshot of all working memory
const snapshot = mgr.getSnapshot();
console.log('Outputs:', snapshot.intermediateOutputs);

// Clear memory
mgr.clear();
```

---

## EpisodicMemory

Persists task outcomes with lessons learned to `~/.clawpowers/memory/episodic.json`.

```javascript
import {
  EpisodicMemory
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
import os from 'os';
import path from 'path';

const episodic = new EpisodicMemory(
  path.join(os.homedir(), '.clawpowers', 'memory', 'episodic.json')
);

// Add a completed task event
await episodic.add({
  taskId: 'task-001',
  timestamp: new Date().toISOString(),
  description: 'Analyzed system performance',
  outcome: 'success',
  lessonsLearned: ['Check CPU first', 'Memory spikes at 14:00'],
  skillsUsed: ['azpowers-native', 'azpowers-rsi'],
  durationMs: 4200,
  tags: ['performance', 'analysis'],
});

// Query recent events
const recent = await episodic.readAll();
console.log('Episodic entries:', recent.length);
console.log('Last entry:', recent[recent.length - 1]);
```

---

## ProceduralMemory

Persists reusable procedures (how-to knowledge) to `~/.clawpowers/memory/procedural.json`.

```javascript
import {
  ProceduralMemory
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
import os from 'os';
import path from 'path';

const procedural = new ProceduralMemory(
  path.join(os.homedir(), '.clawpowers', 'memory', 'procedural.json')
);

// Add a procedure
await procedural.add({
  name: 'performance-audit',
  steps: [
    'Run getActiveTier() to check native capabilities',
    'Collect metrics with MetricsCollector',
    'Analyze with HypothesisEngine',
    'Report findings',
  ],
  tags: ['performance', 'audit'],
  successRate: 0.95,
  avgDurationMs: 5000,
  lastUsed: new Date().toISOString(),
});

// Look up procedures by tag
const procs = await procedural.readAll();
const perfProcs = procs.filter(p => p.tags.includes('performance'));
console.log('Performance procedures:', perfProcs.map(p => p.name));
```

---

## CheckpointManager

Save and restore agent state to `~/.clawpowers/state/checkpoints/`.

```javascript
import {
  CheckpointManager
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
import os from 'os';
import path from 'path';

const checkpoints = new CheckpointManager(
  path.join(os.homedir(), '.clawpowers', 'state', 'checkpoints')
);

// Save a checkpoint
const mem = { taskId: 'task-001', contextWindow: ['step 1 done'] };
await checkpoints.save('task-001', mem);
console.log('Checkpoint saved');

// List all checkpoints
const list = await checkpoints.list();
console.log('Available checkpoints:', list);

// Restore latest checkpoint
const restored = await checkpoints.loadLatest('task-001');
console.log('Restored:', restored?.taskId);
```

---

## ContextInjector

Inject relevant episodic + procedural context into a prompt based on current goal.

```javascript
import {
  ContextInjector, EpisodicMemory, ProceduralMemory
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
import os from 'os';
import path from 'path';

const HOME = path.join(os.homedir(), '.clawpowers', 'memory');
const episodic = new EpisodicMemory(path.join(HOME, 'episodic.json'));
const procedural = new ProceduralMemory(path.join(HOME, 'procedural.json'));
const injector = new ContextInjector(episodic, procedural);

const goal = {
  taskId: 'task-002',
  description: 'Optimize wallet generation performance',
  constraints: [],
  successCriteria: ['Latency < 100ms'],
  createdAt: new Date().toISOString(),
  source: 'cli',
};

// Returns array of context strings to prepend to agent prompt
const contextLines = await injector.inject(goal, 2000);
console.log('Context to inject:');
contextLines.forEach(line => console.log(' -', line));
```

---

## Quick Reference

| Class | File Path | Purpose |
|---|---|---|
| `WorkingMemoryManager` | in-process | Current task scratch space |
| `EpisodicMemory` | `~/.clawpowers/memory/episodic.json` | Task outcome history |
| `ProceduralMemory` | `~/.clawpowers/memory/procedural.json` | How-to procedures |
| `CheckpointManager` | `~/.clawpowers/state/checkpoints/` | Save/restore state |
| `ContextInjector` | uses above | Smart context injection |
