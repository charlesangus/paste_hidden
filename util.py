import nuke
import nukescripts


def upstream_ignoring_hidden(node, nodes_so_far=None):
    inputs = node.dependencies(what=nuke.INPUTS)
    if len(inputs) == 0:
        return nodes_so_far
    else:
        if nodes_so_far is None:
            nodes_so_far = set(inputs)
        else:
            nodes_so_far.update(set(inputs))
    for input_node in inputs:
        nodes_so_far.update(upstream_ignoring_hidden(input_node, nodes_so_far))
    return nodes_so_far


def select_upstream_ignoring_hidden():
    node = nuke.selectedNode()
    ns = upstream_ignoring_hidden(node)
    nukescripts.clear_selection_recursive()
    for n in ns:
        n["selected"].setValue(True)
    node["selected"].setValue(True)
