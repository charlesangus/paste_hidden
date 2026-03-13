# Architecture Research

**Domain:** Nuke plugin — CI/CD, nuke -t validation, quality sweep (v1.2)
**Researched:** 2026-03-12
**Confidence:** HIGH — existing codebase inspected directly; GitHub Actions patterns verified against official documentation and widely-used actions (softprops/action-gh-release v2)

---

## System Overview

### Existing Plugin Architecture (unchanged by v1.2)

```
paste_hidden/ (repo root)
├── paste_hidden.py    # copy/cut/paste replacements
├── anchor.py          # anchor creation, renaming, navigation, tabtabtab plugins
├── link.py            # FQNN utilities, is_anchor/is_link predicates, link setup
├── colors.py          # ColorPaletteDialog, swatch palette helpers
├── prefs.py           # Prefs singleton, PrefsDialog, get_prefs()
├── labels.py          # label application and propagation helpers
├── constants.py       # all magic strings, class maps, PREFS_PATH, colors
├── menu.py            # Nuke menu registration and keyboard shortcut binding
├── tabtabtab.py       # fuzzy-search picker widget framework (700+ LOC)
├── util.py            # DAG traversal utilities
└── tests/             # offline unit tests with StubNode/StubKnob pattern
    ├── __init__.py
    ├── test_anchor_color_system.py
    ├── test_anchor_navigation.py
    ├── test_cross_script_paste.py
    ├── test_dot_anchor_name_sync.py
    ├── test_dot_type_distinction.py
    └── test_prefs.py
```

### New Files Added by v1.2

```
paste_hidden/ (repo root)
├── ... (all existing files unchanged except bug fixes and quality sweep)
├── tests/
│   └── ... (existing tests; may gain new tests for BUG-01/BUG-02 fixes)
└── validation/                          # NEW — nuke -t validation scripts
    ├── validate_stub_alignment.py       # compares stub behavior vs real Nuke API
    └── validate_cross_script_paste.py   # real-Nuke smoke test for BUG-01/BUG-02

.github/                                 # NEW — GitHub Actions
└── workflows/
    └── release.yml                      # tag-triggered: run tests, ZIP, publish release
```

No source-module files are added. All v1.2 changes are in:
- Existing source modules (bug fixes, quality sweep — no new files)
- New `validation/` directory (nuke -t scripts, separate from unit `tests/`)
- New `.github/workflows/` directory (CI/CD)

---

## Component Responsibilities

| Component | Responsibility | v1.2 Status |
|-----------|---------------|-------------|
| `paste_hidden.py` | copy/cut/paste logic; cross-script paste reconnect | Modified — BUG-01/BUG-02 fixes |
| `anchor.py` | anchor creation, navigation, tabtabtab integration | Modified — quality sweep only |
| `link.py` | FQNN, predicates, link setup | Modified — quality sweep only |
| `colors.py` | color picker dialog | Unchanged or quality sweep only |
| `prefs.py` | preferences singleton and dialog | Unchanged or quality sweep only |
| `labels.py` | label helpers | Unchanged or quality sweep only |
| `constants.py` | all constants | Unchanged or quality sweep only |
| `menu.py` | Nuke menu registration | Unchanged |
| `tabtabtab.py` | fuzzy picker framework | Unchanged |
| `util.py` | DAG traversal | Unchanged |
| `tests/` | offline unit tests (StubNode/StubKnob pattern) | May gain tests for bug fixes |
| `validation/` | nuke -t validation scripts requiring real Nuke runtime | NEW |
| `.github/workflows/release.yml` | tag-triggered CI/CD pipeline | NEW |

---

## Recommended Project Structure (v1.2 target)

```
paste_hidden/
├── anchor.py
├── colors.py
├── constants.py
├── labels.py
├── link.py
├── menu.py
├── paste_hidden.py
├── prefs.py
├── tabtabtab.py
├── util.py
│
├── tests/                              # offline unit tests — no Nuke runtime needed
│   ├── __init__.py
│   ├── test_anchor_color_system.py
│   ├── test_anchor_navigation.py
│   ├── test_cross_script_paste.py      # gains tests for BUG-01/BUG-02 cross-script color
│   ├── test_dot_anchor_name_sync.py
│   ├── test_dot_type_distinction.py
│   └── test_prefs.py
│
├── validation/                         # nuke -t scripts — requires real Nuke license
│   ├── validate_stub_alignment.py      # compares StubNode/StubKnob vs real nuke API
│   └── validate_cross_script_paste.py  # smoke test for cross-script paste BUG-01/BUG-02
│
├── .github/
│   └── workflows/
│       └── release.yml                 # CI/CD: test → zip → release
│
├── .gitignore
├── LICENSE
└── README.md
```

### Structure Rationale

- **`tests/` vs `validation/`:** Two distinct test categories with incompatible runtimes. `tests/` runs anywhere Python 3 is available — no Nuke license needed, driven by unittest/pytest with `StubNode/StubKnob` mocks. `validation/` requires a live Nuke installation and `nuke -t` invocation; these cannot run in CI (no Nuke license available in GitHub Actions runners). Keeping them in separate directories makes the distinction explicit and prevents the CI workflow from accidentally attempting to run validation scripts.
- **`.github/workflows/`:** Mandatory location; GitHub scans this path automatically. Only one workflow file is needed for v1.2 (release.yml). A second workflow for push-triggered linting is optional and out of scope.
- **No `src/` layout:** The plugin loads via `nuke.pluginAddPath('paste_hidden')`, which puts the repo root on `sys.path`. Introducing a `src/` layout would break the Nuke load path. The flat structure is correct for this plugin type.

---

## GitHub Actions Workflow Architecture

### Trigger Model

The workflow triggers exclusively on tag push matching `v*`. It does NOT run on every push to main. This is the correct pattern for a single-artist tool with no continuous integration requirements beyond "tests pass before release."

```yaml
on:
  push:
    tags:
      - "v*"
```

### Workflow Stages

```
git push --tags v1.2.0
    |
    v
[GitHub Actions: release.yml triggered]
    |
    +-- Job: build-and-release
        |
        +-- Step 1: Checkout (actions/checkout@v4)
        |       fetches full history for release notes generation
        |
        +-- Step 2: Set up Python (actions/setup-python@v5)
        |       python-version: "3.11"  # matches Nuke 16 runtime
        |
        +-- Step 3: Run offline tests
        |       python -m pytest tests/ -v
        |       fails fast — ZIP not created if tests fail
        |
        +-- Step 4: Build ZIP artifact
        |       shell: bash
        |       creates dist/paste_hidden_v1.2.0.zip
        |       includes: *.py (source), README.md, LICENSE
        |       excludes: tests/, validation/, .github/, .planning/,
        |                 __pycache__/, *.pyc, .gitignore, .pytest_cache/
        |
        +-- Step 5: Publish GitHub Release
                softprops/action-gh-release@v2
                files: dist/paste_hidden_*.zip
                generate_release_notes: true
                GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### ZIP Contents — Include/Exclude Manifest

The ZIP is the user-installable plugin artifact. The artist drops it into their Nuke plugin path and imports from it. Only files needed at runtime are included.

**Include:**
```
anchor.py
colors.py
constants.py
labels.py
link.py
menu.py
paste_hidden.py
prefs.py
tabtabtab.py
util.py
README.md
LICENSE
```

**Exclude (never ship):**
```
tests/          # offline test infrastructure; no value to end user
validation/     # requires Nuke license; not user-facing
.github/        # CI config; not user-facing
.planning/      # GSD planning docs; not user-facing
__pycache__/    # bytecode cache; Python regenerates on import
*.pyc           # compiled bytecode; platform-specific
.gitignore      # VCS metadata
.pytest_cache/  # pytest internal cache
```

**Implementation approach:** Use an explicit shell `zip` command with exclusion flags rather than a separate manifest file. This keeps the exclude list in one place (the workflow YAML) and avoids introducing a `MANIFEST.in` or `pyproject.toml` that would misleadingly imply this is a PyPI-style package.

```bash
# Step 4 implementation pattern
VERSION="${GITHUB_REF_NAME}"
mkdir -p dist
zip -r "dist/paste_hidden_${VERSION}.zip" \
    anchor.py colors.py constants.py labels.py link.py \
    menu.py paste_hidden.py prefs.py tabtabtab.py util.py \
    README.md LICENSE
```

This is explicit (no glob surprises) and easy to update when source files are added or removed.

### Release Notes Generation

Use `generate_release_notes: true` in `softprops/action-gh-release@v2`. This calls GitHub's built-in release notes API, which generates notes from commits and PRs between the previous tag and the new tag. No separate changelog action is needed for a single-artist project.

The release notes body structure is optionally controlled by `.github/release.yml` (label-based categorization). For v1.2 this is unnecessary overhead — accept the GitHub default format.

**Confidence:** MEDIUM — `generate_release_notes` is a documented feature of `softprops/action-gh-release@v2` and GitHub's release API, but behavior depends on commit message format. This project does not use Conventional Commits, so categorization will be minimal. The notes will still be a usable list of commits between tags.

---

## Validation Script Architecture (nuke -t)

### What validation/ is for

The `tests/` directory tests behavior that can be mocked: FQNN logic, paste path branching, prefs serialization, stub knob manipulation. These tests run in CI without Nuke.

The `validation/` directory confirms that the `StubNode/StubKnob` assumptions in `tests/` match real Nuke API behavior. These scripts run manually by the developer with a real Nuke installation. They are NOT run in CI.

### Validation Script Structure

Each validation script is a standalone Python file that runs under `nuke -t`:

```
nuke -t validation/validate_stub_alignment.py
nuke -t validation/validate_cross_script_paste.py
```

A validation script follows this pattern:

```python
"""validate_stub_alignment.py — run with: nuke -t validation/validate_stub_alignment.py

Confirms that StubNode/StubKnob in tests/ match real nuke API contract.
Exit code 0 = pass, 1 = failures found.
"""

import sys
import nuke

failures = []

# --- Validate StubKnob.getText() matches real knob API ---
node = nuke.createNode('NoOp')
knob = node.knobs().get('name')
if not hasattr(knob, 'getText'):
    failures.append("Real knob missing getText() — StubKnob has it, nuke doesn't")
# ... more checks ...

if failures:
    for failure in failures:
        print(f"FAIL: {failure}")
    sys.exit(1)

print(f"PASS: all {len(checks)} checks passed")
sys.exit(0)
```

### Validation Script Placement Decision

Validation scripts go in `validation/` (not `tests/`), for these reasons:

1. **Runtime incompatibility:** `tests/` scripts are designed to run without Nuke. Adding a nuke-runtime-required script to `tests/` would cause it to be discovered by `pytest tests/` and fail in CI with an import error.
2. **Intent separation:** Unit tests verify correctness of logic. Validation scripts verify that mock assumptions about the Nuke API hold. These are different activities with different owners (CI vs manual).
3. **No discovery risk:** `pytest` discovers files matching `test_*.py`. Files in `validation/` are not auto-discovered unless explicitly included. No `conftest.py` is needed in `validation/`.

### Fixing the Flat-Discovery Qt Stub Ordering Problem (TEST-03)

The known issue is that `python3 -m unittest discover` across all test files in `tests/` produces 4–8 errors due to Qt stub ordering conflicts — test files that install incompatible `sys.modules` stubs interfere with each other when discovered and run in sequence.

Each test file currently installs its own Qt stubs at module level (e.g., `sys.modules['PySide6'] = _pyside6_stub`). When test discovery imports multiple files in sequence, the first file's stubs pollute `sys.modules` for subsequent files that expect a different stub configuration.

**Fix approach:** The fix belongs in `tests/` itself, not in `validation/`. Two options exist:

Option A — `conftest.py` with shared stubs (pytest): Create `tests/conftest.py` that installs a single authoritative set of Qt and tabtabtab stubs before any test file is imported. Individual test files stop installing their own stubs. This requires all tests to use pytest rather than unittest discover.

Option B — Per-file stub isolation (unittest): Each test file saves and restores `sys.modules` state around its module-level stub installation using `setUp`/`tearDown` at the class level or a module-level fixture. More defensive but more verbose.

Option A is recommended — the project already has a `.pytest_cache/` directory indicating pytest is in use. A `conftest.py` is the idiomatic pytest solution.

---

## Data Flow

### CI/CD Release Flow

```
Developer: git tag v1.2.0 && git push origin v1.2.0
    |
    v
GitHub Actions triggers release.yml
    |
    +-- actions/checkout@v4
    |   (full clone with tags for release notes generation)
    |
    +-- actions/setup-python@v5, python 3.11
    |
    +-- pytest tests/ -v
    |   StubNode/StubKnob mocks, no Nuke license needed
    |   EXIT 1 on any failure → workflow aborts, no release published
    |
    +-- zip command (shell)
    |   reads source .py files from repo root
    |   writes dist/paste_hidden_v1.2.0.zip
    |
    +-- softprops/action-gh-release@v2
        GITHUB_TOKEN from Actions built-in secret
        upload: dist/paste_hidden_v1.2.0.zip
        generate_release_notes: true
        → GitHub Release created with ZIP as downloadable asset
```

### Validation Flow (manual, not CI)

```
Developer: nuke -t validation/validate_stub_alignment.py
    |
    v
Nuke starts in terminal mode (-t flag)
    |
    +-- validation script imports nuke (real Nuke SDK)
    |
    +-- compares real nuke API behavior against StubNode/StubKnob assumptions
    |
    +-- prints PASS/FAIL per check
    |
    +-- sys.exit(0) if all pass, sys.exit(1) if any fail
    |
    v
Developer interprets output manually
    → if FAIL: update StubNode/StubKnob in tests/ to match real API
    → re-run tests/ to confirm fix did not break offline tests
```

---

## Architectural Patterns

### Pattern 1: Offline Tests vs Runtime Validation — Strict Separation

**What:** Two directories with incompatible runtime requirements. `tests/` = no Nuke required. `validation/` = Nuke required. They never share infrastructure.

**When to use:** Always. Any script that requires a real Nuke license belongs in `validation/`, not `tests/`. Any script that can mock Nuke belongs in `tests/`.

**Trade-offs:** Developers must remember to run `validation/` manually after stub changes. There is no automated check that stubs remain aligned. This is acceptable for a single-artist tool — the cost of misaligned stubs is a test failure that looks correct but isn't, which is caught at UAT time.

### Pattern 2: Explicit ZIP Manifest in Workflow YAML

**What:** The list of files included in the release ZIP is an explicit list of filenames in the workflow step, not a glob pattern or a separate manifest file.

**When to use:** When the project has no `pyproject.toml` or `setup.py` (this project does not package for PyPI). An explicit list is transparent and requires no tooling knowledge to understand.

**Trade-offs:** Adding a new source file requires manually updating the workflow YAML. This is intentional — new files should be consciously included in the release. A glob like `*.py` would include test files accidentally if they were ever moved to the root.

### Pattern 3: Single Job Workflow (no separate test job)

**What:** Test, build ZIP, and publish release all run in a single job in sequence. No separate `test` job with matrix or artifact sharing.

**When to use:** Single-platform plugin with one supported Python version. No reason to fan out.

**Trade-offs:** If tests fail, the job fails before reaching the release step — this is correct behavior. A multi-job structure would add complexity with no benefit for this project.

### Pattern 4: `generate_release_notes: true` over Changelog Action

**What:** Use GitHub's built-in release notes generation (`softprops/action-gh-release@v2` with `generate_release_notes: true`) rather than a separate changelog action or conventional commits tooling.

**When to use:** When commit messages are not structured (no Conventional Commits convention), when the team is one person, and when the release cadence is low. The built-in generator produces a list of commits with links — sufficient for a single-artist tool.

**Trade-offs:** Notes are not categorized (no "Features / Bug Fixes / etc." sections). Acceptable here. If commit messages later adopt Conventional Commits, the `requarks/changelog-action` or `release-changelog-builder` can replace it with no structural changes to the workflow.

---

## Anti-Patterns

### Anti-Pattern 1: Putting nuke -t scripts in tests/

**What people do:** Add `validate_*.py` scripts to `tests/` alongside unit tests.

**Why it's wrong:** `pytest tests/` discovers and runs them in CI. They import `nuke` directly (no stub). The import fails with `ModuleNotFoundError: No module named 'nuke'` — CI breaks. Even if named to avoid discovery (e.g., `validate_` prefix without `test_` prefix), `unittest discover` default pattern picks up `test_*.py` but pytest picks up more broadly with some configurations.

**Do this instead:** Put nuke -t scripts in `validation/`. They are never discovered by pytest. They are run manually by the developer with `nuke -t validation/<script>.py`.

### Anti-Pattern 2: Using glob `*.py` in the ZIP step

**What people do:** `zip paste_hidden.zip *.py` — includes every Python file in the repo root.

**Why it's wrong:** Currently there are no test files at the root, so this is safe. But if a developer ever adds a script or utility at the root, it gets silently included in the release. Explicit filename list forces a conscious decision.

**Do this instead:** List source files by name in the zip command. Ten files is a manageable list.

### Anti-Pattern 3: Triggering CI on every push to main

**What people do:** `on: push: branches: [main]` — runs tests on every commit.

**Why it's wrong for this project:** This plugin has no continuous deployment target. Running tests on every push adds noise without benefit — there is no staging environment to validate. The trigger should be tag-only. If the developer wants push-triggered linting, that belongs in a separate workflow with a fast lint-only job (no ZIP, no release).

**Do this instead:** `on: push: tags: ["v*"]` — run the full pipeline only when a release tag is pushed.

### Anti-Pattern 4: Manually updating StubNode/StubKnob without running validation/

**What people do:** Update `StubNode` or `StubKnob` in `tests/` based on assumptions about what Nuke does, without confirming with `nuke -t`.

**Why it's wrong:** The stubs are approximations. The whole point of `validation/` is to close the loop — if stubs diverge from real Nuke, tests pass but the plugin has undetected bugs. The correct sequence for any stub change is: run `validation/` first to understand real behavior, then update stubs to match, then re-run `tests/`.

**Do this instead:** Treat `validation/` as the source of truth for stub behavior. Run it before and after any stub change.

---

## Integration Points

### New File Integration with Existing Architecture

| New File | Integrates With | How |
|----------|----------------|-----|
| `.github/workflows/release.yml` | `tests/` directory | Runs `pytest tests/ -v` as a workflow step |
| `.github/workflows/release.yml` | Source `.py` files at repo root | Listed explicitly in the `zip` step |
| `.github/workflows/release.yml` | GitHub Release API | Via `softprops/action-gh-release@v2` action |
| `validation/validate_stub_alignment.py` | `tests/` StubNode/StubKnob | Compares stub API surface against real nuke API |
| `validation/validate_cross_script_paste.py` | `paste_hidden.py`, `anchor.py`, `link.py` | Imports them with real nuke available; exercises cross-script paste paths |

### External Service Integration

| Service | Integration | Notes |
|---------|-------------|-------|
| GitHub Actions | Tag push trigger | `on: push: tags: ["v*"]` |
| GitHub Releases API | `softprops/action-gh-release@v2` | Uses built-in `GITHUB_TOKEN`; no additional secret needed |
| GitHub Release Notes API | `generate_release_notes: true` | Generates notes from commits between previous and current tag |

### Module Boundaries — What v1.2 Touches vs Leaves Alone

| Module | v1.2 Change | Boundary Impact |
|--------|-------------|----------------|
| `paste_hidden.py` | BUG-01 (NoOp link color), BUG-02 (anchor vs link on cross-script paste) | Internal logic only; public function signatures unchanged |
| `anchor.py` | Quality sweep — simplify over-complex logic, remove dead code | No API changes; callers (menu.py) unchanged |
| `link.py` | Quality sweep | No API changes |
| `tests/test_cross_script_paste.py` | New tests for BUG-01/BUG-02 | Additive only; existing tests unchanged |
| `tests/conftest.py` | NEW — shared Qt/tabtabtab stubs to fix TEST-03 | Replaces per-file stub installation; reduces stub duplication |

---

## Build Order (Dependency-Ordered)

The milestone has four feature tracks. Dependencies between tracks determine sequencing.

| Step | Track | Work Item | Depends On |
|------|-------|-----------|------------|
| 1 | TEST | Fix TEST-03: create `tests/conftest.py` with shared stubs | — |
| 2 | TEST | Confirm all existing tests pass individually and via `pytest tests/` | Step 1 |
| 3 | BUG | Fix BUG-02: anchor pasted cross-script creates anchor not link | Step 2 (tests must be stable before adding new ones) |
| 4 | BUG | Fix BUG-01: NoOp links pasted cross-script receive anchor color | Step 3 (BUG-01 and BUG-02 are in the same paste code path) |
| 5 | BUG | Add offline unit tests for BUG-01 and BUG-02 fixes | Steps 3, 4 |
| 6 | QUAL | Code quality sweep: simplify over-complex logic, remove dead code | Steps 1–5 (stable test suite required before refactoring) |
| 7 | CI | Create `.github/workflows/release.yml` | Steps 1–6 (tests must pass before wiring CI) |
| 8 | CI | Verify ZIP contents — dry-run the zip command locally | Step 7 |
| 9 | TEST | Write `validation/validate_stub_alignment.py` | Step 6 (quality sweep may change stub-relevant code) |
| 10 | TEST | Write `validation/validate_cross_script_paste.py` | Steps 3–5 |
| 11 | TEST | Run validation scripts against real Nuke; update stubs if needed | Steps 9, 10 |
| 12 | ALL | Push tag v1.2.0; confirm GitHub Actions release workflow | Steps 1–11 |

**Ordering rationale:**
- TEST-03 (conftest.py) goes first because the flat-discovery bug means the test suite is unreliable. All subsequent work depends on a trustworthy test suite.
- BUG fixes before QUAL sweep — fixing bugs in unstable code, then sweeping, avoids re-sweeping code that changes during bug fix. Also ensures bug fix tests are in place before any quality-sweep refactoring touches the same functions.
- CI workflow after all source changes — the workflow file is straightforward to write once the test suite is green and the file list is finalized. Writing it last means the ZIP manifest reflects the final state of the codebase.
- Validation scripts after quality sweep — if the sweep changes stub-relevant function signatures, write the validation scripts against the final code.

**Critical path:** TEST-03 → BUG-02 → BUG-01 → tests → QUAL sweep → CI workflow → tag push.

---

## Sources

- Direct inspection: all source files in `/workspace/` and `/workspace/tests/`; `.planning/PROJECT.md`; `.planning/codebase/ARCHITECTURE.md`, `STRUCTURE.md`, `TESTING.md`, `CONCERNS.md`
- `softprops/action-gh-release` documentation: https://github.com/softprops/action-gh-release (verified via web search — v2 is current stable version; `generate_release_notes: true` is a documented feature)
- GitHub Actions `actions/checkout@v4`, `actions/setup-python@v5`: standard first-party actions with stable v4/v5 pinning (HIGH confidence)
- Foundry Nuke developer docs — `nuke -t` flag for terminal mode Python execution: https://learn.foundry.com/nuke/developers/63/pythondevguide/command_line.html (confirmed via web search)
- pytest conftest.py pattern for shared fixtures: standard pytest documentation (HIGH confidence — no web search needed)

---
*Architecture research for: paste_hidden v1.2 — CI/CD, nuke -t validation, quality sweep*
*Researched: 2026-03-12*
