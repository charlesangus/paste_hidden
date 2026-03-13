# Pitfalls Research

**Domain:** Adding GitHub Actions CI/CD, nuke -t validation, and code quality sweep to existing Nuke Python plugin
**Researched:** 2026-03-12
**Confidence:** HIGH — codebase directly inspected; GitHub Actions and Nuke headless behavior verified against official documentation and community sources

---

## Critical Pitfalls

### Pitfall 1: ZIP Release Accidentally Includes .planning/, tests/, and __pycache__

**What goes wrong:**
The GitHub Actions ZIP packaging step grabs everything in the repo and ships it as the release artifact. The single-artist using this plugin receives a ZIP containing `.planning/`, `tests/`, `__pycache__/`, `.github/`, `.gitattributes`, and development files. The ZIP is bigger than it should be, looks unprofessional, and could expose in-progress notes or test infrastructure.

**Why it happens:**
The naive `zip -r plugin.zip .` or `actions/upload-artifact` step includes everything present in the checkout. There is no explicit exclusion list unless one is designed upfront.

**How to avoid:**
Use `git archive` to produce the ZIP rather than `zip -r`. `git archive` respects `.gitattributes` `export-ignore` entries and automatically excludes the `.git/` directory. Add a `.gitattributes` file that marks every non-shipping path with `export-ignore`:

```
tests/               export-ignore
.planning/           export-ignore
.github/             export-ignore
.gitattributes       export-ignore
.gitignore           export-ignore
__pycache__/         export-ignore
```

The `git archive` command in the workflow becomes:
```bash
git archive --format=zip --prefix=paste_hidden/ HEAD > paste_hidden-${{ github.ref_name }}.zip
```

The `--prefix` option ensures contents land in a subdirectory inside the ZIP, which is expected for Nuke plugin installs.

**Warning signs:**
- Release ZIP size significantly larger than expected source file count
- `.planning/` or `tests/` visible when unzipping the artifact locally
- Workflow uses `zip -r` or `actions/upload-artifact` on the entire workspace directory

**Phase to address:**
CI/CD pipeline phase — define the ZIP exclusion list before writing the workflow YAML.

---

### Pitfall 2: GitHub Actions Release Step Fails Due to Missing `contents: write` Permission

**What goes wrong:**
The workflow runs `softprops/action-gh-release` or `gh release create` to publish a GitHub Release. The step fails with a 403 or "Resource not accessible by integration" error even though the workflow seems correctly configured. The tag is pushed but no release is created; the run appears green until the release step.

**Why it happens:**
GitHub Actions defaults to `contents: read` for `GITHUB_TOKEN` since late 2021. Creating a release (and uploading assets) requires `contents: write`. Many example workflows online were written before this policy change and omit the permission declaration. The error is not always surfaced clearly in the Actions UI.

Additionally, if `default_workflow_permissions` is set to "read" in the organization or repository settings, the token permissions must be explicitly declared at the workflow or job level — they do not inherit "write" from the repo settings.

**How to avoid:**
Declare permissions explicitly at the job level in the workflow YAML:

```yaml
permissions:
  contents: write
```

Do not rely on repo-level settings. Verify the permission is declared at job scope (not just workflow scope) if other jobs in the same workflow need read-only access.

**Warning signs:**
- 403 error on the release creation step
- "Resource not accessible by integration" in the Actions log
- Workflow YAML has no `permissions:` block

**Phase to address:**
CI/CD pipeline phase — include permission declaration in the initial workflow template.

---

### Pitfall 3: Tag-Triggered Workflow Does Not Fire on the First Push

**What goes wrong:**
`git push origin v1.2.0` pushes the tag, but the `on: push: tags:` workflow never triggers. The Actions tab shows no new run. This happens most often when the tag was pushed in the same command as commits (`git push --follow-tags`), when the tag was force-pushed, or when the workflow YAML was only merged to `main` after the tag was already pushed.

**Why it happens:**
GitHub Actions tag triggers require the workflow YAML to exist on the branch the tag points to. If the tag is pushed before the workflow file is committed and merged, GitHub has no workflow to run. Similarly, `GITHUB_TOKEN`-triggered events from within another workflow do not create new workflow runs (a security restriction). If the tag push originates from an Actions-internal script, the trigger is suppressed.

**How to avoid:**
Merge the workflow YAML to `main` before pushing any release tags. Tag the commit that includes the workflow file (or a later commit). Test the trigger with a `v0.0.0-test` tag before doing the real release. Never push release tags from inside another workflow job using `GITHUB_TOKEN` — if automation is needed, use a PAT.

**Warning signs:**
- No Actions run visible after `git push origin <tag>`
- Workflow YAML was added to the repo after the tag was created
- Tag is annotated vs. lightweight — both work, but confirm with a test push first

**Phase to address:**
CI/CD pipeline phase — include a test-tag validation step in the acceptance criteria before the first real release.

---

### Pitfall 4: nuke -t Imports menu.py (GUI-Only Code) and Crashes

**What goes wrong:**
The validation script run via `nuke -t validate.py` imports the plugin's `menu.py` (directly or via `~/.nuke/menu.py`). `menu.py` calls `nuke.menu("Nuke")` and `nuke.toolbar()` on module import. In headless mode (`nuke -t`), these functions raise `RuntimeError`. The validation script crashes before any business logic runs.

**Why it happens:**
Nuke only executes `menu.py` automatically in GUI sessions. But if the validation script explicitly imports `menu` — or if `init.py` sources `menu.py` unconditionally — the crash occurs. The test author may not realize `menu.py` is GUI-only code because it looks like regular Python.

This project's `menu.py` calls `nuke.menu("Nuke")` on line 7 at module level. Any `import menu` from a headless script will crash immediately.

**How to avoid:**
Never import `menu` from a `nuke -t` validation script. Import only the logic modules directly: `paste_hidden`, `anchor`, `link`, `prefs`, `constants`. If `menu.py` must be tested, guard it with `if nuke.GUI:` at the top. Keep the validation script's import list minimal and explicitly documented.

**Warning signs:**
- `RuntimeError: nuke.menu: only available in GUI mode` in `nuke -t` output
- Validation script has `import menu` anywhere
- `~/.nuke/init.py` calls `import menu` unconditionally

**Phase to address:**
nuke -t validation phase — validation script template must exclude `menu` from imports; document this constraint in the script header comment.

---

### Pitfall 5: nuke -t Validation Calls PySide2/PySide6 Without a Qt Guard

**What goes wrong:**
The validation script imports `anchor.py` or `colors.py`. These files import PySide2/PySide6 at module level inside a `try/except ImportError` block — if Qt is absent, `QtWidgets` is set to `None`. However, if the validation script exercises code paths that call `QtWidgets.QDialog.Accepted` or `dialog.exec_()` directly (without checking `if QtWidgets is None:`), it will raise `AttributeError` in headless mode because the Qt guard produced `None` globals.

Specifically, `anchor.py` line 285: `if dialog.exec_() != QtWidgets.QDialog.Accepted` — if `QtWidgets` is `None`, this crashes with `AttributeError: 'NoneType' object has no attribute 'QDialog'`.

**Why it happens:**
The author writes the validation script to exercise anchor creation logic, thinking the Qt guard handles headless gracefully. The guard sets `QtWidgets = None` but the downstream code still dereferences `QtWidgets.QDialog.Accepted` unchecked.

**How to avoid:**
In `nuke -t` validation scripts, only test code paths that do not reach any Qt call. `create_anchor_named()` is safe (it does not open a dialog). `create_anchor()` calls `ColorPaletteDialog` which is guarded with `if ColorPaletteDialog is None: return` — but this early return means `create_anchor()` does nothing in headless, making it a poor test target. Write validation scripts that test the core logic functions, not the dialog entry points. Specifically: `create_anchor_named()`, `find_anchor_by_name()`, `rename_anchor_to()`, `get_links_for_anchor()`, `paste_hidden()` with a pre-pasted clipboard file.

**Warning signs:**
- `AttributeError: 'NoneType' object has no attribute 'QDialog'` in `nuke -t` output
- Validation script calls `anchor.create_anchor()` or `anchor.rename_anchor()` directly
- Any script path that opens a dialog is included in headless validation

**Phase to address:**
nuke -t validation phase — annotate each testable function in the validation script as "dialog-free path" confirmed before adding it.

---

### Pitfall 6: nuke -t Runs Against an Unsaved (Empty) Script — FQNN Stem Is "Root"

**What goes wrong:**
The paste logic uses `nuke.root().name()` to derive the script stem for FQNN comparison. When `nuke -t` runs without loading a `.nk` file first, `nuke.root().name()` returns `"Root"` (the default node name for an unsaved session). All FQNN stems will be `"Root"` regardless of the conceptual "source" and "destination" scripts. Cross-script detection logic (`fqnn_stem != current_stem`) will always be `False`, making every paste appear same-script even for nodes stamped with a foreign FQNN.

This does not reflect real behavior, where the artist always has a named script open.

**Why it happens:**
The validation script author does not load a `.nk` file before running paste logic tests, because creating a minimal test script is extra setup effort.

**How to avoid:**
At the start of every `nuke -t` validation script, create a minimal saved script or explicitly set the root name before testing FQNN-dependent code:

```python
nuke.scriptNew()
# Provide a fake path so root().name() is non-trivial
nuke.root()['name'].setValue('/tmp/test_script.nk')
```

Alternatively, test FQNN cross-script logic exclusively through the offline Python unit tests (where the stub already controls `nuke.root().name()`), and restrict `nuke -t` validation to non-FQNN tests such as anchor creation and node graph manipulation.

**Warning signs:**
- `nuke.root().name()` returns `"Root"` in any print/debug output from the validation script
- Cross-script paste tests all pass when they should fail (false negatives)
- Validation script has no `nuke.scriptNew()` or script path setup at the top

**Phase to address:**
nuke -t validation phase — validation script template must include root name setup as step 1.

---

### Pitfall 7: Quality Sweep Renames or Removes a Knob Name Constant, Breaking Existing .nk Files

**What goes wrong:**
The code quality sweep identifies a knob name constant in `constants.py` that looks redundant or oddly named (e.g., `ANCHOR_RECONNECT_KNOB_NAME`, `DOT_TYPE_KNOB_NAME`, `DOT_ANCHOR_KNOB_NAME`) and renames it for clarity. All Python references are updated. But every existing `.nk` script the artist has ever saved contains serialized knob data stored under the old knob name as a string. When the artist opens those scripts, Nuke cannot find the knob by the old name and silently discards the value. The anchor/link knob system is now broken for all existing scripts.

**Why it happens:**
The sweep author treats knob name constants as pure Python symbols and renames them like any variable. The critical difference is that these constants are **serialized as literal strings in .nk files** — they are part of the file format, not just internal identifiers. Renaming `KNOB_NAME = 'copy_hidden_input_node'` to `KNOB_NAME = 'ph_fqnn'` changes the string literal that gets written to `.nk` files going forward, but all existing files still contain `copy_hidden_input_node`. `nuke.toNode()` and knob lookup by name will return `None` or raise `KeyError` on load.

The affected constants in this project are:
- `KNOB_NAME = 'copy_hidden_input_node'` — the critical FQNN store on every link and anchor node
- `DOT_TYPE_KNOB_NAME = 'paste_hidden_dot_type'`
- `DOT_ANCHOR_KNOB_NAME = 'paste_hidden_dot_anchor'`
- `ANCHOR_RECONNECT_KNOB_NAME = 'reconnect_child_links'`
- `ANCHOR_RENAME_KNOB_NAME = 'rename_anchor'`
- `ANCHOR_SET_COLOR_KNOB_NAME = 'set_anchor_color'`
- `TAB_NAME = 'copy_hidden_tab'`

**How to avoid:**
Mark every string constant whose value is serialized in `.nk` files as **FROZEN — do not rename**. Add a comment in `constants.py` to that effect. The quality sweep must explicitly skip these values. Only rename the Python symbols that reference these constants (e.g., renaming `KNOB_NAME` to `FQNN_KNOB_NAME` in Python code while keeping its value as `'copy_hidden_input_node'` is safe — but not worth the churn).

**Warning signs:**
- Any change to the string value of `KNOB_NAME`, `DOT_TYPE_KNOB_NAME`, `DOT_ANCHOR_KNOB_NAME`, or `TAB_NAME` in `constants.py`
- Grep for `copy_hidden_input_node` or `paste_hidden_dot_type` returns zero hits (the string was replaced)
- Tests pass but UAT with a pre-existing `.nk` script fails to reconnect links

**Phase to address:**
Code quality sweep phase — first action is to annotate all serialized-string constants as FROZEN before touching any other code.

---

### Pitfall 8: Quality Sweep Changes copy_hidden() Color Logic, Reintroducing BUG-01 (NoOp Link Gets Wrong Color)

**What goes wrong:**
BUG-01 is: NoOp links pasted cross-script receive the default purple (`ANCHOR_DEFAULT_COLOR`) instead of the anchor's actual `tile_color`. The fix requires reading the anchor's actual `tile_color` and calling `setup_link_node()` correctly in the cross-script paste path. A quality sweep that "simplifies" `paste_hidden()` — consolidating branching, extracting helpers, or reordering the color assignment in `setup_link_node()` — can silently undo the fix if the author doesn't understand why the color is set where it is.

Specifically: in `paste_hidden.py` Path B (link dot cross-script), line 211 sets `node['tile_color'].setValue(ANCHOR_DEFAULT_COLOR)` to override the color that `setup_link_node()` applied. This override is intentional for Link Dots and must survive any refactor. Similarly, in `copy_hidden()` line 79, a `node['tile_color'].setValue(ANCHOR_DEFAULT_COLOR)` override happens after `setup_link_node()` for link dots — also intentional.

**Why it happens:**
The sweep author sees `setup_link_node(destination_anchor, node)` followed immediately by `node['tile_color'].setValue(ANCHOR_DEFAULT_COLOR)` and reads it as a bug ("why set the color twice?"). They remove the second assignment as "redundant." This breaks color correctness for cross-script link dot pastes.

**How to avoid:**
Add explanatory comments above each intentional "override after setup_link_node" call, stating explicitly that `setup_link_node()` may assign the anchor's color and the override is required. The BUG-01 fix description must be referenced inline. The quality sweep phase must treat any post-`setup_link_node` color assignment as off-limits without regression testing.

**Warning signs:**
- `tile_color` assignment removed anywhere in `paste_hidden()` or `copy_hidden()` as "duplicate"
- Inline comment removed from a color override statement during a documentation cleanup sweep
- BUG-01 test case missing from the regression test run before merging the sweep

**Phase to address:**
Code quality sweep phase — BUG-01 must be fixed and have test coverage before the sweep begins, so the sweep does not accidentally undo an in-flight fix.

---

### Pitfall 9: Quality Sweep Changes `is_anchor()` or `is_link()` Logic, Breaking Backward Compatibility for Old .nk Nodes

**What goes wrong:**
`is_anchor()` in `link.py` has three detection paths: (1) name starts with `ANCHOR_PREFIX`, (2) `DOT_ANCHOR_KNOB_NAME` present, (3) legacy labelled Dot heuristic. `is_link()` checks for `KNOB_NAME` in `node.knobs()`. A quality sweep that removes the legacy heuristic from `is_anchor()` (path 3) or adds an additional strict guard breaks detection of nodes created by earlier plugin versions that lack the newer knobs.

**Why it happens:**
Path 3 in `is_anchor()` looks like dead code or over-engineering to a sweep author who only looks at nodes created by the current version. Older artist scripts may have Dot nodes created by the pre-DOT_ANCHOR_KNOB_NAME era that rely on path 3 for correct detection.

**How to avoid:**
Add a comment to the legacy detection path in `is_anchor()` noting that it exists for backward compatibility with pre-DOT_ANCHOR_KNOB_NAME nodes. The quality sweep must treat all three detection paths as intentional. Do not remove the legacy heuristic without a migration plan.

**Warning signs:**
- Any modification to `is_anchor()` that removes path 3 (the labelled Dot check)
- `is_link()` gains an additional check beyond `KNOB_NAME in node.knobs()`
- UAT tests with a pre-v1.0 script fail to recognize existing anchor nodes

**Phase to address:**
Code quality sweep phase — `is_anchor()` and `is_link()` must be explicitly marked as off-limits for behavioral changes.

---

### Pitfall 10: BUG-02 Fix (Anchor-Pasted-Cross-Script Creates Link Instead of Anchor) Reverts Under Sweep

**What goes wrong:**
BUG-02 is a regression: when a NoOp anchor node is pasted cross-script, the paste logic in `paste_hidden.py` Path A/C should create a new anchor in the destination script (or leave a placeholder), but instead creates a link node. The fix is in how `is_anchor(node)` is evaluated on a freshly-pasted node and how the cross-script branch decides between creating a link vs. creating a new anchor.

A quality sweep that "simplifies" the Path A/C logic in `paste_hidden()` — collapsing the `is_anchor(node)` check with the `node.Class() in LINK_SOURCE_CLASSES` check, or rewriting the cross-script branch — can reintroduce this regression.

**Why it happens:**
The Path A/C logic has subtle ordering: `is_anchor(node)` is checked inside `if node.Class() in LINK_SOURCE_CLASSES or is_anchor(node):`. Simplifying this compound condition or moving the anchor check changes behavior for nodes where both conditions might be ambiguously truthy.

**How to avoid:**
Fix BUG-02 before starting the quality sweep, and add a regression test that asserts an anchor pasted cross-script does not produce a link node. Run this test as a gate on any sweep changes to `paste_hidden()`.

**Warning signs:**
- The `or is_anchor(node)` clause in the paste_hidden Path A/C condition is removed or reordered
- No regression test for the cross-script anchor paste path exists before the sweep begins
- Sweep changes paste_hidden() and the BUG-02 test is not in the required-pass list

**Phase to address:**
Both the bug fix phase (write the test) and the quality sweep phase (run it as a gate).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| ZIP workflow without `.gitattributes` exclusions | Simple one-liner packaging | Ships tests/, .planning/, __pycache__ to end user; confusing artifact | Never — set up exclusions before first release |
| nuke -t validation script without nuke.scriptNew() setup | Less boilerplate | FQNN cross-script tests all give false passes | Acceptable only for tests that don't touch FQNN logic |
| Quality sweep on paste_hidden.py without BUG-01/BUG-02 fixed first | Cleaner code sooner | Sweep may undo in-flight bug fixes that aren't test-covered yet | Never — fix bugs before sweeping |
| Inline workflow ZIP step without version in filename | Simple | Release artifacts have identical names across tags; GitHub release UI confusing | Never — always include `${{ github.ref_name }}` in artifact filename |
| Removing legacy detection path 3 from is_anchor() | Simpler predicate | Old .nk files lose anchor detection; artist must manually re-mark nodes | Never — backward compat with existing scripts is a hard requirement |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| GitHub Actions + `softprops/action-gh-release` | No `permissions: contents: write` declared | Declare `permissions: contents: write` at job scope in YAML |
| `git archive` + `.gitattributes` | Commit `.gitattributes` after pushing the release tag | `.gitattributes` must be committed and on the tagged commit for `export-ignore` to take effect |
| `nuke -t` + `menu.py` | Importing or sourcing menu.py in headless validation | Never import `menu` in a `nuke -t` script; menu.py calls `nuke.menu()` at module level |
| `nuke -t` + FQNN comparison | Running paste tests without loading a script first | Call `nuke.scriptNew()` and set root name before any FQNN-dependent test |
| `nuke -t` + PySide2/PySide6 | Calling dialog entry points that reach Qt code despite `if QtWidgets is None:` early returns | Only test `*_named()` or `*_silent()` variants of functions; avoid entry points that open dialogs |
| Quality sweep + serialized knob names | Renaming the string value of `KNOB_NAME` or `DOT_TYPE_KNOB_NAME` | Never change string values of serialized constants; only rename the Python symbol if desired |
| GitHub Actions tag trigger | Pushing the tag before merging the workflow YAML | Merge workflow YAML first, then push the release tag |

---

## Performance Traps

Not applicable at the expected scale of this project (single-artist local plugin, no CI rendering, no external API calls). The only performance consideration is `nuke -t` startup time, which is fixed overhead (~5–15 seconds for license acquisition) and cannot be optimized from the plugin side.

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Release ZIP without directory prefix | Unzipping drops files into current directory with no containing folder | Use `git archive --prefix=paste_hidden/` so files land in a clean subdirectory |
| Release notes omit migration notes for BUG-01 / BUG-02 fixes | Artist re-opens old scripts expecting broken behavior to still be there, gets confused when it's fixed | Include explicit "what changed" in release notes for every bug fix |
| Quality sweep removes the "Reconnect" button knob from existing link nodes | Artist loses the manual reconnect affordance on older nodes | Any removal of UI knobs from live nodes requires a migration knob added in its place, or explicit backward-compat verification |

---

## "Looks Done But Isn't" Checklist

- [ ] **CI ZIP contents verified:** Download the release artifact and unzip it locally. Confirm `tests/`, `.planning/`, `__pycache__/`, `.github/` are absent. Confirm all `.py` source files are present.
- [ ] **Release permissions confirmed:** Deliberately remove `contents: write` from the workflow YAML, push a test tag, confirm it fails with a 403. Restore permission and confirm the real release succeeds.
- [ ] **First tag trigger test:** Push a `v0.0.0-test` tag to verify the workflow fires before doing the real `v1.2.0` tag.
- [ ] **nuke -t validation script does not import menu:** Run `grep -n 'import menu' validate*.py` — must return zero results.
- [ ] **nuke -t root name setup present:** Confirm the validation script sets a non-trivial root name before any FQNN-dependent test.
- [ ] **Serialized knob names unchanged:** Run `grep -n 'copy_hidden_input_node\|paste_hidden_dot_type\|paste_hidden_dot_anchor\|copy_hidden_tab' constants.py` — the string values must be identical to v1.1.
- [ ] **BUG-01 regression test passes after quality sweep:** The test asserting NoOp link color = anchor `tile_color` on cross-script paste must pass after every sweep commit.
- [ ] **BUG-02 regression test passes after quality sweep:** The test asserting an anchor pasted cross-script creates a link (not a duplicate anchor) must pass after every sweep commit.
- [ ] **Existing .nk script opens correctly:** Open a pre-v1.2 saved script after installing the swept codebase. Verify all anchor/link nodes are detected, reconnect buttons are present, colors are correct.
- [ ] **nuke -t validation script exits with code 0:** A non-zero exit code from `nuke -t validate.py` means a crash or assertion failure, not just a Nuke warning.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| ZIP includes .planning/ and tests/ | LOW | Add `.gitattributes` export-ignore, re-tag (delete old tag, push new), re-run release |
| Release step fails with 403 (missing permissions) | LOW | Add `permissions: contents: write` to workflow YAML, re-trigger with another tag push |
| Tag pushed before workflow YAML merged | LOW | Merge workflow YAML, delete and re-push the tag, verify trigger fires |
| nuke -t script crashes on `nuke.menu()` | LOW | Remove `import menu` from validation script; re-run |
| Quality sweep changed a serialized knob string value | HIGH | Revert the constant value change; write a one-time migration script that reads old-named knobs from existing .nk nodes and re-stamps with the new name; ship as a hotfix with explicit artist instructions |
| Quality sweep reverted BUG-01 fix | MEDIUM | Identify the specific commit, revert it, re-apply the bug fix, add the regression test to the sweep's required-pass list |
| BUG-02 regression reintroduced by sweep | MEDIUM | Revert the paste_hidden.py change, add regression test coverage before retrying sweep |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| ZIP includes dev files | CI/CD phase — .gitattributes setup | Unzip artifact locally; confirm no tests/ or .planning/ present |
| Missing `contents: write` permission | CI/CD phase — initial workflow template | Deliberately test without permission; confirm 403; restore and confirm success |
| Tag trigger not firing | CI/CD phase — acceptance criteria includes test tag push | v0.0.0-test tag pushed and workflow run confirmed before real release |
| nuke -t imports menu.py | nuke -t validation phase — import list documented in script header | grep for `import menu` in validation scripts |
| nuke -t Qt guard bypassed | nuke -t validation phase — only test non-dialog entry points | Validation script imports reviewed for any Qt-calling code paths |
| nuke -t root name not set | nuke -t validation phase — template includes root setup | Print `nuke.root().name()` at start of validation; must not be "Root" |
| Quality sweep changes serialized knob names | Code quality sweep phase — FROZEN annotation on all serialized constants | grep confirms string values unchanged from v1.1 |
| Quality sweep reverts BUG-01 color fix | Bug fix phases before sweep; regression test gating sweep | BUG-01 test in required-pass list for all sweep PRs |
| Quality sweep reverts BUG-02 anchor/link fix | Bug fix phases before sweep; regression test gating sweep | BUG-02 test in required-pass list for all sweep PRs |
| is_anchor() legacy path removed | Code quality sweep phase — explicit off-limits annotation | UAT with pre-v1.0 .nk script to verify anchor detection |

---

## Sources

- Direct codebase analysis: `/workspace/paste_hidden.py` — cross-script paste paths A/B/C, color override positions, FQNN stem comparison
- Direct codebase analysis: `/workspace/link.py` — `is_anchor()`, `is_link()`, `setup_link_node()`, knob name constants
- Direct codebase analysis: `/workspace/anchor.py` — Qt guard pattern (try/except ImportError), `QtWidgets.QDialog.Accepted` usage without None guard (line 285)
- Direct codebase analysis: `/workspace/menu.py` — `nuke.menu("Nuke")` called at module level (line 7); headless crash source
- Direct codebase analysis: `/workspace/constants.py` — all serialized knob name string values
- Direct codebase analysis: `/workspace/tests/test_cross_script_paste.py` — existing stub setup, FQNN test patterns
- [GitHub Docs: Controlling permissions for GITHUB_TOKEN](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/controlling-permissions-for-github_token) — `contents: write` required for release creation (HIGH confidence)
- [softprops/action-gh-release — permissions required](https://github.com/softprops/action-gh-release) — confirmed `contents: write` needed (HIGH confidence)
- [GitHub Changelog: Control permissions for GITHUB_TOKEN (2021)](https://github.blog/changelog/2021-04-20-github-actions-control-permissions-for-github_token/) — default changed to read (HIGH confidence)
- [Foundry: Q100490 — init.py vs menu.py](https://support.foundry.com/hc/en-us/articles/360003811839-Q100490-What-are-the-init-py-and-menu-py-files) — menu.py only runs in GUI mode; nuke.menu() raises RuntimeError headless (HIGH confidence)
- [Foundry: Using the Command-line — nuke -t](https://learn.foundry.com/nuke/developers/15.1/pythondevguide/command_line.html) — headless mode does not render/execute nodes by default (HIGH confidence)
- [git-scm: git archive export-ignore](https://git-scm.com/docs/git-archive) — .gitattributes export-ignore excludes files from archives (HIGH confidence)
- Community discussion: `nuke.root().name()` returns `"Root"` for unsaved/headless session — corroborated by Foundry community posts referencing `if nuke.root().name() == "Root"` pattern (MEDIUM confidence)
- [Foundry NDK: Versioning — Obsolete_knob for renamed knobs](https://learn.foundry.com/nuke/developers/63/ndkdevguide/intro/pluginversioning.html) — confirmed that knob names are serialized in .nk files and renames break existing scripts (HIGH confidence)

---

*Pitfalls research for: paste_hidden v1.2 — CI/CD packaging, nuke -t validation, code quality sweep, cross-script paste bug fixes*
*Researched: 2026-03-12*
