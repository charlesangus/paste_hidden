import nuke
import paste_hidden

menu = nuke.menu("Nuke")
menu.addCommand("Edit/Copy", "paste_hidden.copy_hidden()", "^C")
menu.addCommand("Edit/Cut", "paste_hidden.cut_hidden()", "^X")
menu.addCommand("Edit/Paste", "paste_hidden.paste_hidden()", "^V")
menu.addCommand("Edit/Paste Multiple", "paste_hidden.paste_multiple_hidden()", "+^V")

menu.addCommand("Edit/Copy (old)", "paste_hidden.copy_old()")
menu.addCommand("Edit/Cut (old)", "paste_hidden.cut_old()")
menu.addCommand("Edit/Paste (old)", "paste_hidden.paste_old()", "+^D")
