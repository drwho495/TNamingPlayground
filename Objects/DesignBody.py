import sys
import os
import time

sys.path.append(os.path.dirname(__file__))

from Objects.StableDesignObject import SDObject
import Objects.ObjectUtils as ObjectUtils
import Geometry.GeometryManager as GeometryManager
from Geometry.TShape import TShape
from Data.DataEnums import *
import PerformanceTimer as PerformanceTimer
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
                            isFeatureOperation = False,
                            typeName = "DesignBody")
        
        if not obj.hasExtension("App::OriginGroupExtensionPython"):
            obj.addExtension("App::OriginGroupExtensionPython")
            obj.Origin = App.ActiveDocument.addObject("App::Origin", "Origin")
        
        if not hasattr(obj, "TipObject"):
            obj.addProperty("App::PropertyEnumeration", "TipObject")
            self.updateTipEnum(obj)
    
    def updateTipEnum(self, obj):
        tipObjList = []

        if hasattr(obj, "TipObject"):
            for subObj in obj.Group:
                if ObjectUtils.isSDFeatureOperation(subObj):
                    tipObjList.append(subObj.Name)
            
            obj.TipObject = tipObjList
        
        return tipObjList
        
    def attach(self, obj):
        super().attach(obj)

        self.updateProps(obj)

    def showFeature(self, obj, feature):
        for subObj in obj.Group:
            if subObj.Name != feature.Name and hasattr(subObj, "IsFeatureOperation") and subObj.IsFeatureOperation:
                subObj.Visibility = False

    def onDocumentRestored(self, obj):
        self.attach(obj)
    
    def onChanged(self, obj, prop):
        if prop == "Group":
            oldTipValue = obj.TipObject
            enumList = self.updateTipEnum(obj)

            if oldTipValue in enumList:
                obj.TipObject = oldTipValue
            elif len(enumList) != 0:
                obj.TipObject = enumList[-1]

    def getTipObject(self, obj):
        if obj.TipObject != "":
            tipObj = obj.Document.getObject(obj.TipObject)
            return (tipObj, obj.Group.index(tipObj))
        return (None, 0)

    def execute(self, obj):
        self.updateProps(obj)

        PerformanceTimer.GlobalTimer.removeKeys()
        startTime = time.time()
        tipObject, tipIndex = self.getTipObject(obj)

        if tipObject != None:
            for i, subObj in enumerate(obj.Group):
                if i <= tipIndex and ObjectUtils.isSDFeatureOperation(subObj) and hasattr(subObj, "Proxy") and hasattr(subObj.Proxy, "computeShape"):
                    subObj.Proxy.computeShape(subObj)
                    subObj.purgeTouched()
        
        PerformanceTimer.GlobalTimer.logKeys()
        
        App.Console.PrintLog(f"\nTotal recorded time from PerformanceTimer: {PerformanceTimer.GlobalTimer.getTotalTime()}.\n")

        PerformanceTimer.GlobalTimer.removeKeys()
        
        App.Console.PrintLog(f"Recompute time for {obj.Label} was {round((time.time() - startTime) * 1000, 1)}.\n")

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