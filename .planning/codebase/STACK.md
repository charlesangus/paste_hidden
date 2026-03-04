# Technology Stack

**Analysis Date:** 2026-03-03

## Languages

**Primary:**
- Python 2.7+ / 3.x - Core plugin scripting language for all functionality

## Runtime

**Environment:**
- Nuke (Foundry) - Proprietary VFX compositing software with embedded Python interpreter
- Nuke 14+ - Minimum supported version (version detection for PySide2/PySide6 available in code)
- Nuke 16+ - Supports PySide6 (newer Qt bindings)

**Package Manager:**
- Python built-in modules only - No external package manager configuration (requirements.txt, pyproject.toml, setup.py, or poetry.lock found)
- Dependencies installed via Nuke's bundled environment

## Frameworks

**Core:**
- nuke - Foundry Nuke Python API - Core compositing engine and node manipulation
- nukescripts - Nuke scripting utilities (menu management, selection, clipboard handling)

**UI:**
- PySide2 / PySide6 (conditional) - Qt bindings for GUI components
  - Nuke 16+: PySide6 (newer)
  - Nuke <16: PySide2 (legacy)
  - Selection via version detection: `nuke.NUKE_VERSION_MAJOR >= 16`

**Utilities:**
- tabtabtab (v2.0) - Fuzzy-search command palette framework
  - Embedded in codebase: `tabtabtab.py`
  - Custom plugin system for anchor/link selection
  - Weights persistence via JSON

## Key Dependencies

**Critical:**
- nuke - Nuke Python API for node manipulation, knob access, DAG traversal
- nukescripts - Essential for clipboard management (`cut_paste_file()`), selection clearing, menu integration
- PySide2/PySide6 - GUI widgets for anchor picker and navigator dialogs (gracefully disabled if unavailable)

**Built-in:**
- os - File path operations (basename, expanduser)
- re - String sanitization for anchor names
- json - Weights file persistence in tabtabtab

## Configuration

**Environment:**
- Nuke init.py integration: `nuke.pluginAddPath('paste_hidden')` in user's top-level init.py
- Menu system: Automatically loaded by `menu.py` via Nuke's plugin mechanism

**Build:**
- No build process - Pure Python plugin
- No external build tools required

## Platform Requirements

**Development:**
- Nuke 14+ installation
- Python 2.7+ (for Nuke 14-15) or Python 3.x (for Nuke 16+)
- PySide2 or PySide6 available in Nuke's bundled Qt installation

**Production:**
- Deployed as plugin in Nuke's `.nuke` directory
- Requires Nuke 14+ with nuke Python API enabled
- No additional runtime dependencies beyond Nuke's standard libraries

## Installation

**Deployment:**
- Copy entire `paste_hidden` directory to user's `~/.nuke/` folder
- Add single line to `~/.nuke/init.py`: `nuke.pluginAddPath('paste_hidden')`
- menu.py auto-loads remaining modules on Nuke startup

---

*Stack analysis: 2026-03-03*
