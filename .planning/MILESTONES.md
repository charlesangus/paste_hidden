# Milestones

## v1.0 MVP (Shipped: 2026-03-10)

**Phases completed:** 5 phases, 13 plans

**Timeline:** 2026-03-03 → 2026-03-10 (7 days)
**LOC:** ~5,500 Python
**Git range:** `d13aebf feat(01-01)` → `588dc04 feat(04-02)`

**Key accomplishments:**
- canSetInput stream-type probe — Camera anchors produce NoOp links; Read produces PostageStamp (LINK-03 fix)
- Cross-script paste reconnection — Link nodes reconnect by anchor name in destination scripts (XSCRIPT-01)
- Anchor color system — ColorPaletteDialog wired into creation/rename dialogs and anchor node; propagates to all linked nodes (COLOR-01–05)
- DAG navigation history — Alt+A saves position, Alt+Z jumps back; labelled BackdropNodes in picker (NAV-01, NAV-02, FIND-01)
- DOT_TYPE knob distinction — formal Link Dot / Local Dot separation eliminates cross-script false positives (XSCRIPT-01/02 robustness)
- TDD infrastructure — 74+ offline unit tests covering all paste, anchor, color, and navigation logic

**Requirements:** 17/18 v1 requirements shipped; NAV-03 (full forward/back history stack) deferred to v2 as planned stretch goal

**Archive:** `.planning/milestones/v1.0-ROADMAP.md`, `.planning/milestones/v1.0-REQUIREMENTS.md`

---

