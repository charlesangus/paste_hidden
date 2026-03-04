# External Integrations

**Analysis Date:** 2026-03-03

## APIs & External Services

**Not Applicable:**
- No external API integrations detected
- No network calls or remote service dependencies
- All functionality is local to Nuke scripts

## Data Storage

**Databases:**
- Not applicable - No database connections

**File Storage:**
- Local filesystem only
- Weights persistence for tabtabtab fuzzy-search picker: `~/.nuke/paste_hidden_anchor_weights.json` and `~/.nuke/paste_hidden_anchor_navigate_weights.json`
  - Location: `anchor.py` lines 309, 413
  - Format: JSON
  - Purpose: Stores user's frecency/selection history for anchor picker

**Caching:**
- No explicit caching layer
- tabtabtab widget persistence: Global variables `_anchor_picker_widget` and `_anchor_navigate_widget` maintain picker state during session

## Authentication & Identity

**Not Applicable:**
- No authentication system
- No identity management
- Operates within Nuke's user context

## Monitoring & Observability

**Error Tracking:**
- Not applicable - No error tracking integration

**Logs:**
- Console output via Nuke's script editor
- No structured logging or log aggregation

## CI/CD & Deployment

**Hosting:**
- Not applicable - Desktop plugin only
- Deployed directly to user's Nuke installation

**CI Pipeline:**
- Not applicable - No CI/CD configured

## Environment Configuration

**Required env vars:**
- None - All configuration is Nuke-native or file-based

**Secrets location:**
- Not applicable - No secrets or credentials stored

## Webhooks & Callbacks

**Incoming:**
- No incoming webhooks

**Outgoing:**
- No outgoing webhooks or callbacks to external services

## Internal Event System

**Nuke Callbacks:**
- Custom knob callbacks registered via PyScript_Knob:
  - `reconnect_anchor_knob`: `anchor.reconnect_anchor_node(nuke.thisNode())` - Line 76-78 in `anchor.py`
  - `rename_anchor_knob`: `anchor.rename_anchor(nuke.thisNode())` - Line 85-87 in `anchor.py`
  - `link_reconnect_knob`: `link.reconnect_link_node(nuke.thisNode())` - Line 101-103 in `link.py`

**Menu System Integration:**
- Replaces Nuke built-in copy/cut/paste via `nuke.menu("Nuke").findItem("Edit")`
- Custom menu hierarchy: `Edit > Anchors > [submenus]`
- Keyboard shortcuts:
  - Ctrl+C, Ctrl+X, Ctrl+V - Modified copy/cut/paste
  - A - Anchor shortcut (context-aware)
  - Alt+A - Anchor find/navigate
  - Shift+M - Label (Large)
  - Shift+N - Label (Medium)
  - Ctrl+M - Append Label
  - Shift+Ctrl+D - Paste (old style)

## File I/O

**Input:**
- Nuke script files (.nk) - Read via `nuke.root()`, node graph traversal
- Clipboard via Nuke's `nukescripts.cut_paste_file()` - Temporary file location managed by Nuke

**Output:**
- Nuke script modifications - Direct node property manipulation via nuke API
- Weights files - JSON serialization to `~/.nuke/paste_hidden_*.json`

---

*Integration audit: 2026-03-03*
