import os
import sys
import locater
import FreeCADGui as Gui
import FreeCAD as App
from Commands.CreateDesignBody import CreateDesignBody
from Commands.CreateThickness import CreateThickness
from Commands.CreateExtrusion import CreateExtrusion
from Commands.CreateFillet import CreateFillet
from Commands.CreateChamfer import CreateChamfer
from Commands.CreateSelector import CreateSelector
from Commands.SelectRootFeature import SelectRootFeature
from Commands.DisplayElementHistory import DisplayElementHistory

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(locater.__file__)))) # allow python to see ".."
__dirname__ = os.path.dirname(locater.__file__)

class ToponamingBench(Gui.Workbench):
    global __dirname__

    MenuText = App.Qt.translate("Workbench", "Stable Design")
    ToolTip = App.Qt.translate("Workbench", "Stable Design")

    def __init__(self):
        self.documentObserver = None

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        bodyCommands = [
            "CreateDesignBody"
        ]

        featureCommands = [
            "CreateExtrusion",
            "CreateFillet",
            "CreateChamfer",
            "CreateThickness"
        ]

        debugTools = [
            "DisplayElementHistory",
            "CreateSelector",
            "SelectRootFeature",
        ]
        
        self.appendToolbar("SD Design Body", bodyCommands)
        self.appendMenu("SD Design Body", bodyCommands)

        self.appendToolbar("SD Feature Operations", featureCommands)
        self.appendMenu("SD Feature Operations", featureCommands)

        self.appendToolbar("SD Debug Tools", debugTools)
        self.appendMenu("SD Debug Tools", debugTools)

    def Activated(self):
        pass

    def Deactivated(self):
        pass

Gui.addWorkbench(ToponamingBench())