# Stack Research

**Domain:** Nuke Python plugin — CI/CD pipeline, nuke -t validation, code quality tooling
**Researched:** 2026-03-12
**Confidence:** HIGH (CI/CD and Python quality tools), MEDIUM (nuke -t license behavior in CI)

## Context: This Is a Targeted Milestone

v1.1 shipped with a validated runtime stack. This research covers only the three new
capability areas for v1.2: GitHub Actions packaging/release pipeline, nuke -t headless
validation scripting, and Python code quality tooling. The existing plugin runtime stack
(Python 3 embedded, PySide2/PySide6, JSON stdlib) is not re-evaluated.

---

## Recommended Stack

### Area 1: GitHub Actions CI/CD Pipeline

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `actions/checkout` | v4 | Repo checkout in workflow | Current stable major; v3 deprecated Jan 2025; v4 uses Node 20 |
| `softprops/action-gh-release` | v2 | Create GitHub Release and attach assets | De-facto standard for tag-triggered releases; v2 is current major (v2.5.0 latest point release); handles asset upload, draft mode, prerelease flag |
| Python stdlib `zipfile` + `os.walk` | stdlib | Create the ZIP archive | No third-party zip action needed; a `run: python3 -c` or inline script step gives full control over archive structure; no extra action pin to maintain |

**Workflow trigger:**

```yaml
on:
  push:
    tags:
      - 'v*'
```

This fires only on tag pushes matching `v*` (e.g. `v1.2.0`). The `github.ref_name` context
variable gives the bare tag name (e.g. `1.2.0`) without the `refs/tags/` prefix — use it as
the ZIP filename stem.

**ZIP packaging pattern (inline Python, no pip, no third-party action):**

```yaml
- name: Package plugin ZIP
  run: |
    python3 - <<'EOF'
    import zipfile, os, sys

    tag = os.environ["GITHUB_REF_NAME"]          # e.g. "v1.2.0"
    zip_name = f"paste_hidden-{tag}.zip"
    source_files = [
        "paste_hidden.py",
        "anchor.py",
        "clipboard.py",
        "colors.py",
        "constants.py",
        "prefs.py",
        # add menu.py / init.py if present
    ]
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in source_files:
            if os.path.exists(path):
                zf.write(path)
    print(f"Created {zip_name}")
    EOF
```

Enumerate source files explicitly — avoids accidentally bundling `tests/`, `.planning/`,
`.git/`, or dev tooling into the release artifact.

**Release step:**

```yaml
- name: Create GitHub Release
  uses: softprops/action-gh-release@v2
  with:
    files: paste_hidden-${{ github.ref_name }}.zip
    generate_release_notes: true
```

`generate_release_notes: true` auto-populates the release body from commits since the last
tag — appropriate for a single-developer project with no manual changelog management.

**Permissions required** — add to the job or workflow level:

```yaml
permissions:
  contents: write
```

`softprops/action-gh-release` needs write access to `contents` to create the release. Without
this the step fails silently on repos with default `contents: read`.

---

### Area 2: nuke -t Headless Validation Scripts

| Technology | Purpose | Notes |
|------------|---------|-------|
| `nuke -t <script.py>` | Run a Python script in Nuke's headless Python interpreter mode | Uses nuke_r (render) license; no GUI; full `nuke` Python API available |
| `nuke -ti <script.py>` | Same as -t but requests nuke_i (interactive) license instead of nuke_r | Use `-ti` if only interactive licenses are available and no render seats |
| `sys.exit(1)` in script | Signal failure back to the CI runner or shell | Nuke propagates non-zero sys.exit as process exit code; CI picks this up |

**Key behaviors of `nuke -t`:**

- Starts Nuke in terminal/Python interpreter mode — no DAG, no panels, no GUI license
- The full `nuke` Python module is importable; all node/knob APIs are available
- `sys.argv` receives any arguments placed after the script path on the command line
- Arguments after `-t scriptname.py` are passed through to `sys.argv[1:]`
- Frame range args are the exception: `-F 1001` before the script name is consumed by Nuke
  itself, not passed to the script

**Syntax:**

```bash
# Basic: run a Python script headlessly
Nuke14.0 -t /path/to/validation_script.py

# With arguments to the script
Nuke14.0 -t /path/to/validation_script.py --strict

# Render license variant (default with -t)
Nuke14.0 -t script.py           # requests nuke_r

# Interactive license variant
Nuke14.0 -ti script.py          # requests nuke_i
```

**Validation script pattern for stub verification:**

```python
#!/usr/bin/env python3
"""Validate that offline stubs match real Nuke API behavior."""
import sys
import nuke

failures = []

# Example: verify knob type matches stub expectation
node = nuke.createNode("NoOp")
knob = node.knob("label")
if not isinstance(knob, nuke.String_Knob):
    failures.append(f"label knob type: expected String_Knob, got {type(knob)}")

if failures:
    for f in failures:
        print(f"FAIL: {f}", file=sys.stderr)
    sys.exit(1)

print("All validation checks passed.")
sys.exit(0)
```

**CI constraint:** Running `nuke -t` in a GitHub Actions workflow requires a licensed Nuke
installation reachable by the runner. This is not practical with standard GitHub-hosted runners
(`ubuntu-latest`). The nuke -t validation step is intended for **local developer execution**
(or a self-hosted runner with Nuke installed), not as part of the GitHub Actions workflow that
runs on push/tag. The CI workflow handles packaging and release only; nuke -t scripts are
developer tooling run manually.

**Confidence: MEDIUM** — the `-t` flag behavior and `sys.exit` exit-code propagation are
documented in Foundry's Python Developer Guide (versions 6.3 through 15.1 all consistent).
License behavior (`nuke_r` vs `nuke_i`) is confirmed via Foundry support article Q100106.
The CI impracticality of running Nuke on GitHub-hosted runners is a known constraint for
all Nuke pipeline tooling.

---

### Area 3: Python Code Quality Tooling

All tools below are **dev/CI-only**. None are added to the plugin runtime. The constraint
"no new runtime dependencies" is not affected — these are installed in the developer
environment and in GitHub Actions, not bundled with the plugin.

| Tool | Version | Purpose | Why Recommended |
|------|---------|---------|-----------------|
| `ruff` | 0.15.x (0.15.5 current as of 2026-03-12) | Linting + import sorting + code style | Single tool replaces flake8 + isort + pyupgrade; 10-100x faster than flake8; 800+ rules; zero runtime deps; first-class GitHub Actions support |
| `ruff format` | (bundled with ruff) | Code formatting check (Black-compatible) | Bundled at no extra cost; verify formatting without enforcing it (use `--check` in CI) |
| `radon` | 6.0.1 | Cyclomatic complexity analysis | McCabe complexity per function; identifies over-complex logic targeted by QUAL-01; output is human-readable and scriptable; installs in ~2s |

**Ruff rule selection for a moderate quality sweep (QUAL-01):**

```toml
# pyproject.toml or ruff.toml
[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # Pyflakes (unused imports, undefined names, dead code markers)
    "W",    # pycodestyle warnings
    "B",    # flake8-bugbear (opinionated bug-prone patterns)
    "C90",  # McCabe complexity (mccabe)
    "I",    # isort (import ordering)
    "UP",   # pyupgrade (modernize Python syntax)
    "SIM",  # flake8-simplify (unnecessary complexity patterns)
]
ignore = [
    "E501",  # line too long — handled by formatter preference, not hard error
]

[tool.ruff.lint.mccabe]
max-complexity = 10  # flag functions above complexity 10
```

`B` (bugbear) and `SIM` (simplify) are the most valuable for QUAL-01 — they catch patterns
like unnecessary `else` after `return`, redundant `bool()` wrapping, and negated conditions
that should be simplified. `F` catches dead imports and unreachable-code markers. `C90`
quantifies the over-complex logic that is the stated target.

**Radon for complexity reporting (not enforcement):**

```bash
# Report functions with cyclomatic complexity B or higher (≥6)
radon cc src/ -s -n B

# Show maintainability index per file
radon mi src/ -s
```

Use radon for the initial sweep to identify which functions to simplify. Ruff's `C90` rule
can then enforce a ceiling going forward in CI.

**GitHub Actions step:**

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'

- name: Install quality tools
  run: pip install ruff radon

- name: Lint
  run: ruff check .

- name: Format check
  run: ruff format --check .

- name: Complexity report (informational)
  run: radon cc . -s -n B
  continue-on-error: true   # report only, do not fail CI on complexity
```

Note: `radon` step uses `continue-on-error: true` during the sweep phase. Once refactoring
is complete, remove it (or replace with `xenon` for hard limits).

---

## Installation

```bash
# Developer + CI environment only — NOT bundled with plugin
pip install ruff radon

# Verify versions
ruff --version    # should be 0.15.x
radon --version   # should be 6.0.1
```

No changes to plugin files, `requirements.txt`, or Nuke's Python environment.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `ruff` | `flake8` + `isort` + `pyupgrade` separately | Never for new projects; ruff replaces all three at 10-100x speed with a single config file |
| `ruff` | `pylint` | pylint has much broader semantic analysis and cross-file inference; prefer it if you need type-inference-aware rules. For a moderate sweep (QUAL-01), ruff's speed and focused ruleset is more practical |
| `radon` for complexity reporting | `xenon` for complexity enforcement | `xenon` wraps radon and fails CI if complexity exceeds thresholds — use after sweep is complete and limits are established |
| Inline Python `zipfile` step | `TheDoctor0/zip-release` GitHub Action | Use the marketplace action if ZIP structure becomes complex (directory exclusion patterns, recursive glob filters). For a flat plugin ZIP, stdlib is simpler and has no version-pin to maintain |
| `softprops/action-gh-release@v2` | GitHub CLI (`gh release create`) in a `run:` step | `gh` CLI is pre-installed on GitHub-hosted runners and is a valid alternative; use it if you want to avoid the external action pin. Tradeoff: more shell scripting, no built-in draft-until-complete feature |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `actions/upload-artifact` for the release ZIP | Upload-artifact stores artifacts for workflow-to-workflow transfer, not for public GitHub Releases. Releases require `softprops/action-gh-release` or `gh release create` | `softprops/action-gh-release@v2` with `files:` key |
| `black` as a separate formatter | Ruff's formatter is Black-compatible and bundled; installing both is redundant and creates config conflicts | `ruff format` |
| `flake8-cognitive-complexity` | Not implemented in ruff; requires flake8 plugin system which ruff explicitly does not support | `ruff` `C90` (McCabe) + `SIM` rules cover the meaningful cases |
| Any pip install in the plugin distribution | Plugin runtime is Nuke-embedded Python with no package manager; installing anything into the plugin itself breaks the no-external-deps constraint | Keep all tooling in the dev/CI layer only |
| `nuke -t` in GitHub Actions on ubuntu-latest | No licensed Nuke installation available on GitHub-hosted runners; the step will fail at the license check before executing any Python | Run `nuke -t` validation locally or on a self-hosted runner with Nuke installed |

---

## Stack Patterns by Variant

**If running ruff in CI (tag-triggered release workflow):**
- Add a separate `quality` job that runs `ruff check` and fails on violations
- Keep the `package` job independent so a lint failure does not block release if intentionally bypassed
- Use `continue-on-error: true` on radon during the active sweep phase

**If nuke -t validation is added to a self-hosted runner:**
- Use `-t` (nuke_r license) not `-ti` if render seats are available — render licenses are cheaper
- Use `-ti` only if the studio has interactive-only licensing (common for small facilities)
- Exit code propagation: `sys.exit(1)` in the Python script causes the runner step to fail

**If repository uses `pyproject.toml` (recommended):**
- Place `[tool.ruff]` section in `pyproject.toml` alongside any existing `[tool.pytest.ini_options]`
- If no `pyproject.toml` exists, `ruff.toml` at repo root is also valid

---

## Version Compatibility

| Tool | Python 3.9 (Nuke 14) | Python 3.11 (Nuke 16) | CI (ubuntu-latest) |
|------|----------------------|----------------------|-------------------|
| ruff 0.15.x | Yes (dev env only) | Yes (dev env only) | Yes |
| radon 6.0.1 | Yes (dev env only) | Yes (dev env only) | Yes |
| actions/checkout@v4 | N/A | N/A | Yes (Node 20) |
| softprops/action-gh-release@v2 | N/A | N/A | Yes |

These tools are installed in the developer/CI Python environment, not in Nuke's embedded
Python, so Nuke's Python version is irrelevant to their operation.

---

## Sources

- [softprops/action-gh-release releases](https://github.com/softprops/action-gh-release/releases) — v2.5.0 confirmed latest; v2 major tag current (MEDIUM confidence, sourced from search results referencing GitHub releases page)
- [actions/checkout GitHub](https://github.com/actions/checkout) — v4 confirmed current stable major; v3 deprecated January 2025 (HIGH confidence)
- [actions/upload-artifact deprecation notice](https://github.blog/changelog/2024-04-16-deprecation-notice-v3-of-the-artifact-actions/) — v4 required from January 2025 (HIGH confidence)
- [Foundry Nuke Python Dev Guide — Command Line](https://learn.foundry.com/nuke/developers/15.1/pythondevguide/command_line.html) — `-t` flag behavior, `sys.argv` passing, exit code semantics (HIGH confidence — official Foundry documentation)
- [Foundry Nuke 14.1 Command Line Operations](https://learn.foundry.com/nuke/14.1v6/content/comp_environment/configuring_nuke/command_line_operations.html) — `-t` vs `-ti` license behavior (MEDIUM confidence — searched but page not directly fetched; consistent with older version docs)
- [ruff PyPI — 0.15.5](https://pypi.org/project/ruff/) — version confirmed current via search (HIGH confidence)
- [ruff rules documentation](https://docs.astral.sh/ruff/rules/) — rule categories E, F, W, B, C90, SIM confirmed (HIGH confidence — official docs)
- [radon PyPI — 6.0.1](https://pypi.org/project/radon/) — version confirmed via search (MEDIUM confidence)

---
*Stack research for: paste_hidden v1.2 — CI/CD pipeline, nuke -t validation, code quality tooling*
*Researched: 2026-03-12*
