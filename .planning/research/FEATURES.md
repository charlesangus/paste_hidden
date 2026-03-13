# Feature Research

**Domain:** Nuke Python plugin — v1.2 Hardening milestone (CI/CD, stub validation, code quality, cross-script paste bugs)
**Researched:** 2026-03-12
**Confidence:** HIGH (CI/CD patterns), MEDIUM (nuke -t headless limits), HIGH (code quality tooling), HIGH (cross-script paste bugs — code read directly)

---

## Context

This is a subsequent milestone on a shipped single-artist plugin. "Table stakes" and "differentiators"
are framed relative to a hardening release, not a greenfield product. Features are the six active
items from PROJECT.md v1.2: CI-01, CI-02, BUG-01, BUG-02, QUAL-01, TEST-01/02/03.

---

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Tag-triggered GitHub Release with ZIP | Standard delivery for VFX plugins — artist downloads zip, drops into ~/.nuke | LOW | `softprops/action-gh-release@v2` on `push: tags: v*.*.*` trigger; ZIP built excluding tests/, .planning/, __pycache__ |
| Release body / changelog | Reviewable history at download time; answers "what changed in this version?" | LOW | `generate_release_notes: true` auto-pulls from merged PRs/commits; or `body_path` pointing to a CHANGELOG section |
| Correct tile_color on cross-script NoOp link paste (BUG-01) | Anchor color conveys semantic ownership — default purple on a reconnected link breaks visual consistency across scripts | LOW | Bug in paste_hidden.py line 212: `node['tile_color'].setValue(ANCHOR_DEFAULT_COLOR)` overwrites the correct color that `setup_link_node(destination_anchor, node)` just set one line earlier. Fix: remove that line. |
| Anchor pasted cross-script stays an anchor (BUG-02) | Pasting an anchor should seed it in the destination — silently converting it to a link is wrong | MEDIUM | Bug in paste_hidden.py Path A/C: when an anchor NoOp is pasted cross-script and `find_anchor_by_name()` finds a same-named anchor in the destination, the code deletes the pasted node and creates a link. Anchors should not follow this path; only explicit link nodes and LINK_SOURCE_CLASSES should. Fix: skip link-creation when `is_anchor(node)` is true in the cross-script branch. |
| Test suite runs cleanly via flat discovery (TEST-03) | Discovery failures (`python3 -m unittest discover`) erode CI output trust and hide real failures | MEDIUM | Cause: Qt stub modules installed into sys.modules by one test file leak into subsequently-loaded files. Fix patterns: `setUpModule`/`tearDownModule` with sys.modules cleanup, or per-test mock.patch on sys.modules entries. |

### Differentiators (Valuable, Not Assumed)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| nuke -t validation scripts (TEST-01/02) | Confirms stub behavior matches real Nuke API — detects mock drift before tests silently validate wrong behavior | MEDIUM | Manual developer step only (no CI license). Scripts exercise each StubNode/StubKnob method against real nuke.Node/nuke.Knob. Output: printed pass/fail per method under test. |
| Moderate code quality sweep (QUAL-01) | Reduces future maintenance cost; improves readability without altering plugin behavior | MEDIUM | Highest-value targets: dead code (vulture), unused imports (ruff F401), overly broad exception handlers, comments restating obvious code. No API breaks, no new runtime deps. |
| Auto-generated release notes from commits | Zero-ceremony changelog — PR titles and commit messages appear in the GitHub Release body automatically | LOW | `generate_release_notes: true` in softprops action. Requires commit message discipline going forward. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| nuke -t validation in CI pipeline | "Run everything in CI automatically" | Nuke requires a commercial license to execute any Python API. GitHub Actions runners have no Nuke license and cannot acquire one; the job fails at license checkout before any test runs. | Keep nuke -t scripts as a manual developer tool run against a local licensed install. Document the workflow in a comment in the validation script itself. |
| Automated dead-code removal without review | vulture/deadcode output piped straight to deletion | False positives on plugin entry points registered in menu.py or called by Nuke callbacks via string name — they appear unused statically but are live. Blind removal breaks the plugin. | Use vulture output as a human-review checklist. `vulture --make-whitelist` for known false positives. |
| ruff --fix on the entire codebase in one pass | Fast, appeals as a one-shot cleanup | Auto-fix rewrites can change semantics (exception chain simplification, comprehension rewrites). In a plugin with no type annotations, some rewrites reduce clarity. Batch application makes the diff hard to review. | Run `ruff check` only first. Review findings by category. Apply fixes file-by-file with manual verification. |
| python-semantic-release for version automation | Automatic version bumping, industry practice for packages | Heavyweight dependency and opinionated commit-message format for a single-developer plugin. Adds pyproject.toml complexity for no practical gain. | Manual `git tag v1.2.0 && git push origin v1.2.0`. The CI workflow reads `github.ref_name` for the release name. |
| PyPI publication step in CI | "Publish like a real package" | This plugin has no PyPI audience. It is a ~/.nuke-dropped directory plugin, not an importable package. PyPI publication would require setup.py/pyproject.toml restructuring with no benefit to the single user. | GitHub Release ZIP is the correct and sufficient distribution artifact. |
| Parallel test isolation via subprocess-per-test-file | Cleanly solves Qt stub ordering | Extreme complexity for a 100-test suite; subprocess invocations add CI time and configuration overhead. | Fix stub ordering at the module level with setUpModule/tearDownModule sys.modules cleanup — simpler and sufficient. |

---

## Feature Dependencies

```
[GitHub Actions workflow]
    └──requires──> [git tag convention matching v*.*.*]
    └──produces──> [Release ZIP + GitHub Release]

[Release ZIP]
    └──requires──> [clean source tree / no __pycache__ or test files in ZIP]

[nuke -t validation scripts]
    └──requires──> [licensed local Nuke install — NOT on CI]
    └──validates──> [StubNode/StubKnob behavior in tests/]
    └──informs──> [stub corrections in test files if mock drift found]

[Code quality sweep (QUAL-01)]
    └──uses──> [vulture (dead code) + ruff (style/imports)]
    └──informs──> [BUG-01 and BUG-02 fixes] (reading paste_hidden.py during sweep surfaces both bugs)
    └──must not break──> [existing public API: functions referenced in menu.py or by name in node knobs]

[BUG-01 fix]
    └──located in──> [paste_hidden.py Path B cross-script branch, line 212]
    └──isolated from──> [BUG-02 fix] (different code paths)

[BUG-02 fix]
    └──located in──> [paste_hidden.py Path A/C, lines 156-171]
    └──must not break──> [XSCRIPT-01 working behavior: link nodes still reconnect cross-script]

[TEST-03 fix]
    └──located in──> [tests/ sys.modules stub installation in each test file]
    └──independent of──> [BUG-01, BUG-02] (test infrastructure only)
```

### Dependency Notes

- **CI workflow requires tag convention:** The `on: push: tags: v*.*.*` trigger must match the developer's tagging convention. `v1.2.0` matches; `1.2.0` does not. Must be documented.
- **nuke -t validation is one-directional:** If validation finds drift, fixes land in tests/ (stub definitions), not in production code. The production API is the ground truth.
- **BUG-02 fix must preserve XSCRIPT-01:** The existing working behavior where a NoOp *link* pasted cross-script reconnects to a same-named anchor in the destination must not regress. The fix must distinguish `is_anchor(node)` from `is_link(node)`.

---

## v1.2 Milestone Scope (replaces generic MVP section)

### Ship to close v1.2

- [ ] GitHub Actions CI/CD: tag-triggered ZIP packaging + GitHub Release (CI-01, CI-02)
- [ ] BUG-01: NoOp links pasted cross-script receive anchor tile_color, not default purple
- [ ] BUG-02: Anchor pasted cross-script stays an anchor (not converted to a link)
- [ ] Moderate code quality sweep: dead code removed, complex logic simplified, no API breaks (QUAL-01)
- [ ] nuke -t validation scripts written and run manually against licensed local Nuke (TEST-01, TEST-02)
- [ ] TEST-03: flat-discovery Qt stub ordering conflicts resolved

### Defer to v2+

- [ ] Full forward/back navigation history stack (NAV-03)
- [ ] Manual tile_color changes propagate to links (COLOR-V2-01) — out of scope by design

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| BUG-01 tile_color fix | HIGH (visual regression, visible on every cross-script link paste) | LOW (remove one line) | P1 |
| BUG-02 anchor cross-script fix | HIGH (behavioral regression, silent wrong semantics) | MEDIUM (conditional in Path A/C) | P1 |
| TEST-03 flat-discovery fix | MEDIUM (CI integrity, developer trust in suite) | MEDIUM (sys.modules isolation) | P1 |
| GitHub Actions CI/CD ZIP release | MEDIUM (packaging convenience) | LOW (~30 lines YAML) | P1 |
| Code quality sweep | MEDIUM (maintainability, reduces future debt) | MEDIUM (tool-assisted + human review) | P2 |
| nuke -t validation scripts | LOW-MEDIUM (one-time confidence check, not recurring CI) | MEDIUM (write scripts, run manually, interpret results) | P2 |

**Priority key:** P1 = required for v1.2 close. P2 = value-adds within milestone scope.

---

## nuke -t Headless Validation: Capability Map

### What CAN be tested headlessly with `nuke -t` (MEDIUM confidence)

- Node creation: `nuke.createNode()`, `nuke.nodes.NoOp()`, etc.
- Knob read/write: `node['knob'].value()`, `.setValue()`, `.getText()`, `.setText()`
- Node graph traversal: `nuke.allNodes()`, `node.input(0)`, `node.setInput()`
- Custom knob addition: `node.addKnob()`, `knob_name in node.knobs()`
- Script I/O: `nuke.scriptOpen()`, `nuke.scriptSave()`, `nuke.root()`
- `nuke.toNode(name)` lookup
- `nuke.env['gui']` returns `False` — can gate UI code on this
- `nuke.execute()` for rendering (requires valid read/write inputs — not needed for stub validation)
- `nuke.root().name()` returns the script filename stem

### What CANNOT be tested headlessly with `nuke -t`

- Any Qt/PySide2/PySide6 UI: dialogs, panels, widgets — Qt event loop does not run
- `nuke.message()`, `nuke.ask()`, `nuke.getInput()` — blocking GUI dialogs, will fail or hang
- `nuke.executeInMainThread()` — no GUI main thread running
- `nuke.toNode("preferences")` NodeColourSlot knob access — preferences node may not initialise correctly in headless (depends on Nuke version; avoid relying on this in validation scripts)
- DAG/viewport operations: `nuke.zoom()`, `nuke.center()` — no DAG panel
- `nuke.getColor()` — launches a modal color picker GUI

### What the validation scripts should cover

Goal: confirm each StubNode/StubKnob method in `tests/` faithfully mimics real `nuke.Node`/`nuke.Knob` behavior for operations the test suite depends on.

Key behaviors to validate against real Nuke:
1. `node['knob'].value()` returns set value (not a MagicMock side-effect)
2. `node['knob'].setValue(x)` followed by `.value()` round-trips correctly
3. `node.knobs()` returns a dict-keyed structure with knob name as key
4. `node.addKnob(knob)` makes `knob.name() in node.knobs()` true
5. `node.Class()` returns class string
6. `node.name()` / `node.setName()` round-trip
7. `nuke.root().name()` returns filename stem (e.g. `"untitled"` for unsaved)
8. `nuke.allNodes()` returns list of current-context nodes
9. `nuke.toNode(name)` returns node or None
10. `node.input(0)` / `node.setInput(0, other)` connectivity
11. `knob.getText()` / `knob.setText()` for String_Knob (separate from `value()`/`setValue()`)

### Critical constraint: license required, CI is off-limits

Nuke requires a commercial floating license (or Nuke Non-Commercial) to run any Python API call.
GitHub Actions runners have no Nuke license. Therefore:

- nuke -t validation is a **manual developer step only**
- The `.github/workflows/` YAML must NOT include any `nuke -t` or `nuke --tg` step
- The CI workflow contains only: offline Python unittest (stub-based), ZIP build, release upload

---

## Cross-Script Paste Color Propagation: Bug Analysis

### BUG-01: NoOp links get wrong tile_color on cross-script paste

**Location in code:** `paste_hidden.py`, Path B cross-script branch, approximately lines 203-214

**Root cause:** After `setup_link_node(destination_anchor, node)` correctly sets `tile_color` from the destination anchor (via `find_node_color(destination_anchor)` in `link.py:162`), the very next line unconditionally resets it:

```
setup_link_node(destination_anchor, node)   # sets correct anchor color
node['tile_color'].setValue(ANCHOR_DEFAULT_COLOR)  # BUG: overwrites with purple
```

The purple override was originally placed here to canonicalize Dot link tile color at copy time. In the paste cross-script path it is incorrect — the correct color from the destination anchor was just set.

**Fix:** Remove the `node['tile_color'].setValue(ANCHOR_DEFAULT_COLOR)` line in the cross-script Link Dot branch. `setup_link_node` already handles color propagation correctly.

**Risk:** LOW. `ANCHOR_DEFAULT_COLOR` (purple) is never the right value post-reconnect when a destination anchor exists. The same-script path does not have this line.

### BUG-02: Anchor pasted cross-script becomes a link node

**Location in code:** `paste_hidden.py`, Path A/C, approximately lines 147-180

**Root cause:** When a NoOp anchor is pasted cross-script, `is_anchor(node)` is true. `find_anchor_node()` returns None (FQNN belongs to a different script). The code then calls `find_anchor_by_name(display_name)`. If a same-named anchor exists in the destination, the pasted anchor node is deleted and a new link node is created pointing at the destination anchor.

This is correct behavior for **link nodes** (which should reconnect). It is wrong for **anchor nodes** (which should be planted as independent anchors in the destination).

**Fix:** In the cross-script block inside the `is_anchor(node)` branch, skip the `find_anchor_by_name` → create-link path. Instead: leave the pasted anchor in place, update its FQNN knob to reflect the current script stem, and continue. The pasted anchor becomes a fresh anchor in the destination.

**Must preserve:** XSCRIPT-01 behavior — a NoOp *link* pasted cross-script (which satisfies `is_link(node)`, not `is_anchor(node)`) must still reconnect to a same-named anchor. `is_anchor()` and `is_link()` are mutually exclusive predicates; the fix does not touch the link path.

**Risk:** MEDIUM. The change alters semantics for a cross-script paste case. The existing test for XSCRIPT-01 in `test_cross_script_paste.py` provides the regression guard.

---

## GitHub Actions Release Pipeline: Standard Patterns

### Minimal correct workflow structure

```yaml
on:
  push:
    tags:
      - "v*.*.*"

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build ZIP
        run: |
          mkdir -p dist
          zip -r dist/paste_hidden-${{ github.ref_name }}.zip \
            *.py LICENSE README.md \
            --exclude "__pycache__/*" "*.pyc" "tests/*" ".planning/*"
      - uses: softprops/action-gh-release@v2
        with:
          files: dist/paste_hidden-*.zip
          generate_release_notes: true
```

**Key decisions:**
- `softprops/action-gh-release@v2` is current; `actions/create-release` is deprecated and should not be used
- `github.ref_name` gives the tag name without additional extraction steps
- Exclude `tests/`, `.planning/`, `__pycache__`, `.pyc` from the artist-facing ZIP
- `generate_release_notes: true` pulls from PR titles and merged commit messages automatically

### What "done" looks like for CI-01/CI-02

After implementation, `git tag v1.2.0 && git push origin v1.2.0` triggers:
1. Actions workflow activates on the tag push
2. ZIP built containing all `.py` source files, LICENSE, README (no test/planning content)
3. GitHub Release created at that tag with ZIP attached
4. Release notes auto-generated from commits since last tag
5. Artist downloads ZIP from the Releases page, drops into ~/.nuke

---

## Code Quality Sweep: Scope and Tooling

### Most valuable at moderate scope (ordered by ROI)

1. **Dead code removal** — unused functions, unreachable conditional branches, imports never referenced. Use `vulture . --min-confidence 80`. Human review required before deletion (entry points registered via `menu.py` string references are false positives).
2. **Overly complex conditionals** — nested if/elif chains that can be flattened or extracted to named predicates. Read the code; tools do not catch this reliably.
3. **Exception scope tightening** — bare `except Exception: pass` clauses that swallow errors silently. Either handle the specific exception or re-raise.
4. **Redundant comments** — comments that restate what the code obviously does. Remove them; keep comments explaining *why*.
5. **Import hygiene** — unused imports. `ruff check --select F401` catches these reliably and fast.

### What to avoid at moderate scope (no API breaks constraint)

- Renaming public API symbols (functions called by name in node knob PyScript callbacks, e.g. `link.reconnect_link_node`)
- Changing function signatures (callers in `menu.py` pass positional arguments)
- Reformatting entire files with ruff format / black (creates noisy diffs obscuring logical changes)
- Adding type annotations (out of scope for a hardening milestone)

### Tooling recommendation

- `vulture .` — dead code detection; output is a review checklist, not a deletion script. Confidence: HIGH for what it finds; always human-review before removing.
- `ruff check . --select F,E,W` — unused imports (F401), undefined names (F821), basic style violations. Fast and low-noise. No runtime dependency introduced.
- Neither tool requires installation into the plugin itself; both are dev-only.

---

## Sources

- [softprops/action-gh-release — GitHub](https://github.com/softprops/action-gh-release) — release action inputs and tag trigger pattern (HIGH confidence)
- [NUKE Python Developers Guide — Command Line](https://learn.foundry.com/nuke/developers/63/pythondevguide/command_line.html) — `nuke -t` capabilities (MEDIUM confidence — older version, behavior stable)
- [Foundry Nuke Python API Reference 14.0](https://learn.foundry.com/nuke/developers/140/pythonreference/basics.html) — `nuke.env['gui']`, node/knob API (HIGH confidence)
- [vulture — Find dead Python code](https://github.com/jendrikseipp/vulture) — dead code detection (HIGH confidence)
- [ruff — Python linter](https://github.com/astral-sh/ruff) — style and unused-import checks (HIGH confidence)
- Code read directly: `/workspace/paste_hidden.py` lines 147-214, `/workspace/link.py` lines 160-174 — bug analysis (HIGH confidence, primary source)
- Code read directly: `/workspace/tests/test_cross_script_paste.py`, `/workspace/tests/test_anchor_color_system.py` — stub pattern and test infrastructure (HIGH confidence)

---

*Feature research for: paste_hidden v1.2 Hardening milestone*
*Researched: 2026-03-12*
