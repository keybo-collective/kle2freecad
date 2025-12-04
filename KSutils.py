# -*- coding: utf-8 -*-

import os
import inspect
import FreeCAD

_dir = os.path.abspath(inspect.getfile(inspect.currentframe()))
modulePath = os.path.dirname(_dir)
iconPath = os.path.join(modulePath, "Icons")

def isGuiLoaded():
    """Check if the FreeCAD GUI is loaded."""
    if hasattr(FreeCAD, "GuiUp"):
        return FreeCAD.GuiUp
    return False
