import os
import sys
import locater
import FreeCADGui as Gui
import FreeCAD as App
from Commands.CreateTExtrusion import CreateTExtrusion
from Commands.CreateTDressup import CreateTDressup
from Commands.CreateSelector import CreateSelector
from Commands.SelectRootFeature import SelectRootFeature
from Commands.DisplayElementHistory import DisplayElementHistory

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(locater.__file__)))) # allow python to see ".."
__dirname__ = os.path.dirname(locater.__file__)

class ToponamingBench(Gui.Workbench):
    global __dirname__

    MenuText = App.Qt.translate("Workbench", "Toponaming Test Bench")
    ToolTip = App.Qt.translate("Workbench", "Toponaming Test Bench")

    commands = [
    ]
    def __init__(self):
        self.documentObserver = None

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        """
        Initialize the workbench commands
        """
        # List the commands to be added to the workbench
        featureCommands = [
            "CreateTExtrusion",
            "DisplayElementHistory",
            "CreateSelector",
            "SelectRootFeature",
            "CreateTDressup"
        ]
        
        self.appendToolbar("TNaming Features", featureCommands)
        self.appendMenu("TNaming Features", featureCommands)

    def Activated(self):
        pass

    def Deactivated(self):
        pass

Gui.addWorkbench(ToponamingBench())