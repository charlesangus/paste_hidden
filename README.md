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
