---
phase: 10
slug: code-quality-sweep
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` (Wave 0 configures ruff; pytest config already present) |
| **Quick run command** | `pytest tests/ -q` |
| **Full suite command** | `pytest tests/` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -q`
- **After every plan wave:** Run `pytest tests/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 0 | QUAL-01 | lint | `/home/latuser/.local/share/nvim/mason/bin/ruff check --select E,F,W,B,C90,I,SIM .` | ✅ | ⬜ pending |
| 10-01-02 | 01 | 1 | QUAL-01 | lint+unit | `ruff check . && pytest tests/ -q` | ✅ | ⬜ pending |
| 10-01-03 | 01 | 1 | QUAL-01 | lint+unit | `ruff check . && pytest tests/ -q` | ✅ | ⬜ pending |
| 10-01-04 | 01 | 1 | QUAL-01 | lint+unit | `ruff check . && pytest tests/ -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pyproject.toml` — add `[tool.ruff]` with `line-length = 100`, `select = ["E","F","W","B","C90","I","SIM"]`, and `per-file-ignores` for `tabtabtab.py`

*Wave 0 is a config-only task; no test stubs needed — existing pytest infrastructure covers all behavioral verification.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Nuke runtime menu callbacks still fire | QUAL-01 | Requires live Nuke process; cannot be automated in CI | Load plugin in Nuke, open right-click menu, verify paste/copy actions appear and execute |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
