---
phase: 06-preferences-infrastructure
verified: 2026-03-11T14:00:00Z
status: passed
score: 5/5 must-haves verified
re_verification:
  previous_status: passed
  previous_score: 13/13 (pre-UAT)
  note: "Previous VERIFICATION.md was written before UAT ran. UAT found one gap (Test 1: prefs file not created on first run). Plan 06-05 closed it. This is the post-gap-closure re-verification."
  gaps_closed:
    - "~/.nuke/paste_hidden_prefs.json is created on first run containing plugin_enabled, link_classes_paste_mode, and custom_colors keys"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Prefs file created on first Nuke launch"
    expected: "Delete ~/.nuke/paste_hidden_prefs.json, launch Nuke, load plugin — file exists with plugin_enabled=true, link_classes_paste_mode='create_link', custom_colors=[]"
    why_human: "Requires a live Nuke session to confirm file materialization at startup"
  - test: "Migration from old palette file"
    expected: "Delete prefs file, keep old palette file, launch Nuke — prefs file created containing those colors; old palette file unmodified"
    why_human: "Requires a live Nuke session; migration runs at import time"
  - test: "plugin_enabled=False disables Ctrl+C/X/V plugin behavior"
    expected: "Pasted node is a plain Read node — no hidden knob, no FQNN stamp"
    why_human: "Requires a live Nuke session to verify absence of knob stamping"
  - test: "passthrough mode copies Read/Camera plain"
    expected: "Pasted Read node has no copy_hidden_input_node knob"
    why_human: "Requires a live Nuke session to inspect pasted node knobs"
  - test: "Menu items grey out when plugin_enabled=False"
    expected: "All gated anchor/label items greyed out; old copy/cut/paste remain active"
    why_human: "Visual menu state cannot be verified programmatically"
---

# Phase 6: Preferences Infrastructure Verification Report

**Phase Goal:** Plugin preferences persist across sessions and the paste-mode toggle controls LINK_CLASSES copy behavior
**Verified:** 2026-03-11
**Status:** PASSED
**Re-verification:** Yes — after gap closure (Plan 06-05: save() on first run)

---

## Re-Verification Context

The previous VERIFICATION.md (written immediately after plan execution) was marked `passed` before UAT ran. UAT Test 1 then revealed a gap: `~/.nuke/paste_hidden_prefs.json` was never written to disk on first Nuke startup because `_load()` returned immediately after `_migrate_from_old_palette()` without calling `save()`. Plan 06-05 added one line — `save()` after `_migrate_from_old_palette()` in the file-absent branch — and added three unit tests to lock in the behaviour. This re-verification confirms the gap is closed and no regressions were introduced.

---

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria + UAT gap)

| #  | Truth                                                                                                                                          | Status     | Evidence                                                                                                         |
|----|------------------------------------------------------------------------------------------------------------------------------------------------|------------|------------------------------------------------------------------------------------------------------------------|
| 1  | `~/.nuke/paste_hidden_prefs.json` is created on first run with `plugin_enabled`, `link_classes_paste_mode`, `custom_colors` keys               | VERIFIED   | `prefs.py` line 52: `save()` called in `_load()` file-absent branch after `_migrate_from_old_palette()`; 3 unit tests pass (test_prefs.py) |
| 2  | On first run with old `paste_hidden_user_palette.json`, colors migrate; old file is never written                                              | VERIFIED   | `_migrate_from_old_palette()` reads from `USER_PALETTE_PATH` only; `save()` call materializes the new prefs file with migrated colors |
| 3  | When `plugin_enabled` is false, Ctrl+C/X/V pass through to Nuke default clipboard; anchor/label functions return immediately                   | VERIFIED   | `copy_hidden` line 35, `cut_hidden` line 106, `paste_hidden` line 135 all have early-return gates; 6 anchor gates at lines 287, 310, 492, 509, 548, 635; 3 label gates at lines 47, 61, 75 |
| 4  | When `link_classes_paste_mode` is `passthrough`, copying a Read/Camera node produces a plain Nuke copy with no FQNN stamp                      | VERIFIED   | `paste_hidden.py` lines 48-49: `continue` inside `if node.Class() in LINK_SOURCE_CLASSES` before stamping logic |
| 5  | Preferences load from disk on import and can be persisted via `save()`; corrupt/missing file silently falls back to defaults                   | VERIFIED   | `_load()` wraps file open in `try/except (OSError, ValueError, json.JSONDecodeError)`; `pass` on exception; defaults remain |

**Score:** 5/5 success criteria verified

---

## Required Artifacts

| Artifact          | Expected                                                                                                 | Status     | Details                                                                                                             |
|-------------------|----------------------------------------------------------------------------------------------------------|------------|---------------------------------------------------------------------------------------------------------------------|
| `prefs.py`        | Module-level singleton; `plugin_enabled`, `link_classes_paste_mode`, `custom_colors`, `save()`; `save()` called in file-absent branch of `_load()` | VERIFIED | Lines 20-22: defaults; line 52: `save()` in file-absent branch; line 68: `save()` writes all three keys; line 86: `_load()` at import |
| `constants.py`    | Exports `PREFS_PATH` constant alongside existing `USER_PALETTE_PATH`                                     | VERIFIED   | Line 31: `USER_PALETTE_PATH`; line 32: `PREFS_PATH = os.path.expanduser('~/.nuke/paste_hidden_prefs.json')`        |
| `colors.py`       | `ColorPaletteDialog` accepts `custom_colors=None`; no `load_user_palette`/`save_user_palette`; no `import prefs` | VERIFIED | Line 94: `custom_colors=None` param; line 102: `self._custom_colors`; line 130: `user_palette_colors = self._custom_colors`; `grep` confirms no `import prefs`, no `USER_PALETTE_PATH` |
| `paste_hidden.py` | `import prefs`; `plugin_enabled` gates in 3 clipboard functions; passthrough gate in Path A               | VERIFIED   | Line 24: `import prefs`; gates at lines 35, 106, 135; passthrough `continue` at lines 48-49                        |
| `anchor.py`       | `import prefs`; 6 entry-point gates; 3x `custom_colors=prefs.custom_colors` injections                   | VERIFIED   | Line 40: `import prefs`; gates at lines 287, 310, 492, 509, 548, 635; injections at lines 135, 269, 337            |
| `labels.py`       | `import prefs`; 3 label entry-point gates                                                                 | VERIFIED   | Line 13: `import prefs`; gates at lines 47, 61, 75                                                                 |
| `menu.py`         | `_gated_menu_items` list; `set_anchors_menu_enabled()` function; startup state call                       | VERIFIED   | Lines 33, 43, 72-78, 84: list, append in helper, function def, startup call with `prefs.plugin_enabled`            |
| `tests/test_prefs.py` | 3 tests covering file creation on first run, migration path, no-overwrite on existing file           | VERIFIED   | File exists; all 3 tests pass: `Ran 3 tests in 0.002s OK`                                                          |

---

## Key Link Verification

| From                                       | To                                  | Via                                                              | Status  | Details                                                                                              |
|--------------------------------------------|-------------------------------------|------------------------------------------------------------------|---------|------------------------------------------------------------------------------------------------------|
| `prefs.py`                                 | `constants.py`                      | `from constants import PREFS_PATH, USER_PALETTE_PATH`            | WIRED   | Line 15 of prefs.py                                                                                  |
| `prefs._load()` file-absent branch         | `prefs.save()`                      | Direct call after `_migrate_from_old_palette()` before `return`  | WIRED   | Line 52: `save()` — gap closure confirmed; test_prefs.py test_file_created_on_first_run_* passes     |
| `prefs._load()`                            | `prefs._migrate_from_old_palette()` | Called when prefs file absent                                    | WIRED   | Lines 50-53: `if not os.path.exists(PREFS_PATH): _migrate_from_old_palette(); save(); return`        |
| `paste_hidden.copy_hidden`                 | `prefs.plugin_enabled`              | Early-return guard at top of function                            | WIRED   | Lines 35-37: first statement in `copy_hidden()`                                                      |
| `paste_hidden.copy_hidden` Path A          | `prefs.link_classes_paste_mode`     | `continue` skip inside `LINK_SOURCE_CLASSES` branch              | WIRED   | Lines 48-49: `if prefs.link_classes_paste_mode == 'passthrough': continue`                           |
| `ColorPaletteDialog.__init__`              | `_build_ui`                         | `self._custom_colors` stored; used as `user_palette_colors`      | WIRED   | Line 102 stores; line 130 uses                                                                       |
| `anchor.py` public entry points (6 total)  | `prefs.plugin_enabled`              | Early-return guard at top of each gated function                 | WIRED   | Gates at lines 287, 310, 492, 509, 548, 635                                                         |
| `menu.py` `addCommand` calls               | `_gated_menu_items` list            | `_gated_menu_items.append(item)` in `_add_gated_command`         | WIRED   | Line 43: append; line 84: startup state call                                                         |
| `ColorPaletteDialog` call sites in anchor  | `prefs.custom_colors`               | `custom_colors=prefs.custom_colors` keyword argument             | WIRED   | Lines 135, 269, 337 in anchor.py                                                                     |

---

## Requirements Coverage

| Requirement | Source Plans      | Description                                                                                                                                        | Status     | Evidence                                                                                                                     |
|-------------|-------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|------------|------------------------------------------------------------------------------------------------------------------------------|
| PREFS-01    | 06-01, 06-02, 06-05 | Preferences persisted to `~/.nuke/paste_hidden_prefs.json` with keys: `plugin_enabled`, `link_classes_paste_mode`, `custom_colors`; file created on first run | SATISFIED | `save()` called in `_load()` file-absent branch (line 52); all three keys in `json.dump`; 3 tests pass confirming first-run creation |
| PREFS-02    | 06-01             | On first run with no prefs file, existing `paste_hidden_user_palette.json` colors migrate; old file never written again                            | SATISFIED  | `_migrate_from_old_palette()` reads only; `save()` call materializes new file with migrated colors; test_file_created_on_first_run_with_old_palette passes |
| PREFS-03    | 06-03, 06-04      | When plugin disabled, `copy_hidden()`, `cut_hidden()`, `paste_hidden()` fall through to Nuke default; anchor/label functions return immediately    | SATISFIED  | 3 clipboard gates + 6 anchor gates + 3 label gates all present in code                                                       |
| PREFS-04    | 06-03             | When `link_classes_paste_mode` is `passthrough`, copying LINK_CLASSES node produces plain Nuke copy — no anchor creation, no FQNN stamp            | SATISFIED  | `continue` at lines 48-49 of paste_hidden.py skips all stamping; node still included in `nuke.nodeCopy()` at end            |

No orphaned requirements: all four PREFS IDs claimed by plans and verified in code.

---

## Anti-Patterns Found

| File        | Line | Pattern      | Severity | Impact                                                                          |
|-------------|------|--------------|----------|---------------------------------------------------------------------------------|
| `colors.py` | 87   | comment references `prefs.custom_colors` | INFO | Docstring only — no import; legitimate documentation of caller convention |
| `paste_hidden.py` | 155 | word "placeholders" | INFO | Appears in a code comment describing cross-script paste behaviour — not a stub |

No blocker or warning-level anti-patterns found.

---

## Human Verification Required

### 1. Prefs file created on first Nuke launch

**Test:** Delete `~/.nuke/paste_hidden_prefs.json`, launch Nuke, load the plugin, then quit. Open the file.
**Expected:** File exists with `plugin_enabled: true`, `link_classes_paste_mode: "create_link"`, `custom_colors: []`.
**Why human:** Requires a live Nuke session to exercise the import-time `_load()` path.

### 2. Migration from old palette file

**Test:** Delete `~/.nuke/paste_hidden_prefs.json`, ensure `~/.nuke/paste_hidden_user_palette.json` contains color values, launch Nuke.
**Expected:** `paste_hidden_prefs.json` created and contains those colors in `custom_colors`; old palette file is unmodified.
**Why human:** Requires a live Nuke session; migration runs at import time.

### 3. plugin_enabled=False disables Ctrl+C/X/V plugin behavior

**Test:** Set `plugin_enabled` to `false` in prefs file, launch Nuke, copy a Read node (Ctrl+C), paste (Ctrl+V).
**Expected:** Pasted node is a plain Read node — no hidden knob, no FQNN stamp.
**Why human:** Requires a live Nuke session to inspect pasted node knobs.

### 4. passthrough mode copies Read/Camera plain

**Test:** Set `link_classes_paste_mode` to `"passthrough"` in prefs file, launch Nuke, copy a Read node, paste.
**Expected:** Pasted Read node has no `copy_hidden_input_node` knob.
**Why human:** Requires a live Nuke session to inspect pasted node knobs.

### 5. Menu items grey out when plugin_enabled=False

**Test:** Set `plugin_enabled` to `false` in prefs file, launch Nuke, open Edit > Anchors menu.
**Expected:** All gated items (Create Anchor, Rename Anchor, etc.) are greyed out; Copy (old), Cut (old), Paste (old) remain active.
**Why human:** Visual menu state cannot be verified programmatically; depends on Nuke 13+ `setEnabled` support.

---

## Gaps Summary

No gaps remain. The UAT gap (Test 1: prefs file not created on first run) is closed:

- `prefs.py` line 52: `save()` now called in `_load()` file-absent branch immediately after `_migrate_from_old_palette()`
- `save()` docstring updated to document automatic first-run invocation
- `tests/test_prefs.py` added with 3 tests — all pass: `Ran 3 tests in 0.002s OK`
- UAT Test 2 (legacy migration) inherits the fix automatically — migration path now also materializes the file

All four PREFS requirements satisfied. Phase goal achieved.

---

_Verified: 2026-03-11_
_Verifier: Claude (gsd-verifier)_
