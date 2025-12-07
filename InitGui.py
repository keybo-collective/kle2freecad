# -*- coding: utf-8 -*-

import inspect, os, sys
import FreeCAD, FreeCADGui

class KSWorkbench (FreeCADGui.Workbench):
    """FreeCAD Workbench for the KLE Plate Generator"""
    from KSutils import iconPath
    from KSprefs import KSprefsPage

    MenuText = "KLE Plate Generator"
    ToolTip = "Convert KLE output to a sketch"
    Icon = os.path.join(iconPath, "kle2sketch.svg")

    def Initialize(self):
        """This function is executed when the workbench is first activated.
        It is executed once in a FreeCAD session followed by the Activated function.
        """
        import KLESketch  # registers commands

        self.list = ["KLESketchGenerator"]
        self.appendToolbar("KLE Plate Generator", self.list)
        self.appendMenu("KLE Plate Generator", self.list)

        # Ensure the icon directory is on the search path
        FreeCADGui.addIconPath(self.iconPath)

        FreeCADGui.addPreferencePage(self.KSprefsPage, "KLE Plate Generator")

    def Activated(self):
        """This function is executed whenever the workbench is activated"""
        return

    def Deactivated(self):
        """This function is executed whenever the workbench is deactivated"""
        return

    def ContextMenu(self, recipient):
        """This function is executed whenever the user right-clicks on screen"""
        # "recipient" will be either "view" or "tree"
        # self.appendContextMenu("My commands", self.list) # add commands to the context menu

    def GetClassName(self):
        # This function is mandatory if this is a full Python workbench
        # This is not a template, the returned string should be exactly "Gui::PythonWorkbench"
        return "Gui::PythonWorkbench"

FreeCADGui.addWorkbench(KSWorkbench())
