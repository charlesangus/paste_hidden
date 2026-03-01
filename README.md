# Paste Hidden

Replacement and improvement for the Copy/Cut/Paste functions in Foundry's Nuke.

- "Input Nodes" (e.g. Read, Camera, ReadGeo, DeepRead) will be replaced by a hidden input-ed PostageStamp/NoOp when copied/pasted. This prevents multiplying input nodes, which is a bad practice which makes script maintenance difficult. Inputs should exist exactly one time in the script.
- Makes working with hidden inputs easier, by re-piping the hidden input of a copy/pasted PostageStamp/NoOp/Dot.
- Handles colorizing and labelling hidden input-ed PostageStamp/NoOp/Dot nodes.
- "Old-style" paste (without the secret sauce) is available with `Ctrl-Shift-D`.

# Installation

Copy the `paste_hidden` folder into your `~/.nuke` folder and add this line to your top-level `init.py`:

`nuke.pluginAddPath('paste_hidden')`

The included `menu.py` will handle replacing the built-in copy/paste functions.

# Why

I am a firm believer that it is impossible to have an organized script without hidden inputs for any but the most trivial scripts. However, working with hidden inputs is painful. Unlike a Read node, which stays pointing at the same file sequence when you copy-paste it, a hidden input must be re-piped every time it's pasted. This is pointless busy-work, as the cases where we do and do not want a hidden input re-piped are well-defined and consistent:

```If the parent node is not in the selection, AND the parent node is at the "same level" as the pasted node (i.e. at the Root level or in the same Group node) AND in the same script, AND the node in question is a valid class to have hidden inputs (i.e. PostageStamp/NoOp/Dot), re-pipe.```

If the parent node is in the selection, the parent and child will be pasted together with their inputs intact, so we don't need to re-pipe. Nuke handles this automatically, as it does all inputs where both nodes are pasted together.

If the parent node is not at the same level, re-piping cannot occur. Nuke (unlike e.g. Houdini) cannot connect nodes that do not exist at the same level.

If the parent node is not in the same script, re-piping cannot occur. Nuke cannot connect nodes across scripts (LiveGroups aside).

I am a firm believer that the ONLY nodes that should ever have hidden inputs are PostageStamps/NoOps/Dots. These nodes have exactly one input, and serve as "placeholders" for the input that has been hidden, providing a visual reference of the connection's existence. Without this visual reference of the hidden input, the script becomes immediately confusing.

# How

There are no callbacks. Everything is handled by over-riding the builtin copy-paste functions. Hidden knobs are added to relevant nodes as copying is conducted, and the magic happens at paste time. If you re-pipe nodes yourself, labels etc. will not update as nothing is live.

If you would like to customize the behaviour, look at the top of the script. This contains two variables which control which nodes are treated as "Hidden input nodes", and which nodes are replaced by "Hidden input nodes". So e.g. you could add `Constant` nodes to the list that gets replaced, and set them to be replaced by `PostageStamp` nodes. It does not make sense to replace nodes which have inputs, so please don't try it. Only replace nodes with no inputs.

# Bonus

Also includes multiple pasting, because it's handy, and other multiple paste solutions won't have the Paste Hidden secret sauce that handles the re-piping etc.

# Python API

The following functions are stable entry points for tools and scripts that want to integrate with paste_hidden programmatically.

## Anchors (`import anchor`)

### Querying

```python
anchor.all_anchors() -> list[nuke.Node]
```
Returns all anchor nodes in the current script, sorted alphabetically by display name.

```python
anchor.find_anchor_by_name(display_name: str) -> nuke.Node | None
```
Looks up an anchor by its display name (the label shown in the node graph). Returns `None` if not found.

```python
anchor.get_links_for_anchor(anchor_node: nuke.Node) -> list[nuke.Node]
```
Returns all link nodes in the current script that reference the given anchor node. Useful for impact analysis before renaming or deleting an anchor.

---

### Creating anchors

```python
anchor.create_anchor_named(name: str, input_node: nuke.Node | None = None) -> nuke.Node
```
Creates an anchor with the given name. Positions it below `input_node` and wires it up if provided. Returns the new anchor node.
Raises `ValueError` if `name` sanitizes to an empty string (i.e. contains no alphanumeric characters or underscores).

```python
anchor.create_anchor_silent(input_node: nuke.Node | None = None) -> nuke.Node
```
Creates an anchor using the auto-suggested name derived from the input node's file path and surrounding backdrop. Falls back to the node's name, then to `"Anchor"` if no suggestion can be derived. Returns the new anchor node.

```python
anchor.create_anchor()
```
Prompts the user for a name (pre-filled with the auto-suggestion) and creates the anchor. Intended for interactive use via keybind or menu.

---

### Creating links

```python
anchor.create_from_anchor(anchor_node: nuke.Node) -> nuke.Node
```
Creates a link node wired to the given anchor node and returns it. The link node class (PostageStamp, NoOp, Dot) is chosen based on the anchor's input.

```python
anchor.create_link_for_anchor_named(display_name: str) -> nuke.Node
```
Looks up the anchor by display name, creates a link node wired to it, and returns the link node.
Raises `ValueError` if no anchor with that display name exists.

```python
anchor.try_create_link_for_anchor_named(display_name: str) -> nuke.Node | None
```
Same as above but returns `None` instead of raising if the anchor is not found.

---

### Renaming

```python
anchor.rename_anchor_to(anchor_node: nuke.Node, name: str)
```
Renames the anchor to `name` and updates the stored reference and label on all link nodes that point to it.
Raises `ValueError` if `name` sanitizes to an empty string.

```python
anchor.rename_anchor(anchor_node: nuke.Node)
```
Prompts the user for a new name (pre-filled with a suggestion) and renames the anchor. Intended for interactive use.

---

### Reconnecting

```python
anchor.reconnect_anchor_node(anchor_node: nuke.Node)
```
Re-wires all link nodes that reference the given anchor. Useful after loading or merging scripts.

```python
anchor.reconnect_all_links()
```
Re-wires every link node in the current script.

---

## Copy / Paste (`import paste_hidden`)

These are drop-in replacements for Nuke's built-in copy/cut/paste. They are wired to `Ctrl+C/X/V` by `menu.py` automatically on installation. You only need to call them directly if you are building your own menu or keybind setup.

```python
paste_hidden.copy_hidden()
paste_hidden.cut_hidden()
paste_hidden.paste_hidden() -> nuke.Node   # returns last pasted node, same as nuke.nodePaste()
paste_hidden.paste_multiple_hidden()
```

The "old-style" equivalents (no anchor/link magic) are also available as `copy_old()`, `cut_old()`, and `paste_old()`.
