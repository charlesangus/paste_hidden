---
phase: 06-preferences-infrastructure
verified: 2026-03-11T00:00:00Z
status: passed
score: 13/13 must-haves verified
re_verification: false
---

# Phase 6: Preferences Infrastructure Verification Report

**Phase Goal:** Plugin preferences persist across sessions and the paste-mode toggle controls LINK_CLASSES copy behavior
**Verified:** 2026-03-11
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| #  | Truth                                                                                                                                     | Status     | Evidence                                                                                   |
|----|-------------------------------------------------------------------------------------------------------------------------------------------|------------|--------------------------------------------------------------------------------------------|
| 1  | `~/.nuke/paste_hidden_prefs.json` is created on first run with `plugin_enabled`, `link_classes_paste_mode`, `custom_colors` keys          | VERIFIED   | `prefs.save()` writes all three keys via `json.dump`; `PREFS_PATH` constant correct        |
| 2  | On first run with old `paste_hidden_user_palette.json`, colors migrate; old file is never written                                         | VERIFIED   | `_migrate_from_old_palette()` reads from `USER_PALETTE_PATH`, never writes to it           |
| 3  | When `plugin_enabled` is false, Ctrl+C/X/V pass through to Nuke default clipboard; no anchor/FQNN activity                               | VERIFIED   | `copy_hidden`, `cut_hidden`, `paste_hidden` each have early-return gates; anchor/label fns also gated |
| 4  | When `link_classes_paste_mode` is `passthrough`, copying a Read/Camera node produces a plain Nuke copy with no FQNN stamp                 | VERIFIED   | `continue` inside `if node.Class() in LINK_SOURCE_CLASSES` block before stamping logic    |

**Score:** 4/4 success criteria verified

---

## Required Artifacts

| Artifact         | Expected                                                          | Status     | Details                                                                                  |
|------------------|-------------------------------------------------------------------|------------|------------------------------------------------------------------------------------------|
| `prefs.py`       | Module-level singleton with `plugin_enabled`, `link_classes_paste_mode`, `custom_colors`, `save()` | VERIFIED | All four present; `_load()` runs at import; `save()` writes all keys |
| `constants.py`   | Exports `PREFS_PATH` constant                                     | VERIFIED   | Line 32: `PREFS_PATH = os.path.expanduser('~/.nuke/paste_hidden_prefs.json')`            |
| `colors.py`      | `ColorPaletteDialog` with `custom_colors=None` parameter; no `load_user_palette`/`save_user_palette` | VERIFIED | Functions removed; param added at line 94; `self._custom_colors` stored; used in `_build_ui` line 130 |
| `paste_hidden.py`| `import prefs`; `plugin_enabled` gates in 3 clipboard functions; passthrough gate in Path A | VERIFIED | Line 24: `import prefs`; gates at lines 35, 106, 135; passthrough at lines 48-49 |
| `anchor.py`      | `import prefs`; 6 entry-point gates; 3x `custom_colors=prefs.custom_colors` injections | VERIFIED | Line 40: `import prefs`; 6 gates confirmed; injections at lines 135, 269, 337 |
| `labels.py`      | `import prefs`; 3 label entry-point gates                         | VERIFIED   | Line 13: `import prefs`; gates at lines 47, 61, 75                                      |
| `menu.py`        | `_gated_menu_items` list; `set_anchors_menu_enabled()` function; startup state call | VERIFIED | Lines 33, 72, 84; `hasattr` guard present; old commands ungated               |

---

## Key Link Verification

| From                                      | To                              | Via                                                      | Status   | Details                                                               |
|-------------------------------------------|---------------------------------|----------------------------------------------------------|----------|-----------------------------------------------------------------------|
| `prefs.py`                                | `constants.py`                  | `from constants import PREFS_PATH, USER_PALETTE_PATH`    | WIRED    | Line 15 of prefs.py                                                   |
| `prefs._load()`                           | `prefs._migrate_from_old_palette()` | Called when prefs file absent                        | WIRED    | Lines 50-52: `if not os.path.exists(PREFS_PATH): _migrate_from_old_palette()` |
| `paste_hidden.copy_hidden`                | `prefs.plugin_enabled`          | Early-return guard at top of function                    | WIRED    | Lines 35-37: first statement in `copy_hidden()`                       |
| `paste_hidden.copy_hidden` Path A         | `prefs.link_classes_paste_mode` | `continue` skip inside `LINK_SOURCE_CLASSES` branch     | WIRED    | Lines 47-49: `if prefs.link_classes_paste_mode == 'passthrough': continue` |
| `ColorPaletteDialog.__init__`             | `_build_ui`                     | `self._custom_colors` stored; used as `user_palette_colors` | WIRED  | Line 102 stores; line 130 uses                                        |
| `anchor.py` public entry points           | `prefs.plugin_enabled`          | Early-return guard at top of each gated function         | WIRED    | All 6 functions: `create_anchor`, `rename_selected_anchor`, `anchor_shortcut`, `select_anchor_and_create`, `select_anchor_and_navigate`, `navigate_back` |
| `menu.py` `addCommand` calls              | `_gated_menu_items` list        | Stored return value via `_add_gated_command`             | WIRED    | `_gated_menu_items.append(item)` in `_add_gated_command`; 10 items tracked |
| `ColorPaletteDialog` call sites in `anchor.py` | `prefs.custom_colors`    | `custom_colors=prefs.custom_colors` keyword argument     | WIRED    | Lines 135, 269, 337 in anchor.py                                      |

---

## Requirements Coverage

| Requirement | Source Plans      | Description                                                                                                 | Status     | Evidence                                                         |
|-------------|-------------------|-------------------------------------------------------------------------------------------------------------|------------|------------------------------------------------------------------|
| PREFS-01    | 06-01, 06-02      | Preferences persisted to `~/.nuke/paste_hidden_prefs.json` with keys: `plugin_enabled`, `link_classes_paste_mode`, `custom_colors` | SATISFIED | `prefs.save()` writes all three; `PREFS_PATH` correct; `_load()` reads them back |
| PREFS-02    | 06-01             | On first run with no prefs file, existing `paste_hidden_user_palette.json` colors migrate; old file never written again | SATISFIED | `_migrate_from_old_palette()` reads only; called when `PREFS_PATH` absent |
| PREFS-03    | 06-03, 06-04      | When plugin disabled, `copy_hidden()`, `cut_hidden()`, `paste_hidden()` fall through to Nuke default; anchor/label functions return immediately | SATISFIED | 3 clipboard gates + 6 anchor gates + 3 label gates all implemented |
| PREFS-04    | 06-03             | When `link_classes_paste_mode` is `passthrough`, copying LINK_CLASSES node produces plain Nuke copy — no anchor creation, no FQNN stamp | SATISFIED | `continue` at line 48-49 of paste_hidden.py skips all stamping; node still included in `nuke.nodeCopy()` at end |

No orphaned requirements: all four PREFS IDs claimed by plans and verified in code.

---

## Anti-Patterns Found

| File        | Line | Pattern      | Severity | Impact                                                                          |
|-------------|------|--------------|----------|---------------------------------------------------------------------------------|
| `colors.py` | 29   | `return []`  | INFO     | Legitimate early-exit in `_get_nuke_pref_colors()` when called outside Nuke — documented in docstring |
| `paste_hidden.py` | 155 | "placeholders" | INFO | Word appears in a code comment describing cross-script paste behavior — not a stub |

No blocker or warning-level anti-patterns found.

---

## Human Verification Required

### 1. Prefs file created on first Nuke launch

**Test:** Delete `~/.nuke/paste_hidden_prefs.json`, launch Nuke, trigger any copy via Ctrl+C, then quit; open the prefs file.
**Expected:** File exists with `plugin_enabled: true`, `link_classes_paste_mode: "create_link"`, `custom_colors: []`.
**Why human:** Requires a live Nuke session to exercise the save path.

### 2. Migration from old palette file

**Test:** Delete `~/.nuke/paste_hidden_prefs.json`, ensure `~/.nuke/paste_hidden_user_palette.json` has color values, launch Nuke.
**Expected:** After Phase 7 Preferences dialog opens and saves, the `paste_hidden_prefs.json` contains those colors; the old palette file is unmodified.
**Why human:** Requires a live Nuke session; migration runs at import time.

### 3. plugin_enabled=False disables Ctrl+C/X/V plugin behavior

**Test:** Set `plugin_enabled` to False in `~/.nuke/paste_hidden_prefs.json`, launch Nuke, copy a Read node (Ctrl+C), then paste (Ctrl+V).
**Expected:** Pasted node is a plain Read node — no hidden knob, no FQNN stamp.
**Why human:** Requires a live Nuke session to verify absence of knob stamping.

### 4. passthrough mode copies Read/Camera plain

**Test:** Set `link_classes_paste_mode` to `"passthrough"` in `~/.nuke/paste_hidden_prefs.json`, launch Nuke, copy a Read node (Ctrl+C), paste (Ctrl+V).
**Expected:** Pasted Read node has no `copy_hidden_input_node` knob — identical to standard Nuke paste behavior.
**Why human:** Requires a live Nuke session to inspect pasted node knobs.

### 5. Menu items grey out when plugin_enabled=False

**Test:** Set `plugin_enabled` to False in prefs file, launch Nuke, open Edit > Anchors menu.
**Expected:** All gated items (Create Anchor, Rename Anchor, etc.) are greyed out; Copy (old), Cut (old), Paste (old) remain active.
**Why human:** Visual menu state cannot be verified programmatically; depends on Nuke 13+ `setEnabled` support.

---

## Gaps Summary

No gaps found. All 13 must-have checks pass:

- `prefs.py` singleton is substantive and fully wired to `constants.py`
- `_load()` / `_migrate_from_old_palette()` / `save()` all implement correct logic with proper error handling
- `colors.py` palette functions removed; `custom_colors` injection path complete end-to-end
- `paste_hidden.py` has all three `plugin_enabled` early-returns and the passthrough `continue` in the correct position (inside `LINK_SOURCE_CLASSES` block, before `if cut:`)
- `anchor.py` has all 6 entry-point gates and 3 `custom_colors=prefs.custom_colors` injections
- `labels.py` has all 3 entry-point gates
- `menu.py` has `_gated_menu_items`, `set_anchors_menu_enabled()`, startup state call, and old commands ungated

All four PREFS requirements satisfied. Phase goal achieved.

---

_Verified: 2026-03-11_
_Verifier: Claude (gsd-verifier)_
