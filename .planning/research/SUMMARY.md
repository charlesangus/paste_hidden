# Project Research Summary

**Project:** paste_hidden v1.2 Hardening Milestone
**Domain:** Nuke Python plugin — CI/CD pipeline, cross-script paste bug fixes, code quality sweep, nuke -t stub validation
**Researched:** 2026-03-12
**Confidence:** HIGH (CI/CD, bugs, quality tooling), MEDIUM (nuke -t headless edge cases)

## Executive Summary

The v1.2 milestone is a hardening release on a shipped single-artist Nuke plugin. It is not a greenfield build: the plugin runtime stack (Python 3 embedded in Nuke, PySide2/PySide6, JSON stdlib) is stable and unchanged. The six active work items — CI-01/CI-02 (GitHub Actions packaging and release), BUG-01/BUG-02 (cross-script paste color and anchor/link semantics), QUAL-01 (code quality sweep), and TEST-01/02/03 (nuke -t validation scripts and flat-discovery fix) — have clear, well-researched implementation paths with root causes confirmed via direct codebase inspection. The recommended approach is a dependency-ordered execution: fix test infrastructure first (TEST-03), then fix the two bugs with regression tests, then sweep quality, then wire CI, then write and run nuke -t validation scripts manually.

The key constraint shaping all CI work is that Nuke requires a commercial license to run any Python API call, making nuke -t validation impractical on GitHub-hosted runners. The CI workflow handles only offline tests (stub-based), ZIP packaging, and GitHub Release publication. nuke -t validation scripts belong in a separate `validation/` directory and are run manually by the developer against a local licensed Nuke install. This is the correct architecture for any Nuke plugin project — not a compromise.

The top risks are ordering risks, not technical risks. Sweeping code quality before bugs are fixed and regression-tested can silently reintroduce BUG-01 or BUG-02. Renaming serialized knob name constants in `constants.py` breaks every existing .nk file the artist has ever saved. Pushing a release tag before merging the workflow YAML means the CI trigger never fires. All three risks have clear, low-cost prevention strategies that are primarily about phase ordering rather than technical complexity.

## Key Findings

### Recommended Stack

The CI/CD pipeline requires no new runtime dependencies. The dev and CI toolchain consists of four tools installed in the developer/CI environment only — nothing is added to the plugin or Nuke's embedded Python.

**Core technologies:**
- `softprops/action-gh-release@v2`: Create GitHub Release and upload ZIP artifact — de-facto standard, current major (v2.5.0), handles GITHUB_TOKEN permission requirements explicitly
- `actions/checkout@v4`: Repository checkout in CI workflow — current stable major; v3 deprecated January 2025
- `ruff` 0.15.x: Linting, import sorting, and formatting check — replaces flake8 + isort + pyupgrade with one tool; 10-100x faster; zero runtime deps; recommended rule set: E, F, W, B, C90, I, UP, SIM
- `radon` 6.0.1: Cyclomatic complexity reporting — identifies over-complex logic for QUAL-01; informational output only during sweep phase, not CI enforcement
- `nuke -t` flag: Nuke headless Python interpreter mode — full `nuke` API available, no GUI, requires nuke_r or nuke_i license; cannot run on GitHub-hosted runners

**Critical version and configuration requirements:**
- `actions/checkout` must be v4 (v3 deprecated January 2025)
- Workflow must declare `permissions: contents: write` at job scope or the release creation step fails with 403
- `ruff` radon step must use `continue-on-error: true` during sweep phase; remove after sweep is complete

### Expected Features

All six v1.2 items are scoped and well-understood from direct codebase inspection. Root causes for both bugs are confirmed with line-level precision.

**Must have (table stakes — P1):**
- BUG-01: NoOp links pasted cross-script receive the anchor's actual tile_color, not default purple — root cause is a single-line unconditional color override at `paste_hidden.py` ~line 212 that fires after `setup_link_node()` already set the correct color; fix is removing that line
- BUG-02: Anchor pasted cross-script stays an anchor, not converted to a link node — root cause is Path A/C missing an `is_anchor(node)` guard before the `find_anchor_by_name` → delete-and-create-link branch; fix adds that guard
- TEST-03: Flat-discovery Qt stub ordering fix — create `tests/conftest.py` with shared authoritative stubs; eliminates 4-8 spurious errors from `pytest tests/` flat discovery
- CI-01/CI-02: Tag-triggered GitHub Release with ZIP artifact — approximately 30 lines YAML; ZIP excludes tests/, validation/, .planning/, __pycache__

**Should have (differentiators — P2):**
- QUAL-01: Moderate code quality sweep — dead code (ruff F), unused imports (ruff F401), overly broad exception handlers, complex conditional chains; no API breaks, no public symbol renames
- TEST-01/02: nuke -t validation scripts for stub alignment and cross-script paste smoke test — manual developer step only; confirms stub correctness against real Nuke runtime

**Defer to v2+:**
- NAV-03: Full forward/back navigation history stack
- COLOR-V2-01: Manual tile_color changes propagating to link nodes (explicitly deferred by design)

### Architecture Approach

The v1.2 architecture adds two new directories and modifies three existing files. No new source modules are added at the plugin level. The fundamental structural principle is a strict separation between two test categories with incompatible runtimes: `tests/` (offline, stub-based, runs in CI) and `validation/` (requires live Nuke license, manual developer-only). Mixing these would either break CI or give false confidence.

**Major components:**
1. `.github/workflows/release.yml` (NEW) — tag-triggered CI: runs `pytest tests/`, builds ZIP with an explicit file-by-file manifest, publishes GitHub Release via `softprops/action-gh-release@v2`; single job, no matrix
2. `tests/conftest.py` (NEW) — shared Qt and tabtabtab stubs for all test files; replaces per-file stub installation that causes flat-discovery ordering conflicts
3. `validation/` directory (NEW) — two nuke -t scripts: `validate_stub_alignment.py` (StubNode/StubKnob vs real Nuke API) and `validate_cross_script_paste.py` (smoke test for BUG-01/BUG-02 fixed paths)
4. `paste_hidden.py` (MODIFIED) — BUG-01 fix (remove erroneous post-`setup_link_node` color override in Path B cross-script branch) and BUG-02 fix (add `is_anchor(node)` guard in Path A/C cross-script branch before link-creation path)

**Key pattern decisions:**
- Explicit ZIP file list in YAML (not glob): `*.py` glob would silently include files added to the repo root; explicit list requires a conscious decision to add new files
- Single-job workflow (not multi-job): single platform, one Python version, no reason to fan out
- `generate_release_notes: true`: zero-ceremony changelog sufficient for single-artist project; no Conventional Commits requirement

### Critical Pitfalls

1. **Serialized knob name constants renamed in quality sweep** — The string values of `KNOB_NAME`, `DOT_TYPE_KNOB_NAME`, `DOT_ANCHOR_KNOB_NAME`, `TAB_NAME`, and related constants in `constants.py` are serialized as literal strings in every .nk file the artist has ever saved. Renaming these string values breaks all existing scripts silently (Nuke discards unknown knob values on load). Prevention: annotate all serialized constants as FROZEN in `constants.py` before touching any other file during the sweep.

2. **Quality sweep reverts BUG-01 or BUG-02 fix** — The post-`setup_link_node` color assignment looks like a bug (setting color twice); the `or is_anchor(node)` clause looks like dead code. A sweep author unfamiliar with the fix rationale will remove both. Prevention: fix both bugs with regression tests before the sweep begins; both tests must be in the required-pass gate for any sweep commit touching `paste_hidden.py`.

3. **Missing `permissions: contents: write` in workflow YAML** — GitHub Actions defaults to `contents: read` since late 2021. The release creation step fails with 403 silently on some runner configurations. Prevention: include the declaration in the initial workflow template; do not rely on repo-level settings.

4. **ZIP includes dev files** — Naive `zip -r` or glob-based packaging ships tests/, .planning/, __pycache__ to end users. Prevention: use `git archive` with `.gitattributes export-ignore` entries, or an explicit file list in the zip command. The `.gitattributes` file must be committed before the release tag is pushed.

5. **nuke -t validation imports menu.py or calls Qt dialog entry points** — `menu.py` calls `nuke.menu("Nuke")` at module level; this raises `RuntimeError` in headless mode. Several anchor functions reach `QtWidgets.QDialog.Accepted` without a None guard when Qt is absent. Prevention: validation scripts must never import `menu`; must only test non-dialog function variants (`*_named()`, `*_silent()` style); must call `nuke.scriptNew()` and set a non-trivial root name before any FQNN-dependent test.

## Implications for Roadmap

Based on combined research, the critical-path ordering is: TEST-03 → BUG-02 → BUG-01 → QUAL-01 → CI-01/CI-02 → TEST-01/02. This ordering is driven by two hard constraints: every phase depends on a trustworthy test suite, and bug fixes must have regression test coverage before the quality sweep to prevent the sweep from silently reverting them.

### Phase 1: Test Infrastructure Stabilization (TEST-03)

**Rationale:** The flat-discovery Qt stub ordering bug means `pytest tests/` currently produces 4-8 spurious errors. All subsequent work depends on a reliable test suite as a feedback mechanism. This is the unblocking dependency for the entire milestone.
**Delivers:** Green `pytest tests/` run via flat discovery; `tests/conftest.py` with shared authoritative stubs; all existing tests pass individually and collectively.
**Addresses:** TEST-03
**Avoids:** Sweeping or bug-fixing against an unreliable test suite that masks real regressions.

### Phase 2: Cross-Script Paste Bug Fixes (BUG-01, BUG-02)

**Rationale:** Both bugs are in `paste_hidden.py` in adjacent code paths. Fixing them together minimizes re-read cost. BUG-02 (anchor/link semantics) must be fixed before BUG-01 (color) because BUG-01 understanding depends on which branch the code enters after BUG-02 is resolved. Regression tests for both must be written in this phase — they gate the subsequent quality sweep.
**Delivers:** Correct tile_color for cross-script link pastes (BUG-01); anchors pasted cross-script remain anchors, not converted to links (BUG-02); new tests for both in `test_cross_script_paste.py`.
**Addresses:** BUG-01, BUG-02
**Avoids:** Quality sweep reverting unfixed, untested bugs.

### Phase 3: Code Quality Sweep (QUAL-01)

**Rationale:** The test suite is stable and both bugs have regression coverage. The sweep can refactor `paste_hidden.py`, `anchor.py`, and `link.py` with confidence. The first action in this phase must be annotating all serialized knob name constants in `constants.py` as FROZEN.
**Delivers:** Dead code removed, unused imports cleaned, overly complex conditionals simplified, exception handlers tightened; no API breaks; no behavior changes; no serialized string values altered.
**Addresses:** QUAL-01
**Uses:** `ruff` (rules E, F, W, B, C90, I, SIM) and `radon` (complexity reporting); `vulture` for dead code checklist
**Avoids:** Renaming serialized knob constants; sweep reverting BUG-01/BUG-02 (regression tests are the gate); removing the `is_anchor()` legacy detection path (backward compat with pre-DOT_ANCHOR_KNOB_NAME nodes).

### Phase 4: CI/CD Pipeline (CI-01, CI-02)

**Rationale:** Written after all source-change phases so the ZIP file manifest reflects the final state of the codebase. The workflow YAML must be merged to main before any release tag is pushed.
**Delivers:** `.github/workflows/release.yml` (tag-triggered: offline tests → ZIP → GitHub Release); `.gitattributes` with export-ignore entries; verified ZIP contents (no dev files present when artifact is unzipped locally).
**Addresses:** CI-01, CI-02
**Uses:** `softprops/action-gh-release@v2`, `actions/checkout@v4`, `actions/setup-python@v5`
**Avoids:** ZIP including dev files; missing `contents: write` permission; tag pushed before workflow YAML merged; tag trigger not firing on first push.

### Phase 5: Nuke -t Validation Scripts (TEST-01, TEST-02)

**Rationale:** Written after the quality sweep because the sweep may change stub-relevant function signatures. These are manual developer-run scripts, not CI steps — they confirm that StubNode/StubKnob assumptions in `tests/` match real Nuke API behavior and provide a smoke test for the BUG-01/BUG-02 fixed paths under a real Nuke runtime.
**Delivers:** `validation/validate_stub_alignment.py` and `validation/validate_cross_script_paste.py`; developer runs both against local licensed Nuke; any stub drift corrected in `tests/`.
**Addresses:** TEST-01, TEST-02
**Avoids:** Importing menu.py in headless scripts; FQNN false negatives from missing root name setup; reaching Qt dialog code paths that crash in headless mode.

### Phase Ordering Rationale

- TEST-03 before everything: a test suite reporting 4-8 false errors provides no useful feedback and cannot serve as a regression gate.
- Bugs before sweep: a sweep author must not have to distinguish "this looks redundant" from "this is a bug fix without a test." Fixed and tested bugs survive the sweep; unfixed bugs disappear quietly under it.
- Sweep before CI: the ZIP manifest must list the final source files; writing CI first risks the manifest going stale if the sweep adds or removes files at the root.
- Validation scripts last: they confirm stub assumptions against real Nuke; if drift is found, fixes land in `tests/` (stubs), not in production code. Writing them after the sweep ensures they test the final code shape.

### Research Flags

Phases with well-documented patterns (no additional research needed):
- **Phase 1 (TEST-03):** pytest conftest.py is standard; the stub sharing pattern is fully specified in ARCHITECTURE.md.
- **Phase 2 (BUG-01/BUG-02):** Root causes confirmed via direct codebase inspection with line-level precision; fix strategies are unambiguous.
- **Phase 3 (QUAL-01):** ruff and radon tooling is mature; specific rule sets and CLI invocations provided in STACK.md.
- **Phase 4 (CI-01/CI-02):** GitHub Actions tag-trigger release is a well-established pattern; specific YAML provided in both STACK.md and ARCHITECTURE.md; test with a `v0.0.0-test` tag before the real release.

Phases that may need spot validation during execution:
- **Phase 5 (TEST-01/02):** nuke -t validation is MEDIUM confidence. License type (nuke_r vs nuke_i), `nuke.root().name()` default value in headless, and the exact Qt guard bypass behavior should be confirmed against the actual Nuke version available in the developer's environment before writing final validation scripts. The validation script templates in ARCHITECTURE.md address all known edge cases but have not been run against a real Nuke install.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | CI/CD actions verified against official GitHub docs; ruff/radon versions confirmed via PyPI; nuke -t flag behavior confirmed in Foundry developer docs (versions 6.3 through 15.1 consistent) |
| Features | HIGH | Bug root causes confirmed via direct codebase inspection (primary source, line-level); CI/CD patterns confirmed against official docs; code quality tooling well-documented |
| Architecture | HIGH | All existing source files directly inspected; GitHub Actions workflow structure verified against documentation; conftest.py pattern is standard pytest; strict tests/validation separation rationale is sound |
| Pitfalls | HIGH | All critical pitfalls derived from direct codebase analysis or official documentation; serialized knob name pitfall confirmed against Foundry NDK versioning docs; GitHub Actions permission pitfall confirmed against GitHub changelog |

**Overall confidence:** HIGH

### Gaps to Address

- **nuke -t license type (nuke_r vs nuke_i):** The correct flag depends on which license type is available in the developer's environment. Default to `-t` (nuke_r). Document the flag choice in the validation script header with a note about `-ti` as the alternative if only interactive seats are available.

- **`nuke.root().name()` default in headless — exact string:** Research indicates the default is `"Root"` (MEDIUM confidence, community sources). The validation script template includes `nuke.scriptNew()` followed by an explicit root name set as a precaution — this is the correct defense regardless of the exact default, and adds negligible overhead.

- **radon enforcement threshold after sweep:** Research recommends `continue-on-error: true` on the radon step during the sweep phase, then adding hard enforcement via `xenon` after the sweep establishes a baseline. The decision of when to switch is a Phase 3 judgment call based on the complexity numbers radon reports. Not a gap that blocks planning.

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection: `/workspace/paste_hidden.py`, `/workspace/link.py`, `/workspace/anchor.py`, `/workspace/menu.py`, `/workspace/constants.py`, `/workspace/tests/` — bug locations (line-level), stub patterns, serialized constants, Qt guard patterns confirmed
- [Foundry Nuke Python Dev Guide — Command Line](https://learn.foundry.com/nuke/developers/15.1/pythondevguide/command_line.html) — nuke -t flag, sys.exit exit code propagation
- [GitHub Docs: Controlling permissions for GITHUB_TOKEN](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/controlling-permissions-for-github_token) — contents: write requirement for release creation
- [GitHub Changelog: Control permissions for GITHUB_TOKEN (2021)](https://github.blog/changelog/2021-04-20-github-actions-control-permissions-for-github_token/) — confirmed default changed to read
- [actions/checkout GitHub](https://github.com/actions/checkout) — v4 current stable; v3 deprecated January 2025
- [ruff rules documentation](https://docs.astral.sh/ruff/rules/) — rule categories E, F, W, B, C90, SIM, I, UP confirmed
- [git-scm: git archive export-ignore](https://git-scm.com/docs/git-archive) — .gitattributes export-ignore behavior
- [Foundry NDK: Versioning — Obsolete_knob](https://learn.foundry.com/nuke/developers/63/ndkdevguide/intro/pluginversioning.html) — knob names serialized in .nk files; renames break existing scripts
- [Foundry: Q100490 — init.py vs menu.py](https://support.foundry.com/hc/en-us/articles/360003811839) — menu.py runs only in GUI mode; nuke.menu() raises RuntimeError in headless

### Secondary (MEDIUM confidence)
- [softprops/action-gh-release releases](https://github.com/softprops/action-gh-release/releases) — v2.5.0 confirmed latest point release; v2 major tag current (sourced from search results referencing GitHub releases page)
- [Foundry Nuke 14.1 Command Line Operations](https://learn.foundry.com/nuke/14.1v6/content/comp_environment/configuring_nuke/command_line_operations.html) — -t vs -ti license behavior (page not directly fetched; consistent with older version docs)
- [radon PyPI — 6.0.1](https://pypi.org/project/radon/) — version confirmed via search
- Community: `nuke.root().name()` returns "Root" for unsaved/headless sessions — corroborated by Foundry community posts referencing `if nuke.root().name() == "Root"` pattern

---
*Research completed: 2026-03-12*
*Ready for roadmap: yes*
