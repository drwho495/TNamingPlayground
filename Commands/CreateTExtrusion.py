import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Features import TExtrusion

class CreateTExtrusion:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "Extrusion.svg"),
            'MenuText': "Create TExtrusion Feature",
            'ToolTip': "Creates a new TExtrusion feature"
        }
        
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if not doc:
            doc = FreeCAD.newDocument()
        
        # Only works if the gui is up
        if FreeCAD.GuiUp == True:
            TExtrusion.makeExtrusion()
            
        doc.recompute()
        
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('CreateTExtrusion', CreateTExtrusion())