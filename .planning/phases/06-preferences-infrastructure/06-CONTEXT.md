# Phase 6: Preferences Infrastructure - Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Create a `prefs.py` module providing a module-level singleton for plugin preferences persisted to `~/.nuke/paste_hidden_prefs.json`. Migrate custom colors from the old `paste_hidden_user_palette.json` into the new prefs file. Gate LINK_CLASSES copy behavior on `link_classes_paste_mode`. Gate all plugin functionality on `plugin_enabled`.

Color picker dialog redesign and the PrefsDialog UI are Phase 7.

</domain>

<decisions>
## Implementation Decisions

### Prefs module structure
- Module-level singleton: `import prefs; prefs.plugin_enabled`, `prefs.link_classes_paste_mode`, `prefs.custom_colors`
- Loads `paste_hidden_prefs.json` at import time (Nuke startup — once per session)
- Phase 7 calls `prefs.save()` after the PrefsDialog closes

### Prefs file keys and defaults
- `plugin_enabled` — default `True`
- `link_classes_paste_mode` — values: `"create_link"` (default) or `"passthrough"`
- `custom_colors` — default `[]`

### link_classes_paste_mode gate
- Lives in `copy_hidden()` where the FQNN stamp is written (already decided in STATE.md)
- When `"passthrough"`: skip FQNN stamping for LINK_CLASSES nodes entirely — plain `nuke.nodeCopy()` with no stamp and no `add_input_knob()` call for those nodes
- Other copy paths (hidden Dots, anchors) are unaffected by this pref

### plugin_enabled scope
- When `False`: ALL plugin functionality is disabled — clipboard trio falls through to `nuke.nodeCopy()`/`nuke.nodePaste()`, AND all anchor operations (Create Anchor, Alt+A, Alt+Z, labels) are silent no-ops
- All Anchors menu items are greyed out except the Preferences entry
- Menu items re-enable/re-disable when user toggles the setting via Preferences dialog (Phase 7 triggers this)
- Note: `link_classes_paste_mode` is a separate, independent pref for controlling LINK_CLASSES behavior when the plugin IS enabled

### Migration from old palette file
- Lazy migration: on first load, if `paste_hidden_prefs.json` does not exist but `paste_hidden_user_palette.json` does, read colors from old file and populate `custom_colors` in the new prefs
- Write new prefs file on first save; never write to `paste_hidden_user_palette.json` again
- If old file has invalid/corrupt data: silently use empty `custom_colors`

### colors.py transition
- `load_user_palette()` and `save_user_palette()` are removed in Phase 6
- `ColorPaletteDialog` receives `custom_colors` as a constructor parameter (no import of `prefs` from `colors.py` — prevents circular dependency)
- Callers that previously called `load_user_palette()` now read `prefs.custom_colors` directly
- `ColorPaletteDialog` does not write custom_colors — write path stays with callers (unchanged)

### Claude's Discretion
- Error handling for corrupt/missing prefs file: silent fallback to defaults
- Exact JSON schema validation approach
- How `prefs.save()` is structured internally

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `constants.py:USER_PALETTE_PATH` — the old palette path; used by `colors.py`. Will be superseded by the new prefs path in Phase 6.
- `colors.py:load_user_palette()` / `save_user_palette()` — to be removed and replaced by prefs reads/writes
- `colors.py:ColorPaletteDialog` — currently calls `load_user_palette()` at line 151 inside `_build_ui()`; Phase 6 adds a `custom_colors` constructor parameter and removes that internal call
- `menu.py:anchors_menu` — the Anchors submenu where menu items will be disabled when `plugin_enabled=False`; a Preferences entry will be added here in Phase 7

### Established Patterns
- Module-level imports from `constants.py` used throughout — `prefs.py` should follow same pattern
- PySide2/PySide6 Qt guard in `colors.py` — prefs.py has no Qt dependency (pure Python/JSON)
- `os.path.expanduser('~/.nuke/...')` pattern already used in `constants.py` for `USER_PALETTE_PATH`

### Integration Points
- `paste_hidden.py:copy_hidden()` — gate for `link_classes_paste_mode` and `plugin_enabled`
- `paste_hidden.py:cut_hidden()`, `paste_hidden()` — gate for `plugin_enabled`
- `anchor.py` — all public entry points (create_anchor, rename, navigate) gated on `plugin_enabled`
- `labels.py` — all entry points gated on `plugin_enabled`
- `menu.py` — menu item enable/disable driven by `plugin_enabled`; Preferences entry exempt

</code_context>

<specifics>
## Specific Ideas

- "The disable menu item should disable all functionality" — `plugin_enabled=False` is a full plugin off-switch, not just a clipboard toggle
- Menu items greyed out except Preferences when disabled, re-enabled on toggle (not just at startup)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-preferences-infrastructure*
*Context gathered: 2026-03-10*
