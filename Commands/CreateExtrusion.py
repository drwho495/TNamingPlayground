import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Objects import Extrusion

class CreateExtrusion:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "Icons", "Extrusion.png"),
            'MenuText': "Create Extrusion Feature",
            'ToolTip': "Creates a new Extrusion feature"
        }
        
    def Activated(self):
        Extrusion.makeExtrusion()
        
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('CreateExtrusion', CreateExtrusion())