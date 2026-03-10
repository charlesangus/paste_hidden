# Project Research Summary

**Project:** paste_hidden v1.1 — preferences panel and color picker redesign
**Domain:** Nuke embedded Python plugin — Qt dialog UI and JSON preferences persistence
**Researched:** 2026-03-10
**Confidence:** HIGH

## Executive Summary

This is a targeted incremental milestone on a shipped Nuke plugin. v1.0 established a validated stack (Python 3, PySide2/PySide6 conditional import guard, JSON file persistence, QDialog-based color picker) and the research confirms: do not re-evaluate any of it. All v1.1 work draws exclusively from the existing stack — `json` stdlib, `os` stdlib, and Qt widgets already imported. No new dependencies are introduced. The approach follows a well-documented sibling plugin pattern (Labelmaker, tabtabtab-nuke) for a `Prefs` singleton backed by `~/.nuke/paste_hidden_prefs.json`.

The recommended approach has two parallel workstreams: (1) create a new `prefs.py` module containing a lazy-loading `Prefs` singleton, a `PrefsDialog` QDialog, and an `open_prefs()` entry point; and (2) redesign `ColorPaletteDialog` in `colors.py` to separate swatch selection from dialog confirmation. These two workstreams have no mutual dependency at the code level and can be built in parallel. The integration points — `anchor.py` passing `custom_colors` into the dialog, and `paste_hidden.py` reading the `link_classes_paste_mode` flag in `copy_hidden()` — are clearly bounded and minimally invasive.

The primary risks are architectural rather than technical: a circular import between `colors.py` and `prefs.py` if naively structured (resolved by dependency injection — `ColorPaletteDialog` receives `custom_colors` as a constructor parameter), a split-brain state if custom colors are left in the old `user_palette.json` alongside new prefs (resolved by absorbing palette into `paste_hidden_prefs.json` with a lazy migration path), and the color picker caller contract being silently broken during the click-to-select redesign (resolved by keeping `exec_()` / `Accepted` as the completion signal for all three existing callers in `anchor.py`, none of which should require any changes).

## Key Findings

### Recommended Stack

The v1.0 stack is entirely unchanged. All new functionality draws from Python stdlib (`json`, `os`) and Qt widgets (`QListWidget`, `QListWidgetItem`, `QPixmap`) that are already in scope via existing imports in `colors.py` and `constants.py`. The PySide2/PySide6 version guard already in place covers all new widget usage — `Qt.DecorationRole` and `QListWidget` work identically in both versions with no enum migration required.

**Core technologies:**
- `json` stdlib: preferences file read/write — already used for `USER_PALETTE_PATH`; no new dependency
- `os.path.expanduser`: `~/.nuke/paste_hidden_prefs.json` path resolution — same pattern as `USER_PALETTE_PATH` in `constants.py`
- `QListWidget` + `QListWidgetItem`: custom color management list in `PrefsDialog` — sufficient for the small dataset (≤20 colors); avoids `QListView` + `QAbstractListModel` boilerplate
- `QPixmap` with `Qt.DecorationRole`: 16×16 color swatches in the list — works identically in PySide2 and PySide6
- `QPushButton.setAutoDefault(False)`: prevents swatch buttons from intercepting Enter key — necessary for the click-to-select redesign

**Critical stack decision:** `QListWidget` over `QListView` + `QAbstractListModel`. The dataset is small, operations are simple, and `QListWidget`'s convenience API avoids ~100 lines of boilerplate with no user-visible benefit at this scale.

### Expected Features

All features below are scoped strictly to v1.1. v1.0 features (swatch grid, color propagation, anchor dialogs) are stable and not re-evaluated.

**Must have (table stakes — v1.1 launch):**
- Preferences dialog accessible from Anchors menu — standard DCC plugin UX; missing = unfinished
- Enable/disable plugin toggle, persisted — without this, disabling requires editing `menu.py` manually
- Paste-mode toggle (link-creation vs plain copy for LINK_SOURCE_CLASSES), persisted — currently hardcoded in `constants.py`
- Preferences JSON load/save module — unblocks all prefs features; foundational
- Custom color list with Add and Remove in preferences panel — backed by existing `load_user_palette()` helpers
- Color picker: click selects swatch without closing dialog — current close-on-click behavior is the reported UX problem
- Color picker: Enter/Return accepts with currently selected color — standard modal dialog keyboard contract
- Color picker: explicit OK button — required once click no longer closes
- Color picker: swatch order reordered (custom first, backdrop, Nuke defaults) — custom colors are most intentional
- Color picker: pre-selected highlight visible after click-to-select flow — already partially implemented; must survive redesign

**Should have (differentiators — v1.1+ if time allows):**
- Custom color list: Edit (replace color value via `nuke.getColor()`) — useful but not blocking
- Custom color list: drag-to-reorder — ergonomic improvement; requires more QListWidget setup

**Defer (v2+):**
- Full forward/back navigation history stack (NAV-03) — already tracked in PROJECT.md as v2 candidate
- Manual `tile_color` change propagation to links (Color-V2-01) — explicitly deferred by design

### Architecture Approach

The v1.1 architecture adds one new module (`prefs.py`) and makes additive or minimal changes to four existing files (`constants.py`, `colors.py`, `paste_hidden.py`, `menu.py`). Three modules remain entirely unchanged (`anchor.py`, `link.py`, `labels.py`). The critical design constraint is avoiding a circular import between `colors.py` and `prefs.py`: `ColorPaletteDialog` must receive `custom_colors` and `on_save_custom_colors` as constructor parameters (dependency injection) rather than importing `prefs` directly. This is the established injection pattern in single-file Nuke plugins.

The prefs file architecture decision is: `paste_hidden_prefs.json` absorbs the existing `paste_hidden_user_palette.json`. Custom colors migrate lazily — read from the old file on first session if the new file is absent, written to the new file on next save. The old file is never written again after migration. This eliminates split-brain state risk permanently.

**Major components:**
1. `prefs.py` (NEW) — `Prefs` data class with lazy-loading `get_prefs()` singleton, `PrefsDialog` QDialog, `open_prefs()` menu entry point, and migration logic from old palette file
2. `ColorPaletteDialog` in `colors.py` (MODIFIED) — redesigned state machine separating `_selected_color` (highlight) from confirmation (Enter / OK / double-click); receives `custom_colors` via constructor injection
3. `constants.py` (MODIFIED, additive only) — gains `PREFS_PATH`; `USER_PALETTE_PATH` retained as read-only migration-source reference
4. `paste_hidden.py` (MODIFIED, minimal) — `copy_hidden()` reads `get_prefs().link_classes_paste_mode` once at function entry to determine `effective_link_classes`
5. `menu.py` (MODIFIED, additive only) — adds "Preferences..." menu item pointing to `prefs.open_prefs()`

**Build order:** `constants.py` first (no dependencies), then `prefs.py` core and `ColorPaletteDialog` redesign in parallel (independent workstreams), then integration of `anchor.py` call sites and `paste_hidden.py` gate, then `PrefsDialog` UI, then `menu.py` entry point, then Nuke smoke test.

### Critical Pitfalls

1. **ColorPaletteDialog caller contract broken by redesign** — Three callers in `anchor.py` (`create_anchor`, `rename_anchor`, `set_anchor_color`) all depend on `exec_() == Accepted` as the completion signal. Remove `self.accept()` from `_on_swatch_clicked` without adding an alternative confirm path and all three callers stall silently. Prevention: keep `exec_()` / `Accepted` as the done-signal; clicks only update `_selected_color`; Enter / OK / double-click calls `accept()`. Acceptance criteria must verify all three callers require zero code changes.

2. **Split-brain state between user_palette.json and prefs file** — If custom colors are written to both files, `load_user_palette()` (reading old path) and `get_prefs().custom_colors` (reading new path) diverge. Prevention: make the architectural decision explicit before writing any code — custom colors live exclusively in `paste_hidden_prefs.json` after first migration write. Document in the phase plan.

3. **LINK_CLASSES paste mode preference gated in wrong location** — The preference must gate `copy_hidden()` (where the anchor FQNN stamp is written to nodes), not `paste_hidden()` (which only reads the stamp). A gate in `paste_hidden()` is bypassed by re-paste from existing clipboard files. Prevention: add the `effective_link_classes` check at the top of `copy_hidden()` before the `LINK_SOURCE_CLASSES` branch; write a unit test that asserts no `KNOB_NAME` knob is stamped when mode is `"passthrough"`.

4. **Custom colors persisted on Cancel** — If `save_user_palette()` is called immediately inside `_on_custom_color_clicked`, a Cancel or Escape after picking a custom color still writes it to disk. Prevention: stage custom colors in memory during the dialog session; only write to disk when `accept()` is called.

5. **Enter key accepts with no swatch selected** — An unconditional Enter→accept handler fires even when `_selected_color` is only the `initial_color` passed at construction, causing `create_anchor()` to silently accept whatever the pre-highlighted color was. Prevention: define the semantics explicitly — Enter confirms the currently highlighted swatch (including the pre-highlight). This is correct UX: Enter on open confirms the existing color. The handler must guard `_selected_color is not None`; write a unit test for the no-click-Enter case.

## Implications for Roadmap

Based on combined research, two phases are recommended. The workstreams are architecturally independent at the code level and can be built in parallel, but sequencing them ensures each is fully tested before integration.

### Phase 1: Prefs Core and Persistence

**Rationale:** All preferences features — enable/disable toggle, paste-mode toggle, and custom color management — depend on the `Prefs` singleton and `paste_hidden_prefs.json` load/save infrastructure. This is the foundation. Building it first with tests means the dialog (Phase 2) can integrate against a tested API rather than building both simultaneously.

**Delivers:** `prefs.py` module with `Prefs` singleton, `get_prefs()` lazy loader, JSON load/save/migrate, schema definition (`plugin_enabled`, `link_classes_paste_mode`, `custom_colors`), `PREFS_PATH` constant added to `constants.py`, and `copy_hidden()` gate for `link_classes_paste_mode`.

**Addresses features:** Preferences persist across sessions, enable/disable toggle, paste-mode toggle, custom color list persistence, prefs JSON load/save module.

**Avoids pitfalls:** Split-brain state (file layout decision made before code); LINK_CLASSES gate in wrong location (gate built and tested here); prefs file absent on first run (migration logic lives here).

**Research flag:** Standard patterns — singleton with lazy loading is a documented sibling plugin pattern. No phase-level research needed. Unit testing infrastructure (existing nuke stub) is already in place from v1.0.

### Phase 2: Color Picker Redesign and PrefsDialog UI

**Rationale:** `ColorPaletteDialog` redesign is independent of `prefs.py` at the code level (it receives `custom_colors` via injection, not via import). Building it after Phase 1 means the complete `get_prefs()` API is available for `anchor.py` call-site updates and for `PrefsDialog` construction. The UI work is also the most visible user-facing change and benefits from a stable backend.

**Delivers:** Redesigned `ColorPaletteDialog` (click-to-select, Enter/OK-accept, `_redraw_swatch_highlights`, constructor injection of `custom_colors`), swatch order change (custom first), `PrefsDialog` with enable/disable checkbox, paste-mode radio buttons, and custom color `QListWidget` (Add/Remove), "Preferences..." menu item in `menu.py`.

**Addresses features:** All color picker table-stakes features, custom color list Add/Remove in prefs panel, swatch order reorder, pre-selected highlight.

**Avoids pitfalls:** Caller contract broken (acceptance criteria explicitly verify all three `anchor.py` callers unchanged); custom colors persisted on Cancel (staging pattern); Enter key accepts wrong color (semantics defined, guard and test in acceptance criteria); `nuke.getColor()` nested event loop (no `processEvents` added, existing call pattern preserved); preferences panel opened from wrong context (panel accessible from menu only).

**Research flag:** Standard patterns — Qt dialog state machines and `QListWidget` are well-documented. No phase-level research needed. The circular import resolution (dependency injection) is the only non-obvious design decision and is fully specified in ARCHITECTURE.md.

### Phase Ordering Rationale

- `prefs.py` has no dependency on the UI redesign; `ColorPaletteDialog` redesign has no dependency on `prefs.py` — true parallel workstreams, sequenced here only for test stability before integration
- The `copy_hidden()` gate (Phase 1) must be built before `PrefsDialog` (Phase 2) because the dialog's toggle must be testable end-to-end against real copy behavior
- `menu.py` changes are additive in both phases and carry no risk; they are done last in each phase as the integration capstone
- Both phases end with a Nuke smoke test to catch embedded Qt event loop issues that unit tests cannot catch

### Research Flags

Phases with standard patterns (skip research-phase):
- **Phase 1 (Prefs Core):** Singleton with lazy loading is a well-established pattern in this codebase. JSON persistence is already in production. Migration logic is a single existence-check. No research needed.
- **Phase 2 (Color Picker / PrefsDialog):** Qt dialog state machines, `QListWidget`, `QPushButton.setAutoDefault`, and `QPixmap` with `DecorationRole` are all documented in Qt for Python official docs. Dependency injection pattern is fully specified in ARCHITECTURE.md. No research needed.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technologies verified against existing production codebase; only `Qt.DecorationRole` PySide6 shorthand compatibility assessed without Nuke runtime test (MEDIUM sub-item; risk is negligible — PySide6 retains it for backwards compatibility) |
| Features | HIGH | Derived directly from codebase analysis and PROJECT.md v1.1 requirements; no market research needed for single-artist internal tool |
| Architecture | HIGH | Based on direct codebase inspection of all seven source files; sibling plugin pattern confirmed; import chain verified for circular-import risk with resolution specified |
| Pitfalls | HIGH | All seven pitfalls derived from direct codebase analysis of actual call sites and actual code paths; not inferred from general patterns |

**Overall confidence:** HIGH

### Gaps to Address

- **Nuke 15 exact Python subversion:** Confirmed as 3.10/3.11 range (VFX RP 2023) but not pinned. This is irrelevant to v1.1 — no Python-version-specific features are used. No action needed.
- **`Qt.DecorationRole` shorthand in PySide6 under Nuke 16:** Not tested in actual Nuke 16 runtime. Risk is low (PySide6 retains the shorthand for backwards compatibility per official docs). Validate in smoke test at end of Phase 2.
- **Prefs file location on Windows `~/.nuke/` expansion:** `os.path.expanduser('~/.nuke/')` resolves correctly on macOS and Linux; Windows Nuke users typically have `%USERPROFILE%\.nuke`. Confirm `os.path.expanduser` behavior matches `USER_PALETTE_PATH` existing pattern — if the existing palette path works on Windows, the same expansion will work for `PREFS_PATH`.

## Sources

### Primary (HIGH confidence)
- Existing codebase: `/workspace/colors.py`, `anchor.py`, `paste_hidden.py`, `constants.py`, `link.py`, `menu.py` — all v1.0 source files inspected directly
- Existing codebase: `/workspace/PROJECT.md` — v1.1 milestone requirements and constraints
- Qt for Python official docs (doc.qt.io/qtforpython-6/) — QListWidget, QListWidgetItem, QPushButton.setAutoDefault, QPixmap, Qt.DecorationRole
- Foundry release notes Nuke 14.0 — Python 3.9, PySide2 5.15 confirmed
- Foundry support article Q100715 — PySide6 migration in Nuke 16

### Secondary (MEDIUM confidence)
- Erwan Leroy, "Updating Your Python Scripts for Nuke 16 and PySide6" — PySide2→PySide6 guard pattern, enum compatibility
- Sibling plugin pattern: Labelmaker, tabtabtab-nuke — Prefs class + PrefsDialog + `~/.nuke/<plugin>_prefs.json` structure (described in milestone context; not inspected directly)
- Foundry: Custom Panels in Nuke Python Developer's Guide — plugin panel UX norms
- Houdini Qt ColorPalette docs — DCC color palette UX precedent (deferred-accept signal pattern)
- napari issue #6502 — `exec_()` re-entrancy risk in embedded Qt environments

### Tertiary (LOW confidence)
- Nuke 15 Python subversion (3.10/3.11 range inferred from VFX Reference Platform 2023) — irrelevant to v1.1; no action needed

---
*Research completed: 2026-03-10*
*Ready for roadmap: yes*
