import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Objects import Dressup

class CreateFillet:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "Icons", "Fillet.png"),
            'MenuText': "Create Fillet Feature",
            'ToolTip': "Creates a new Fillet feature"
        }
        
    def Activated(self):
        if FreeCAD.GuiUp == True:
            Dressup.makeDressup(Dressup.DressupType.FILLET)
            
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('CreateFillet', CreateFillet())