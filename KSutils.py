# -*- coding: utf-8 -*-

import os, inspect
import FreeCAD

_file = globals().get("__file__") or os.path.abspath(inspect.getfile(inspect.currentframe()))
_dir = os.path.dirname(_file)
iconPath = os.path.join(_dir, "Icons")
prefFileName = os.path.join(_dir, "KSprefs.ui")

# ----------------------------------------------------------------------------

def isGuiLoaded():
    """Check if the FreeCAD GUI is loaded."""
    if hasattr(FreeCAD, "GuiUp"):
        return FreeCAD.GuiUp
    return False
