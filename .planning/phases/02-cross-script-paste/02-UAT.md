---
status: complete
phase: 02-cross-script-paste
source: [02-01-SUMMARY.md]
started: 2026-03-04T00:00:00Z
updated: 2026-03-04T00:02:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Unit tests pass
expected: Running `python3 -m pytest tests/test_cross_script_paste.py -v` shows all 11 tests passing with no failures or errors.
result: pass
note: automated — 11/11 passed in 0.05s

### 2. Cross-script NoOp anchor reconnect
expected: When you paste a node from Script A that was linked to a NoOp anchor named "ShotA" into Script B, and Script B already has a NoOp anchor named "ShotA", the pasted node's link reconnects to that anchor automatically. The node is no longer disconnected after paste.
result: issue
reported: "It does not reconnect."
severity: major

### 3. Cross-script Dot handling
expected: Anchor Dots (Dots used as link sources pointing to Anchor nodes) should reconnect cross-script by name. Regular Dots with hidden inputs (non-anchor) should NOT reconnect — they should be left disconnected.
result: issue
reported: "Test description was wrong — Anchor Dots should reconnect. Non-link hidden-input Dots should not. Bug: Make Blur1, make a Dot, connect Dot input to Blur1, hide the Dot input, copy the Dot, open new script, make Blur1, paste the Dot — it erroneously connects to Blur1."
severity: major

## Summary

total: 3
passed: 1
issues: 2
pending: 0
skipped: 0

## Gaps

- truth: "Pasting a node cross-script whose link source is a NoOp anchor reconnects to a same-named anchor in the destination script"
  status: failed
  reason: "User reported: It does not reconnect."
  severity: major
  test: 2
  deferred_to: "Phase 05 — refactor cross-script paste logic for hidden-input Dot vs Anchor Dot distinction"

- truth: "Non-anchor Dots with hidden inputs pasted cross-script are left disconnected; only Anchor Dots reconnect by name"
  status: failed
  reason: "User reported: Make Blur1, make a Dot, connect Dot input to Blur1, hide the Dot input, copy the Dot, open new script, make Blur1, paste the Dot — it erroneously connects to Blur1."
  severity: major
  test: 3
  deferred_to: "Phase 05 — refactor cross-script paste logic for hidden-input Dot vs Anchor Dot distinction"
