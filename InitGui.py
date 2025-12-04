# -*- coding: utf-8 -*-

import os
import sys
import inspect
import FreeCAD
import FreeCADGui

class KSWorkbench (FreeCADGui.Workbench):
    from KSutils import iconPath

    MenuText = "KLE to Sketch"
    ToolTip = "Convert KLE output to a sketch"
    Icon = os.path.join(iconPath, "kle2sketch.svg")

    def Initialize(self):
        """This function is executed when the workbench is first activated.
        It is executed once in a FreeCAD session followed by the Activated function.
        """
        # # Ensure the icon directory is on the search path
        # FreeCADGui.addIconPath(iconPath)

        import KLESketch  # registers commands

        self.list = ["KLESketchGenerator"]
        self.appendToolbar("KLE Transform", self.list)
        self.appendMenu("KLE Transform", self.list)

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
