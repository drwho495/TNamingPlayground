import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Objects import Dressup

class CreateChamfer:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "Icons", "Chamfer.png"),
            'MenuText': "Create Chamfer Feature",
            'ToolTip': "Creates a new Chamfer feature"
        }
        
    def Activated(self):
        if FreeCAD.GuiUp == True:
            Dressup.makeDressup(Dressup.DressupType.CHAMFER)
            
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('CreateChamfer', CreateChamfer())