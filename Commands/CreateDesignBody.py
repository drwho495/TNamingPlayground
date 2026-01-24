import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Objects import DesignBody

class CreateDesignBody:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "Icons", "NewBody.png"),
            'MenuText': "Create Design Body Feature",
            'ToolTip': "Creates a new Design Body feature"
        }
        
    def Activated(self):
        DesignBody.makeDesignBody()
        
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('CreateDesignBody', CreateDesignBody())