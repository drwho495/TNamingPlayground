import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Objects import Thickness

class CreateThickness:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "Icons", "Thickness.png"),
            'MenuText': "Create Thickness Feature",
            'ToolTip': "Creates a new Thickness feature"
        }
        
    def Activated(self):
        if FreeCAD.GuiUp == True:
            Thickness.makeThickness()
            
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('CreateThickness', CreateThickness())