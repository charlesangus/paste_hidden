# Roadmap: paste_hidden

## Milestones

- ✅ **v1.0 MVP** — Phases 1-5 (shipped 2026-03-10)
- 🚧 **v1.1 Polish** — Phases 6-7 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-5) — SHIPPED 2026-03-10</summary>

- [x] Phase 1: Copy-Paste Semantics (3/3 plans) — completed 2026-03-04
- [x] Phase 2: Cross-Script Paste (1/1 plans) — completed 2026-03-05
- [x] Phase 3: Anchor Color System (2/2 plans) — completed 2026-03-07
- [x] Phase 4: Anchor Navigation (4/4 plans) — completed 2026-03-10
- [x] Phase 5: Refactor cross-script paste logic / DOT_TYPE distinction (3/3 plans) — completed 2026-03-05

Full archive: `.planning/milestones/v1.0-ROADMAP.md`

</details>

### 🚧 v1.1 Polish (In Progress)

**Milestone Goal:** Redesign the color picker dialog for usability, and add a preferences panel for plugin-wide settings.

- [x] **Phase 6: Preferences Infrastructure** - Prefs singleton, JSON persistence, migration from old palette file, and LINK_CLASSES paste-mode gate in copy_hidden() (completed 2026-03-11)
- [ ] **Phase 7: Color Picker Redesign and Preferences Panel** - ColorPaletteDialog state machine redesign, PrefsDialog UI with all controls, and menu entry point

## Phase Details

### Phase 6: Preferences Infrastructure
**Goal**: Plugin preferences persist across sessions and the paste-mode toggle controls LINK_CLASSES copy behavior
**Depends on**: Phase 5 (v1.0 complete)
**Requirements**: PREFS-01, PREFS-02, PREFS-03, PREFS-04
**Success Criteria** (what must be TRUE):
  1. A `~/.nuke/paste_hidden_prefs.json` file is created on first run containing `plugin_enabled`, `link_classes_paste_mode`, and `custom_colors` keys
  2. On first run when an old `paste_hidden_user_palette.json` exists, its colors appear in the new prefs file and the old file is never written to again
  3. When `plugin_enabled` is false, Ctrl+C/X/V pass through to Nuke's default clipboard behavior with no anchor or FQNN activity
  4. When `link_classes_paste_mode` is `passthrough`, copying a Read or Camera node produces a plain Nuke copy with no FQNN stamp on the node
**Plans**: 5 plans

Plans:
- [x] 06-01-PLAN.md — prefs.py singleton module + PREFS_PATH constant in constants.py
- [x] 06-02-PLAN.md — colors.py transition: remove palette funcs, add custom_colors constructor param
- [x] 06-03-PLAN.md — paste_hidden.py plugin_enabled and passthrough gates
- [x] 06-04-PLAN.md — anchor.py + labels.py entry point gates + menu.py gating infrastructure
- [ ] 06-05-PLAN.md — gap closure: call save() in _load() to materialize prefs file on first run

### Phase 7: Color Picker Redesign and Preferences Panel
**Goal**: Users can configure plugin settings from the Anchors menu and the color picker behaves as a standard selection dialog
**Depends on**: Phase 6
**Requirements**: PANEL-01, PANEL-02, PANEL-03, PANEL-04, PANEL-05, PANEL-06, PANEL-07, PICKER-01, PICKER-02, PICKER-03, PICKER-04, PICKER-05
**Success Criteria** (what must be TRUE):
  1. User can open a Preferences dialog from the Anchors menu and toggle the plugin on/off; the setting survives a Nuke restart
  2. User can switch LINK_CLASSES paste mode between "Create link" and "Paste copy" in the Preferences dialog; the setting survives a Nuke restart
  3. User can view, add, remove, and replace custom colors in the Preferences dialog; the updated list appears in the color picker swatch group on next open
  4. Clicking a color swatch in the picker highlights it without closing the dialog; pressing Enter or clicking OK confirms the selection and closes
  5. The color picker opens with the current anchor color pre-highlighted, and swatch groups appear in order: custom colors, backdrop colors, Nuke defaults
**Plans**: 3 plans

Plans:
- [ ] 07-01-PLAN.md — ColorPaletteDialog redesign: click-to-select, OK button, group reordering, custom color staging
- [ ] 07-02-PLAN.md — PrefsDialog new class: layout, swatch CRUD, accept lifecycle
- [ ] 07-03-PLAN.md — menu.py Preferences... entry point + human verification

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Copy-Paste Semantics | v1.0 | 3/3 | Complete | 2026-03-04 |
| 2. Cross-Script Paste | v1.0 | 1/1 | Complete | 2026-03-05 |
| 3. Anchor Color System | v1.0 | 2/2 | Complete | 2026-03-07 |
| 4. Anchor Navigation | v1.0 | 4/4 | Complete | 2026-03-10 |
| 5. DOT_TYPE Distinction | v1.0 | 3/3 | Complete | 2026-03-05 |
| 6. Preferences Infrastructure | 5/5 | Complete   | 2026-03-12 | 2026-03-11 |
| 7. Color Picker Redesign and Preferences Panel | v1.1 | 0/3 | Not started | - |
