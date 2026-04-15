---
name: azpowers-swarm
description: Use when you need to coordinate parallel agent tasks — classify task complexity, manage concurrency limits, track token budgets across parallel agents
version: 1.0.0
author: AZPowers-Skills v2.2.6 adapter
requires:
  tools: [node]
---

# ClawPowers Swarm — Parallel Task Coordination

Classify task complexity, select models, manage concurrency limits, and track token budgets across parallel agent workloads.

```javascript
const A0PS = 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
```

---

## classifyHeuristic

Classify a single task's complexity without an LLM call (fast, local).

```javascript
import {
  classifyHeuristic
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

// Returns 'simple' | 'medium' | 'complex'
const complexity = classifyHeuristic('List all files in /tmp');
console.log('Complexity:', complexity); // 'simple'

const complexity2 = classifyHeuristic('Analyze and refactor the entire authentication system, generate tests, and update documentation');
console.log('Complexity:', complexity2); // 'complex'

const complexity3 = classifyHeuristic('Write a function that parses JSON and validates the schema');
console.log('Complexity:', complexity3); // 'medium'
```

---

## classifyTasks

Classify an array of tasks in bulk.

```javascript
import {
  classifyTasks
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

const tasks = [
  { taskId: 'task-1', description: 'List files in /tmp' },
  { taskId: 'task-2', description: 'Parse and validate user input JSON' },
  { taskId: 'task-3', description: 'Redesign the database schema with sharding and migration plan' },
];

const classified = classifyTasks(tasks);
console.log('Classified tasks:');
classified.forEach(t => {
  console.log(`  ${t.taskId}: ${t.complexity}`);
});
// task-1: simple
// task-2: medium  
// task-3: complex
```

---

## selectModel

Get the recommended model name for a given complexity level.

```javascript
import {
  selectModel, classifyHeuristic
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

const task = 'Analyze and refactor authentication system';
const complexity = classifyHeuristic(task);
const model = selectModel(complexity);

console.log(`Task complexity: ${complexity}`);
console.log(`Recommended model: ${model}`);
// complex -> 'claude-opus-4-5' or similar large model
// medium  -> 'claude-sonnet-4-5'
// simple  -> 'claude-haiku-3-5'

// Batch: classify and route in one pass
const tasks = [
  'List files',
  'Write unit tests for auth module',
  'Redesign entire microservices architecture',
];

tasks.forEach(t => {
  const c = classifyHeuristic(t);
  console.log(`"${t.slice(0,30)}" -> ${c} -> ${selectModel(c)}`);
});
```

---

## ConcurrencyManager

Manage a semaphore-based concurrency limit for parallel task slots.

```javascript
import {
  ConcurrencyManager
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

// Allow max 3 parallel tasks, backpressure at 80% capacity
const concurrency = new ConcurrencyManager(3, 0.8);

// Run tasks with controlled concurrency
async function runParallelTasks(tasks) {
  const promises = tasks.map(async (task) => {
    // Acquire slot (waits if at max concurrency)
    await concurrency.acquire();
    try {
      console.log(`Running: ${task.description}`);
      // ... do work ...
      await new Promise(r => setTimeout(r, 100)); // simulate work
      return { taskId: task.taskId, status: 'done' };
    } finally {
      // Always release slot
      concurrency.release();
    }
  });
  return Promise.all(promises);
}

const tasks = [
  { taskId: 'task-1', description: 'Task A' },
  { taskId: 'task-2', description: 'Task B' },
  { taskId: 'task-3', description: 'Task C' },
  { taskId: 'task-4', description: 'Task D' },
];

const results = await runParallelTasks(tasks);
console.log('Active slots:', concurrency.activeCount);
console.log('Results:', results.length);
```

---

## TokenPool

Allocate and track token budgets across parallel agents.

```javascript
import {
  TokenPool
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

// Total pool: 100,000 tokens; default per-task: 20,000
const pool = new TokenPool(100_000, 20_000);

// Allocate budget for a task
const task1Allocated = pool.allocate('task-001');        // uses default 20,000
const task2Allocated = pool.allocate('task-002', 5_000); // custom budget
const task3Allocated = pool.allocate('task-003', 50_000);

console.log('Task-1 allocated:', task1Allocated); // true
console.log('Task-3 allocated:', task3Allocated); // true

// Check remaining budget
const report = pool.getUsageReport();
console.log('Total budget:', report.totalBudget);
console.log('Allocated:', report.allocated);
console.log('Remaining:', report.remaining);
console.log('Active tasks:', report.activeTasks);

// Release tokens when task completes
pool.release('task-001');
pool.release('task-002');

const updated = pool.getUsageReport();
console.log('After release — remaining:', updated.remaining);
```

---

## Full Swarm Orchestration Example

```javascript
import {
  classifyTasks, selectModel, ConcurrencyManager, TokenPool
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

const tasks = [
  { taskId: 'a', description: 'List environment variables' },
  { taskId: 'b', description: 'Write and test authentication module' },
  { taskId: 'c', description: 'Redesign payment architecture with sharding' },
];

// 1. Classify all tasks
const classified = classifyTasks(tasks);

// 2. Set up concurrency and token management
const concurrency = new ConcurrencyManager(2); // max 2 parallel
const pool = new TokenPool(60_000, 20_000);

// 3. Run with budget and concurrency control
const results = await Promise.all(classified.map(async (task) => {
  const model = selectModel(task.complexity);
  const tokenBudget = task.complexity === 'complex' ? 30_000 : 15_000;

  if (!pool.allocate(task.taskId, tokenBudget)) {
    return { taskId: task.taskId, error: 'insufficient token budget' };
  }

  await concurrency.acquire();
  try {
    console.log(`[${task.taskId}] ${task.complexity} -> ${model} (${tokenBudget} tokens)`);
    // ... call model here ...
    return { taskId: task.taskId, complexity: task.complexity, model };
  } finally {
    concurrency.release();
    pool.release(task.taskId);
  }
}));

console.log('Swarm results:', results);
```

---

## Quick Reference

| Function/Class | Signature | Purpose |
|---|---|---|
| `classifyHeuristic(task)` | `(string) -> 'simple'\|'medium'\|'complex'` | Single task classification |
| `classifyTasks(tasks)` | `(Task[]) -> ClassifiedTask[]` | Bulk classification |
| `selectModel(complexity)` | `(complexity) -> string` | Model recommendation |
| `ConcurrencyManager` | `(maxConcurrent=5, backpressure=0.8)` | Semaphore-based slots |
| `TokenPool` | `(totalBudget=100000, perTaskDefault=20000)` | Token budget tracking |

## Notes
- `ConcurrencyManager.acquire()` is async — awaits a free slot
- `ConcurrencyManager.release()` is sync — always call in `finally`
- `TokenPool.allocate()` returns `false` if insufficient budget (never throws)
- Combine with `azpowers-itp` to compress inter-agent messages and save tokens
