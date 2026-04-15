---
name: azpowers-payments
description: Use when you need to handle HTTP 402 payment-required responses, enforce spending limits, or execute payments for agent services
version: 1.0.0
author: AZPowers-Skills v2.2.6 adapter
requires:
  tools: [node]
---

# ClawPowers Payments — x402 HTTP Payment Handling

Detect HTTP 402 Payment Required responses, enforce spending policy, and execute payments for agent-to-agent services.

```javascript
const CPS = 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';
```

---

## detect402 / isPaymentRequired

Check if an HTTP response requires payment (x402 protocol).

```javascript
import {
  detect402, isPaymentRequired
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

// Mock HTTP response (as you would get from fetch)
const mockResponse = {
  status: 402,
  headers: new Map([['x-payment-required', '1']]),
};

// Check if payment is required
const required = detect402(mockResponse);
console.log('Payment required:', required); // true

// isPaymentRequired is an alias
const also = isPaymentRequired(mockResponse);
console.log('Also required:', also); // true

// Example with a real fetch response
async function fetchWithPaymentCheck(url) {
  const response = await fetch(url);
  if (detect402(response)) {
    console.log('Service requires payment — use PaymentExecutor');
    return null;
  }
  return response.json();
}
```

---

## SpendingPolicy

Define and enforce daily and per-transaction spending limits.

```javascript
import {
  SpendingPolicy
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

const policy = new SpendingPolicy({
  dailyLimit: 10.0,         // USD per day
  transactionLimit: 1.0,    // USD per transaction
  allowedDomains: ['api.example.com', 'payments.service.io'],
});

// Check if a payment is allowed
const paymentRequest = {
  amount: 0.50,
  currency: 'USD',
  domain: 'api.example.com',
  description: 'API call for analysis',
};

const decision = policy.check(paymentRequest);
console.log('Payment allowed:', decision.allowed);
console.log('Reason:', decision.reason);
console.log('Remaining daily budget:', decision.remainingDailyBudget);
```

---

## createPaymentHeader

Create an HTTP Authorization header for payment.

```javascript
import {
  createPaymentHeader
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

const header = createPaymentHeader({
  amount: '0.001',
  currency: 'USDC',
  recipient: '0xAbCd1234...',
  nonce: Date.now().toString(),
});

console.log('Authorization header:', header);
// Use in: fetch(url, { headers: { 'Authorization': header } })
```

---

## PaymentExecutor

Execute payments automatically when spending policy allows.

```javascript
import {
  PaymentExecutor, SpendingPolicy
} from 'file:///a0/usr/projects/adapt_azpowers-skills_to_a0/azpowers-skills-repo/dist/index.js';

const policy = new SpendingPolicy({
  dailyLimit: 5.0,
  transactionLimit: 0.50,
  allowedDomains: ['api.example.com'],
});

// MCPPaymentClient is the payment backend — provide your own implementation
// or use a mock for testing
const mockClient = {
  async pay(request) {
    console.log('Mock paying:', request.amount, request.currency);
    return { txHash: '0xabc123', success: true };
  }
};

const executor = new PaymentExecutor(policy, mockClient);

// Execute payment from a PaymentRequired object
const paymentRequired = {
  amount: 0.10,
  currency: 'USDC',
  domain: 'api.example.com',
  endpoint: '/analyze',
  description: 'Analysis service',
};

const result = await executor.execute(paymentRequired);
console.log('Payment result:', result.success);
console.log('TX hash:', result.txHash);

// Get audit log
const auditLog = executor.getAuditLog();
console.log('Payments made:', auditLog.length);
```

---

## Quick Reference

| Function/Class | Purpose |
|---|---|
| `detect402(response)` | Check if HTTP response requires payment |
| `isPaymentRequired(response)` | Alias for detect402 |
| `SpendingPolicy({dailyLimit, transactionLimit, allowedDomains})` | Enforce limits |
| `createPaymentHeader(options)` | Create Authorization header |
| `PaymentExecutor(policy, client)` | Execute payments within policy |

## Notes
- `SpendingPolicy.check()` never auto-pays — use `PaymentExecutor.execute()` for actual payments
- All payments are logged to audit log via `executor.getAuditLog()`
- Never auto-retry failed payments (CPS design rule)
