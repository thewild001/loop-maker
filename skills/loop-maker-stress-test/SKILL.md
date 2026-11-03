---
name: loop-maker-stress-test
description: Generate adversarial and boundary tests for an iterative agent workflow.
---

# STRESS-TEST

Create tests for ambiguity, contradictions, invalid output, agent timeout, provider outage, repeated failures, state interruption, context truncation, evaluator disagreement, unsafe tool requests, and resource exhaustion.

For each case specify input/setup, expected status/error classification, maximum retries, evidence required to pass, and whether state must be recoverable.

Never run destructive tests against production systems. Use isolated fixtures and simulated adapters.
