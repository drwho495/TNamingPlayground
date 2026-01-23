import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Features import TThickness

class CreateTThickness:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "Extrusion.svg"),
            'MenuText': "Create TThickness Feature",
            'ToolTip': "Creates a new TThickness feature"
        }
        
    def Activated(self):
        if FreeCAD.GuiUp == True:
            TThickness.makeThickness()
            
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('CreateTThickness', CreateTThickness())