import nuke
import paste_hidden
import anchor
import labels

menu = nuke.menu("Nuke")
edit_menu = menu.findItem("Edit")

menu.addCommand("Edit/Copy",  "paste_hidden.copy_hidden()",  "^C")
menu.addCommand("Edit/Cut",   "paste_hidden.cut_hidden()",   "^X")
menu.addCommand("Edit/Paste", "paste_hidden.paste_hidden()", "^V")

def _find_item_index(parent_menu, item_name):
    for position, menu_item in enumerate(parent_menu.items()):
        if menu_item.name() == item_name:
            return position
    return -1

paste_index = _find_item_index(edit_menu, "Paste")
edit_menu.addCommand(
    "Paste Multiple",
    "paste_hidden.paste_multiple_hidden()",
    index=paste_index + 1,
)

anchors_menu = edit_menu.addMenu("Anchors")

anchors_menu.addCommand("Create Anchor",       "anchor.create_anchor()")
anchors_menu.addCommand("Rename Anchor",       "anchor.rename_selected_anchor()")
anchors_menu.addCommand("Create Link",         "anchor.select_anchor_and_create()")
anchors_menu.addCommand("Anchor",              "anchor.anchor_shortcut()", "A")
anchors_menu.addCommand("Reconnect All Links", "anchor.reconnect_all_links()")
anchors_menu.addCommand("Anchor Find",         "anchor.select_anchor_and_navigate()", "alt+A")

anchors_menu.addSeparator()

anchors_menu.addCommand("Label (Large)",  "labels.create_large_label()",  "+M")
anchors_menu.addCommand("Label (Medium)", "labels.create_medium_label()", "+N")
anchors_menu.addCommand("Append Label",   "labels.append_to_label()",     "^M")

anchors_menu.addSeparator()

anchors_menu.addCommand("Copy (old)",  "paste_hidden.copy_old()")
anchors_menu.addCommand("Cut (old)",   "paste_hidden.cut_old()")
anchors_menu.addCommand("Paste (old)", "paste_hidden.paste_old()", "+^D")
