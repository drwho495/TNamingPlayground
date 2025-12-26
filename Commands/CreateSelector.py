import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Features import Selector

class CreateSelector:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "Extrusion.svg"),
            'MenuText': "Create Selector Feature",
            'ToolTip': "Creates a new Selector feature"
        }
        
    def Activated(self):
        if FreeCAD.GuiUp == True:
            Selector.makeSelector()
            
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('CreateSelector', CreateSelector())