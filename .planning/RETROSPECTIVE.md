# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-10
**Phases:** 5 | **Plans:** 13

### What Was Built
- Stream-type detection via canSetInput probe — arbitrary node classes classified correctly; Camera/3D → NoOp, 2D → PostageStamp
- Cross-script paste reconnection — Link nodes reconnect by anchor name in destination scripts; Local Dots leave disconnected cleanly
- Anchor color system — ColorPaletteDialog (PySide2/6) wired into creation and rename dialogs, anchor node knob button, and propagation to all linked nodes
- DAG navigation history — single-slot back (Alt+Z) restoring exact zoom+center; BackdropNodes included in Alt+A picker
- DOT_TYPE knob distinction — formal stamp at copy time eliminates cross-script false positives between Link Dots and Local Dots

### What Worked
- **TDD-first approach** worked extremely well: 74+ offline unit tests caught all integration bugs before they reached the Nuke session. Plans with RED/GREEN cycles had zero regressions from prior phases.
- **canSetInput probe pattern** was more reliable than channel-prefix heuristic. Writing a probe against Nuke's own API eliminated the brittleness of string-matching channel names.
- **Phase SUMMARY.md structure** with dependency graph, key decisions, and patterns-established made Phase 5 bug-tracing fast — DOT_TYPE bugs were found in 01-02-SUMMARY decisions within 30 seconds.
- **Yolo mode** allowed rapid plan execution with human checkpoints only where UAT required a Nuke session. Plans averaged 3–5 min each.
- **Offline nuke stub pattern** (StubNode/StubKnob with configurable dict) enabled full paste logic testing without Nuke. Established early in Phase 1, reused through Phase 5 with incremental extensions.

### What Was Inefficient
- **Phase 3 ROADMAP.md checkbox stayed unchecked** — the progress table showed "Not started" for Phase 3 even after it completed. Minor but added a gap-closure doc plan (04-03) that could have been avoided with a doc discipline habit.
- **Qt stub ordering conflict in test discovery** — when running the full suite with `python3 -m unittest discover`, cross-test Qt stub interference caused 4–8 errors. Individual files pass. Fix deferred, but cost time in Phase 3 and 4 diagnoses. Should be fixed once rather than documented as "known" each time.
- **Phase 5 was Phase 2 rework** — Phase 5 fixed two bugs confirmed in Phase 2 UAT that weren't caught by Phase 2's offline tests. Adding a "same-stem false positive" test scenario in Phase 2 would have caught this earlier and eliminated Phase 5.

### Patterns Established
- **Offline nuke stub**: `make_stub_nuke_module()` with StubNode/StubKnob + Qt/tabtabtab module stubs before local imports. Extend per-plan with domain methods (zoom, center, setName, etc.).
- **allNodes side_effect dispatch**: `def _side(class_name=None): return backdrops if class_name == 'BackdropNode' else anchors` — discriminates multi-class queries in a single mock.
- **Detect-once-at-creation pattern**: expensive detection results cached on hidden knob at creation; cheap knob reads at paste time.
- **saved_xxx pattern**: read knob value before a stripping call, re-stamp after. Used for DOT_TYPE preservation across setup_link_node().
- **Backward compat inference fallback**: nodes lacking a typed knob infer type from FQNN structure (anchor-prefix → link type; plain → local type).
- **FQNN stem comparison for cross-script gate**: comparing stored FQNN stem against current script name rather than trusting find_anchor_node() return value, prevents same-stem false positives.

### Key Lessons
1. **Phase 5 could have been avoided**: when UAT found cross-script Dot bugs, they were architectural — Local vs Link Dot — not implementation bugs. Including a "same-stem cross-script paste" test in Phase 2 would have caught this at the plan level.
2. **Test discovery ordering is a real problem**: Qt stub ordering conflicts in flat discovery are not "acceptable known issues" — they obscure real failures. Fix with a conftest.py or test infrastructure plan before v1.1.
3. **Planning document discipline**: update ROADMAP.md checkboxes and progress table immediately when a phase completes, not retroactively. A 5-second update prevents a correction plan.
4. **Yolo mode + TDD is fast**: the combination of automated plan execution and RED/GREEN TDD cycles produced reliable, well-tested code with minimal rework.

### Cost Observations
- Model: claude-sonnet-4-6 (100%)
- Sessions: multiple (separated by phase)
- Notable: Plans with TDD RED/GREEN cycles averaged 3–5 min. Plans without tests (doc-only) averaged 1 min. canSetInput probe (01-03) took 4 min and replaced a fragile heuristic permanently.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 5 | 13 | Initial milestone — established TDD stub pattern, yolo mode, DOT_TYPE architecture |

### Cumulative Quality

| Milestone | Tests | Zero-Dep Additions |
|-----------|-------|--------------------|
| v1.0 | 74+ | 0 (no new external deps) |

### Top Lessons (Verified Across Milestones)

1. TDD offline stubs pay for themselves — caught architectural issues before Nuke sessions
2. Test discovery ordering conflicts should be fixed structurally, not documented as known issues
