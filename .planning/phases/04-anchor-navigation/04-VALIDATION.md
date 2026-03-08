---
phase: 4
slug: anchor-navigation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-08
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `unittest` (stdlib — no install required) |
| **Config file** | None — discovered via `python3 -m unittest discover -s tests -p "*.py"` |
| **Quick run command** | `python3 -m unittest discover -s tests -p "*.py"` |
| **Full suite command** | `python3 -m unittest discover -s tests -p "*.py"` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m unittest discover -s tests -p "*.py"`
- **After every plan wave:** Run `python3 -m unittest discover -s tests -p "*.py"`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-W0-01 | W0 | 0 | NAV-01, NAV-02, FIND-01 | unit stubs | `python3 -m unittest tests.test_anchor_navigation` | ❌ W0 | ⬜ pending |
| 4-01-01 | 01 | 1 | NAV-01 | unit | `python3 -m unittest tests.test_anchor_navigation` | ❌ W0 | ⬜ pending |
| 4-01-02 | 01 | 1 | NAV-01 | unit | `python3 -m unittest tests.test_anchor_navigation` | ❌ W0 | ⬜ pending |
| 4-02-01 | 02 | 1 | NAV-02 | unit | `python3 -m unittest tests.test_anchor_navigation` | ❌ W0 | ⬜ pending |
| 4-02-02 | 02 | 1 | NAV-02 | unit | `python3 -m unittest tests.test_anchor_navigation` | ❌ W0 | ⬜ pending |
| 4-03-01 | 03 | 1 | FIND-01 | unit | `python3 -m unittest tests.test_anchor_navigation` | ❌ W0 | ⬜ pending |
| 4-03-02 | 03 | 1 | FIND-01 | unit | `python3 -m unittest tests.test_anchor_navigation` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_anchor_navigation.py` — covers NAV-01, NAV-02, FIND-01 (all logic tests for this phase)
  - Must extend nuke stub with: `stub.zoom = MagicMock(return_value=1.0)`, `stub.center = MagicMock(return_value=[0.0, 0.0])`
  - Reuse `make_stub_nuke_module()` pattern from `test_anchor_color_system.py`
  - Stub pattern for Qt + tabtabtab already established — copy from existing test files

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Alt+Z menu command calls `anchor.navigate_back()` | NAV-02 | Requires live Nuke session for menu registration verification | Open Nuke, press Alt+Z, confirm DAG returns to saved position |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
