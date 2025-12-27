import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Features import TDressup

class CreateTDressup:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "Extrusion.svg"),
            'MenuText': "Create TDressup Feature",
            'ToolTip': "Creates a new TDressup feature"
        }
        
    def Activated(self):
        if FreeCAD.GuiUp == True:
            TDressup.makeDressup()
            
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('CreateTDressup', CreateTDressup())