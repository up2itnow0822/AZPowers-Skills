#!/usr/bin/env node
/**
 * AZPowers-Skills × Agent Zero — Smoke Test
 * Tests all 7 CPS modules. Exit 0 = all pass. Exit 1 = any fail.
 */

import os from 'os';
import path from 'path';
import { existsSync } from 'fs';

// Resolve CPS module: prefer npm-installed at ~/.clawpowers/runtime, fall back to local dev dist
const HOME = path.join(os.homedir(), '.clawpowers');
const NPM_CPS   = path.join(HOME, 'runtime', 'node_modules', 'clawpowers', 'dist', 'index.js');
const LOCAL_CPS = new URL('../clawpowers-skills-repo/dist/index.js', import.meta.url).pathname;
const CPS_PATH  = existsSync(NPM_CPS) ? NPM_CPS : existsSync(LOCAL_CPS) ? LOCAL_CPS : null;
if (!CPS_PATH) {
  console.error('ERROR: clawpowers dist not found. Run scripts/install.sh first (npm install clawpowers@2.2.6).');
  process.exit(1);
}
const CPS = `file://${CPS_PATH}`;
console.log(`CPS source: ${CPS_PATH}`);


let allPass = true;
const results = [];

function pass(module, detail) {
  results.push({ module, status: 'PASS', detail });
  console.log(`  PASS: ${module} — ${detail}`);
}

function fail(module, detail, err) {
  results.push({ module, status: 'FAIL', detail, err: String(err) });
  console.log(`  FAIL: ${module} — ${detail}`);
  if (err) console.log(`       ${err}`);
  allPass = false;
}

console.log('=== AZPowers-Skills Smoke Test ===\n');

// ─── 1. Memory ────────────────────────────────────────────────────────────────
console.log('[1/7] Memory');
try {
  const { WorkingMemoryManager } = await import(CPS);
  const mgr = new WorkingMemoryManager();
  const goal = {
    taskId: 'smoke-test-001',
    description: 'Smoke test memory',
    constraints: [],
    successCriteria: ['entry stored'],
    createdAt: new Date().toISOString(),
    source: 'cli',
  };
  const mem = mgr.create('smoke-test-001', goal);
  if (mem.taskId !== 'smoke-test-001') throw new Error('taskId mismatch');
  mgr.addIntermediateOutput('step-1', 'smoke output');
  const snapshot = mgr.getSnapshot();
  if (!snapshot.intermediateOutputs['step-1']) throw new Error('output not found in snapshot');
  pass('Memory', `WorkingMemoryManager created taskId=${mem.taskId}, output stored`);
} catch (e) {
  fail('Memory', 'WorkingMemoryManager create/store/retrieve', e);
}

// ─── 2. Wallet ───────────────────────────────────────────────────────────────
console.log('[2/7] Wallet');
try {
  const { generateWallet } = await import(CPS);
  const wallet = await generateWallet({
    chain: 'base',
    dataDir: path.join(HOME, 'wallet'),
  });
  const validAddress = /^0x[0-9a-fA-F]{40}$/.test(wallet.address);
  if (!validAddress) throw new Error(`Invalid address format: ${wallet.address}`);
  pass('Wallet', `generateWallet OK, address=${wallet.address}`);
} catch (e) {
  fail('Wallet', 'generateWallet address format check', e);
}

// ─── 3. Payments ─────────────────────────────────────────────────────────────
console.log('[3/7] Payments');
try {
  const { detect402 } = await import(CPS);
  // Mock 402 response with all required headers
  const mock402 = {
    status: 402,
    headers: {
      'x-payment-amount': '0.001',
      'x-payment-currency': 'USDC',
      'x-payment-recipient': '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266',
      'x-payment-network': 'base',
    },
  };
  const result = detect402(mock402);
  if (result === null) throw new Error('detect402 returned null for valid 402 response');
  // Verify 200 response is NOT 402
  const mock200 = { status: 200, headers: {} };
  const notRequired = detect402(mock200);
  if (notRequired !== null) throw new Error('detect402 returned non-null for 200 response');
  pass('Payments', `detect402 correctly identified 402 (amount=${result.amount ?? result['amount']})`);
} catch (e) {
  fail('Payments', 'detect402 on mock 402 response', e);
}

// ─── 4. RSI ──────────────────────────────────────────────────────────────────
console.log('[4/7] RSI');
try {
  const { MetricsCollector } = await import(CPS);
  const metricsDir = path.join(HOME, 'metrics');
  const metrics = new MetricsCollector(
    path.join(metricsDir, 'smoke-tasks.json'),
    path.join(metricsDir, 'smoke-skills.json')
  );
  // Record a task metric
  await metrics.recordTaskMetrics({
    taskId: 'smoke-task-001',
    timestamp: new Date().toISOString(),
    durationMs: 1200,
    stepCount: 3,
    stepsCompleted: 3,
    stepsFailed: 0,
    retryCount: 0,
    skillsUsed: ['azpowers-native'],
    outcome: 'success',
    memoryEntriesCreated: 1,
  });
  // Record a skill metric
  await metrics.recordSkillMetrics({
    skillName: 'azpowers-native',
    timestamp: new Date().toISOString(),
    invoked: true,
    succeeded: true,
    durationMs: 400,
    taskId: 'smoke-task-001',
    mutationActive: false,
  });
  const history = await metrics.getTaskHistory(1);
  if (!history || history.length === 0) throw new Error('No task history returned');
  pass('RSI', `MetricsCollector.recordTaskMetrics OK, history length=${history.length}`);
} catch (e) {
  fail('RSI', 'MetricsCollector recordTaskMetrics/getTaskHistory', e);
}

// ─── 5. Swarm ─────────────────────────────────────────────────────────────────
console.log('[5/7] Swarm');
try {
  const { classifyHeuristic, selectModel } = await import(CPS);
  const simple = classifyHeuristic('List files');
  const complex = classifyHeuristic('Redesign the entire authentication and authorization system with multi-tenant support, OAuth2, and audit logging');
  if (simple !== 'simple' && simple !== 'medium') throw new Error(`Unexpected simple classification: ${simple}`);
  if (complex !== 'complex' && complex !== 'medium') throw new Error(`Unexpected complex classification: ${complex}`);
  const model = selectModel('complex');
  if (!model || typeof model !== 'string') throw new Error('selectModel returned no model');
  pass('Swarm', `classifyHeuristic: simple→${simple}, complex→${complex}, model=${model}`);
} catch (e) {
  fail('Swarm', 'classifyHeuristic + selectModel', e);
}

// ─── 6. Native ────────────────────────────────────────────────────────────────
console.log('[6/7] Native');
try {
  const { getActiveTier, computeSha256, isWasmAvailable } = await import(CPS);
  const tier = await getActiveTier();
  if (!['native', 'wasm', 'ts'].includes(tier)) throw new Error(`Unknown tier: ${tier}`);
  const wasmOk = await isWasmAvailable();
  const hash = await computeSha256('clawpowers-smoke-test');
  if (!/^[0-9a-f]{64}$/i.test(hash)) throw new Error(`Invalid SHA-256 hash: ${hash}`);
  pass('Native', `getActiveTier=${tier}, wasm=${wasmOk}, sha256=${hash.slice(0, 16)}...`);
} catch (e) {
  fail('Native', 'getActiveTier + computeSha256', e);
}

// ─── 7. ITP ──────────────────────────────────────────────────────────────────
console.log('[7/7] ITP');
try {
  const { itpEncode, itpHealthCheck } = await import(CPS);
  // itpHealthCheck — optional, service may not be running
  const isUp = await itpHealthCheck();
  console.log(`        ITP service available: ${isUp}`);
  // itpEncode — must not throw even if service is down
  const result = await itpEncode(
    'Please analyze and synthesize the performance report for the trading system agent',
    'smoke-test-agent'
  );
  if (!result || typeof result.encoded !== 'string') {
    throw new Error('itpEncode returned invalid result');
  }
  const detail = isUp
    ? `encoded=${result.encoded.slice(0, 40)}, compressed=${result.wasCompressed}`
    : `ITP service down — graceful fallback OK, passthrough=${result.encoded.slice(0, 30)}`;
  pass('ITP', detail);
} catch (e) {
  fail('ITP', 'itpEncode graceful fallback', e);
}

// ─── Summary ─────────────────────────────────────────────────────────────────
console.log('\n=== Results ===');
results.forEach(r => {
  const icon = r.status === 'PASS' ? '✓' : '✗';
  console.log(`  ${icon} ${r.module.padEnd(10)} ${r.status}`);
});

const passed = results.filter(r => r.status === 'PASS').length;
const failed = results.filter(r => r.status === 'FAIL').length;
console.log(`\n${passed}/${results.length} modules passed`);

if (!allPass) {
  console.log('\nFailed modules:');
  results.filter(r => r.status === 'FAIL').forEach(r => {
    console.log(`  FAIL ${r.module}: ${r.detail}`);
    if (r.err) console.log(`       Error: ${r.err}`);
  });
  process.exit(1);
} else {
  console.log('\nAll modules passed! ✓');
  process.exit(0);
}
