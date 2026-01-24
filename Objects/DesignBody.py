import sys
import os

sys.path.append(os.path.dirname(__file__))

from Objects.StableDesignObject import SDObject
import Objects.ObjectUtils as ObjectUtils
import Geometry.GeometryManager as GeometryManager
from Geometry.TShape import TShape
from Data.DataEnums import *
import FreeCADGui as Gui
import FreeCAD as App
import json

class DesignBody(SDObject):
    def __init__(self, obj):
        super().__init__()

        obj.Proxy = self
        self.updateProps(obj)
    
    def updateProps(self, obj):
        super().updateProps(obj,
                            implementAliasMap = False, 
                            implementShapePair = False,
                            implementBoolOpType = False,
                            implementRefine = False,
                            typeName = "DesignBody")
        
        if not obj.hasExtension("App::OriginGroupExtensionPython"):
            obj.addExtension("App::OriginGroupExtensionPython")
            obj.Origin = App.ActiveDocument.addObject("App::Origin", "Origin")
        
    def attach(self, obj):
        super().attach(obj)

        self.updateProps(obj)

    def showFeature(self, obj, feature):
        for subObj in obj.Group:
            if subObj.Name != feature.Name and hasattr(subObj, "IsFeatureOperation") and subObj.IsFeatureOperation:
                subObj.Visibility = False

    def onDocumentRestored(self, obj):
        self.attach(obj)

    def execute(self, obj):
        self.updateProps(obj)

        for subObj in obj.Group:
            if ObjectUtils.isSDFeatureOperation(subObj) and hasattr(subObj, "Proxy") and hasattr(subObj.Proxy, "computeShape"):
                subObj.Proxy.computeShape(subObj)
                subObj.purgeTouched()

class DesignBodyViewObject:
    def __init__(self, obj):
        obj.ViewObject.Proxy = self
        self.Object = obj.ViewObject
    
    def attach(self, vobj):
        self.Object = vobj
        self.updateExtensions(vobj)
    
    def updateExtensions(self, vobj):
        if vobj.Object.hasExtension("App::OriginGroupExtensionPython"):
            vobj.addExtension("Gui::ViewProviderOriginGroupExtensionPython")
    
    def onDelete(self, vobj, subelements):
        if hasattr(vobj, "Object") and hasattr(vobj.Object, "Group"):
            for obj in vobj.Object.Group:
                if ObjectUtils.isSDObject(obj):
                    vobj.Object.Document.removeObject(obj.Name)

        return True

    def setEdit(self, vobj, mode):
        if mode != 0:
            return True # fix transform setting this as the active object
        
        if Gui.ActiveDocument.ActiveView.getActiveObject("StableDesign") != vobj.Object:
            Gui.ActiveDocument.ActiveView.setActiveObject("StableDesign", vobj.Object)
            return False
        else:
            Gui.ActiveDocument.ActiveView.setActiveObject("StableDesign", None)
            return False

    def unsetEdit(self, vobj, mode):
        Gui.ActiveDocument.ActiveView.setActiveObject(vobj.Object.Name, None)
        return True

    def getIcon(self):
        return os.path.join(os.path.dirname(__file__), "..", "Icons", "Body.png")
    
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None
    
def makeDesignBody():
    obj = App.ActiveDocument.addObject("Part::FeaturePython", "DesignBody")

    DesignBody(obj)
    DesignBodyViewObject(obj)