# Pitfalls Research

**Domain:** Adding preferences panel and color picker redesign to existing Nuke/PySide Qt plugin
**Researched:** 2026-03-10
**Confidence:** HIGH — based on direct codebase analysis of all source files, plus verified patterns from Nuke/Qt documentation

---

## Critical Pitfalls

### Pitfall 1: ColorPaletteDialog Caller Contract Broken By Redesign

**What goes wrong:**
The redesigned dialog changes `_on_swatch_clicked` to select-without-closing. But three existing callers depend on `dialog.exec_() == Accepted` being the completion signal before reading `dialog.selected_color_int()` and `dialog.chosen_name`. If the dialog no longer calls `self.accept()` on swatch click, those callers stall waiting for a signal that never comes — or they read stale values because `accept()` fires from a different path (e.g., Enter key press).

The three callers are:
- `anchor.create_anchor()` — reads both `chosen_name` and `selected_color_int()` after `exec_()`
- `anchor.rename_anchor()` — reads both after `exec_()`
- `anchor.set_anchor_color()` — reads only `selected_color_int()` after `exec_()`

All three use `if dialog.exec_() == ColorPaletteDialog.Accepted` as the completion gate.

**Why it happens:**
"Click to select without closing" typically means connect `clicked` to a selection-state update rather than `self.accept()`. It's easy to forget that the existing callers rely on `exec_()` returning `Accepted` as the done-signal, not just a selection event.

**How to avoid:**
Keep `exec_()` / `Accepted` as the contract for all three callers. Selection clicks update `self._selected_color` and internal visual state only. A separate confirmation action (Enter key, a "OK" button, or double-click) calls `self.accept()`. Verify all three call sites still work as-is after the redesign — they should require zero changes.

**Warning signs:**
- Any change to `_on_swatch_clicked` that removes or conditionally skips `self.accept()`
- Adding a new "Confirm" button path but forgetting to update `chosen_name` before the accept
- `exec_()` returning `Rejected` (0) when the user pressed Enter after selecting a swatch

**Phase to address:**
Color picker redesign phase — verify all three caller sites in acceptance criteria before merging.

---

### Pitfall 2: user_palette.json and Prefs File Write to Different Paths, Creating a Split-Brain State

**What goes wrong:**
`USER_PALETTE_PATH` in `constants.py` is `~/.nuke/paste_hidden_user_palette.json`. The new preferences panel will introduce a second file (e.g., `~/.nuke/paste_hidden_prefs.json`). If custom colors are stored in both — the old palette file AND the new prefs file — the plugin reads from both inconsistently. The user edits colors in the prefs panel, which writes to the prefs file, but `load_user_palette()` in `colors.py` still reads from the old palette path. Custom colors vanish from the picker.

**Why it happens:**
It is tempting to add the prefs file alongside the existing palette file rather than deciding where custom colors live permanently. The colors UI and the prefs UI are different features so they get different files, but the data overlaps.

**How to avoid:**
Make an explicit architectural decision before writing any code: either (a) the prefs file absorbs the custom palette (migrate `user_palette.json` content into the prefs file on first load), or (b) custom colors remain in `user_palette.json` and the prefs file stores only non-color settings (plugin enabled flag, LINK_CLASSES mode). Option (b) is lower risk because it requires no migration and `colors.py`'s `load_user_palette()` and `save_user_palette()` remain unchanged. Document the decision in the phase plan.

**Warning signs:**
- `colors.py` importing from a prefs module, or a prefs module importing from `colors.py` for color data
- Two different `json.dump` calls that both write color lists to different paths
- `load_user_palette()` returning different results depending on load order

**Phase to address:**
Preferences panel phase — define file layout before any code is written. Record the decision in the PLAN file.

---

### Pitfall 3: LINK_CLASSES Paste Mode Preference Checked Too Late in copy_hidden()

**What goes wrong:**
`copy_hidden()` in `paste_hidden.py` checks `node.Class() in LINK_SOURCE_CLASSES` (line 42) to decide whether to store an anchor FQNN and trigger link-replacement paste behavior. The LINK_CLASSES paste mode preference ("always replace" vs "never replace" vs "only when anchor exists") must gate this check. If the preference is read inside the wrong branch — e.g., only applied during `paste_hidden()` and not during `copy_hidden()` — the hidden knob is still stamped during copy, and paste always replaces regardless of the preference value.

The fix point is line 42 of `paste_hidden.py`: the preference check must happen before the `if node.Class() in LINK_SOURCE_CLASSES` branch, not after.

**Why it happens:**
`paste_hidden()` is the visible "action" and feels like the right place to add a gate. But the copy/paste architecture stamps intent on the node during `copy_hidden()`; paste reads that stamp. A preference that is only checked at paste time is bypassed on re-paste of already-stamped nodes (e.g., paste into a second script from the same clipboard file).

**How to avoid:**
The preference gate belongs in `copy_hidden()`, before the LINK_SOURCE_CLASSES branch. When the mode is "never replace", skip stamping the knob entirely (same effect as `cut=True` for that path). Write a unit test that asserts: given mode="never replace", a copied Read node has no KNOB_NAME knob after `copy_hidden()`.

**Warning signs:**
- The preference is only read in `paste_hidden()`, not in `copy_hidden()`
- Tests for the preference pass in same-session tests but fail when clipboard file is pasted into a new session
- The `cut=True` path in `copy_hidden()` is not consulted when designing the preference gate

**Phase to address:**
Preferences panel phase — specifically the LINK_CLASSES mode sub-feature. Must be tested offline with the existing nuke stub infrastructure.

---

### Pitfall 4: nuke.getColor() Called From Inside exec_() — Nested Event Loop Deadlock

**What goes wrong:**
`ColorPaletteDialog._on_custom_color_clicked()` calls `nuke.getColor()` synchronously while the dialog's own `exec_()` event loop is running. `nuke.getColor()` opens Nuke's native color picker, which itself runs a modal event loop. This creates a nested event loop: Nuke's main event loop → our `exec_()` loop → Nuke's color picker loop. In practice this works, but it is fragile in Nuke's embedded Qt environment: re-entrancy in Qt's event loop is not guaranteed safe, and Nuke versions have historically exhibited freezes or crashes when modal dialogs are stacked from Python-initiated handlers.

If the redesign adds more UI state (e.g., a "live preview" swatch that repaints on hover), the risk of re-entrancy corruption increases.

**Why it happens:**
It works in testing and is the simplest implementation. The issue only surfaces under specific Nuke version × OS combinations, or after the dialog accumulates more event-driven state.

**How to avoid:**
Keep `nuke.getColor()` invocation as-is unless instability is observed — it works today and changing it introduces new risk. Do not add re-entrant event processing (e.g., `QApplication.processEvents()` calls) inside the dialog's event handlers. If the redesign adds a live-preview path, make sure it uses Qt's signal/slot mechanism rather than synchronous paint calls inside event handlers.

**Warning signs:**
- Nuke freezes after clicking "Custom Color..." and the OS color picker appears
- Adding `QApplication.processEvents()` anywhere inside `ColorPaletteDialog` methods
- Any dialog method that opens a second `exec_()` call

**Phase to address:**
Color picker redesign phase — audit any new event-driven code added during the redesign.

---

### Pitfall 5: Enter Key Accepts Before User Has Clicked Any Swatch

**What goes wrong:**
The v1.1 requirement says Enter key should accept the dialog. The current `keyPressEvent` handles Enter only inside `_hint_mode` and only if `self._selected_color is not None`. If the redesign adds an unconditional Enter→accept path (to fix "Enter should work"), it will fire even when no swatch has been clicked and `_selected_color` is still the `initial_color` from construction. The caller in `create_anchor()` then creates an anchor with whatever color was pre-loaded — likely the last-used or default purple — rather than requiring the user to make an explicit choice.

**Why it happens:**
"Enter accepts" is a natural Qt dialog UX pattern, but the dialog has a dual mode: it pre-highlights a color (`initial_color`), so Enter on open is ambiguous — does it confirm the pre-highlighted color or indicate "I haven't picked yet"?

**How to avoid:**
Define the semantics explicitly in the plan: Enter confirms the currently highlighted swatch (the one with white border), including the pre-highlighted one. This means Enter on open with an `initial_color` confirms that color, which is the correct "reconfirm existing color" UX for rename and set-color flows. The create-anchor flow passes `initial_color` too, so Enter confirms the pre-selected color there as well. Write the Enter handler to call `self.accept()` if `self._selected_color is not None`, and add a unit test for the case where Enter is pressed with no swatch ever clicked.

**Warning signs:**
- Enter handler calls `self.accept()` without checking `_selected_color is not None`
- `create_anchor()` caller receiving unexpected color values in UAT
- Test for "Enter with no swatch clicked" is absent from the test plan

**Phase to address:**
Color picker redesign phase — include in the Enter-key acceptance criteria.

---

### Pitfall 6: Custom Colors Persisted to user_palette.json Mid-Dialog, Then Dialog Cancelled

**What goes wrong:**
The v1.1 requirement says custom colors should be persisted. A naive implementation calls `save_user_palette()` immediately when the user picks a custom color via `nuke.getColor()`. If the user then clicks Cancel or presses Escape on the outer dialog, the color is already saved to disk. On next open, the "custom" color appears in the palette even though the user explicitly cancelled.

**Why it happens:**
Persisting immediately feels right (the user picked a color, save it). The Cancel flow is a different code path and it is easy to miss the implication.

**How to avoid:**
Stage custom colors in an in-memory list during the dialog session. Only call `save_user_palette()` when the dialog is accepted (`accept()` is called). In `reject()` or on Escape, discard the staged list. The dialog's `__init__` loads the existing palette into `_user_palette_colors`; `_on_custom_color_clicked` appends to that list and rebuilds the swatch row in-memory; `accept()` writes it to disk.

**Warning signs:**
- `save_user_palette()` called anywhere except in a path that also calls `self.accept()`
- No test for "custom color added, then Cancel pressed, palette unchanged on disk"
- `_on_custom_color_clicked` calling `save_user_palette()` directly

**Phase to address:**
Color picker redesign phase — custom color persistence sub-feature.

---

### Pitfall 7: Preferences Panel Opened From PyScript_Knob or Menu Causes Modal-Under-Nuke-Event Issue

**What goes wrong:**
If the preferences panel is opened from a `nuke.PyScript_Knob` (the same mechanism as "Set Color", "Rename", "Reconnect Child Links"), the knob callback runs inside Nuke's node property panel event handler. Calling `dialog.exec_()` from that context creates a modal loop while Nuke's properties panel is also active. This is generally fine for short dialogs but has been observed to cause issues with preference panels that have persistent state or that write to disk synchronously on apply.

The existing `set_anchor_color()` function calls `dialog.exec_()` from a PyScript_Knob and works correctly. The risk is proportional to the complexity added (disk I/O on apply, signals that trigger Nuke DAG updates from inside the dialog).

**Why it happens:**
Developers test the panel from a menu shortcut (no Nuke property panel open) but users trigger it from the knob. The modal context is different.

**How to avoid:**
Open the preferences panel from a dedicated menu item only, not from a PyScript_Knob. If a knob button is needed, have it call the menu-based entry point rather than spinning up its own `exec_()`. Keep the panel's apply logic synchronous and light — read values, write JSON, close. Do not trigger any `nuke.allNodes()` scans or node mutations from inside the panel's accept path.

**Warning signs:**
- Preferences panel opened by clicking a knob button on a node property panel
- Panel's "Apply" or "OK" button handler calls `nuke.allNodes()` or modifies node knobs
- Panel stores a reference to a Nuke node and mutates it on close

**Phase to address:**
Preferences panel phase — entry point design decision must be made in the plan.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Store prefs and palette in separate files with no migration | Simple; no data migration code | Split-brain state if custom colors move to prefs panel in a future version; `load_user_palette()` path hardcoded | Acceptable only if the decision is documented and custom colors never move to the prefs file |
| Read prefs file on every dialog open (no cache) | Always fresh | Repeated disk reads if dialog opened frequently; slow on network-mounted home directories | Acceptable for a single-artist local tool; flag if performance complaint arises |
| Hardcode preference defaults in `constants.py` | No schema version needed | Adding a new preference requires updating constants AND the JSON read/write path in two places | Acceptable for a small preference set (2-3 settings); revisit if preferences grow beyond 5 |
| Use module-level global for prefs state | Simple | Global mutable state is non-deterministic across test runs; hard to reset between tests | Never acceptable for settings that affect copy_hidden() logic — must be testable in isolation |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `copy_hidden()` + LINK_CLASSES preference | Gate only in `paste_hidden()` | Gate in `copy_hidden()` before the LINK_SOURCE_CLASSES branch; paste reads the stamp, not the pref |
| `ColorPaletteDialog` + `chosen_name` + Enter key | `chosen_name` not updated from `_name_edit` before `accept()` called by Enter | Every path that calls `self.accept()` must first assign `self.chosen_name = self._name_edit.text()` if `_name_edit` is not None |
| Prefs file + user_palette.json co-existence | Prefs module imports colors module to read/write palette | Keep palette I/O in `colors.py` exclusively; prefs module stores only non-color settings |
| `nuke.getColor()` inside `exec_()` loop | Adding `QApplication.processEvents()` to keep UI responsive | Do not add processEvents; keep `nuke.getColor()` as a blocking call — it already manages its own event loop |
| PySide2 vs PySide6 version guard | New dialog code uses PySide6-only API without guard | All new dialog code must sit inside the `if QtWidgets is None: ... else:` guard; test that `ColorPaletteDialog = None` path is still exercised in Qt-absent environments |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `_get_script_backdrop_colors()` called on every dialog open | Dialog slow to open in scripts with 100+ backdrops | No change needed at this scale; single artist tool | Not a real concern at expected usage; do not pre-cache |
| Prefs file read on every `copy_hidden()` call | Copy operation slows when disk is slow | Cache the preference in a module-level variable; reload only on explicit "Reload Preferences" or plugin init | Irrelevant for local disk; matters on network home dir |
| `save_user_palette()` called synchronously inside dialog accept | Blocking disk write inside Qt event handler | Acceptable for small JSON file; would matter at 1000+ colors | Not a concern at expected usage |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Enter on dialog open confirms pre-highlighted color unexpectedly | User types anchor name, presses Enter to confirm name, unintentionally changes color to pre-highlighted one | Confirm semantics in plan: Enter confirms current highlighted swatch (including pre-highlight). This is correct — user who wants a different color clicks before pressing Enter |
| Cancel after picking custom color leaves color in palette | User sees a color they explicitly rejected reappear on next open | Stage custom colors in-memory; only persist on accept |
| "Custom Color..." button opens OS color picker which may render behind the dialog on some OSes | User sees nothing happen | Known risk with `nuke.getColor()`; no mitigation available without replacing it with `QColorDialog` — not worth the complexity |
| Preferences panel "Disable plugin" toggle takes effect immediately without restart explanation | User disables plugin, Ctrl+C still intercepts | Explain in the panel that menu overrides require a Nuke restart or re-source of menu.py |
| Swatch order change (custom → backdrop → Nuke defaults) reorders grid on every open | User has memorized swatch positions; positions shift each session as backdrops change | Document the order as intentional in-panel; do not add session-persistence of swatch positions — it would conflict with the dynamic backdrop list |

---

## "Looks Done But Isn't" Checklist

- [ ] **Enter-key acceptance:** Verify Enter works when a swatch is highlighted AND when no swatch has been clicked since dialog open. Check all three callers (`create_anchor`, `rename_anchor`, `set_anchor_color`) produce correct results.
- [ ] **Cancel does not persist custom colors:** After picking a custom color and pressing Cancel, open the dialog again and verify the new color does not appear in the custom row.
- [ ] **LINK_CLASSES preference gate in copy_hidden:** Copy a Read node with mode="never replace", then paste — verify a plain Read node is pasted, not a Link node.
- [ ] **Prefs file absent on first run:** Delete `~/.nuke/paste_hidden_prefs.json`, restart Nuke, and verify defaults load cleanly without errors.
- [ ] **Prefs file with unknown keys:** Add an unknown key to the JSON manually, reload plugin, verify it is silently ignored and does not crash.
- [ ] **Qt unavailable path still works:** Verify `ColorPaletteDialog is None` branch in all callers falls back to `nuke.getInput()` correctly after any redesign changes.
- [ ] **chosen_name populated on all accept paths:** Test Enter key, swatch click, and "Custom Color..." — all three must set `chosen_name` before accept when `show_name_field=True`.
- [ ] **All three existing callers unchanged:** `create_anchor()`, `rename_anchor()`, and `set_anchor_color()` in `anchor.py` must require zero code changes after the dialog redesign.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| caller contract broken — dialog redesign breaks create_anchor or rename_anchor | MEDIUM | Revert `_on_swatch_clicked` to call `accept()`; add separate selection-state path; re-run all three caller UAT |
| Split-brain prefs + palette files | MEDIUM | Write a one-time migration function that reads `user_palette.json`, merges into prefs file if that was the chosen architecture, deletes old file; ship as a hotfix plan |
| LINK_CLASSES pref gated in wrong location (paste not copy) | LOW | Move check to `copy_hidden()`; add unit test; re-stamp: existing clipboard files already in the wild will paste with old behavior once, then recover |
| custom colors persist on Cancel | LOW | Wrap `save_user_palette()` call in accept-only path; no data loss, just unexpected extra palette entry user can remove via prefs panel |
| Enter key accepts with wrong color | LOW | Tighten Enter handler guard to check `_selected_color is not None`; add unit test |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| ColorPaletteDialog caller contract broken | Color picker redesign phase | All three callers verified in acceptance criteria; zero changes to anchor.py caller code |
| user_palette.json + prefs file split-brain | Preferences panel phase — file layout decision at plan start | Confirm `load_user_palette()` path in colors.py unchanged; single source of truth documented |
| LINK_CLASSES preference gated in wrong location | Preferences panel phase — LINK_CLASSES mode sub-task | Offline unit test: copy Read node with mode="never replace"; assert no KNOB_NAME stamped |
| nuke.getColor() nested event loop risk | Color picker redesign phase | No `QApplication.processEvents()` in any new dialog code; audit during code review |
| Enter key accepts before swatch selected | Color picker redesign phase | Unit test: press Enter with no click; verify `_selected_color` is the initial_color, not None |
| Custom colors persisted on Cancel | Color picker redesign phase — persistence sub-task | Test: pick custom color → Cancel → reopen → verify new color absent |
| Preferences panel opened from PyScript_Knob | Preferences panel phase — entry point design | Panel only accessible from menu; no PyScript_Knob added for preferences |

---

## Sources

- Direct codebase analysis: `/workspace/colors.py` (ColorPaletteDialog, load_user_palette, save_user_palette)
- Direct codebase analysis: `/workspace/anchor.py` (create_anchor, rename_anchor, set_anchor_color — all three callers)
- Direct codebase analysis: `/workspace/paste_hidden.py` (copy_hidden lines 25–93, LINK_SOURCE_CLASSES gate)
- Direct codebase analysis: `/workspace/constants.py` (USER_PALETTE_PATH, LINK_SOURCE_CLASSES)
- Codebase concern audit: `.planning/codebase/CONCERNS.md` (widget lifecycle, bare exception handling, Qt unavailable path)
- v1.0 retrospective: `.planning/RETROSPECTIVE.md` (what patterns worked, what caused rework)
- [Foundry: Q100715 — How to address Python PySide issues in Nuke 16+](https://support.foundry.com/hc/en-us/articles/25604028087570-Q100715-How-to-address-Python-PySide-issues-in-Nuke-16)
- [Foundry: Custom Panels — NUKE Python Developer's Guide](https://learn.foundry.com/nuke/developers/111/pythondevguide/custom_panels.html)
- [napari: Use open instead of exec for QDialogs](https://github.com/napari/napari/issues/6502) — background on exec_() re-entrancy in embedded Qt environments
- Personal knowledge: Nuke embedded Qt event loop modal stacking behavior (MEDIUM confidence — corroborated by Foundry developer guide)

---

*Pitfalls research for: paste_hidden v1.1 — preferences panel and color picker redesign*
*Researched: 2026-03-10*
