import sys
import os
import json

sys.path.append(os.path.dirname(__file__))

from Geometry.TShape import TShape
from Data.ElementMap import ElementMap
import Objects.ObjectUtils as ObjectUtils
from abc import ABC

class SDObject(ABC):
    def __init__(self):
        self.aliasMap = {}

    def updateProps(self,
                    obj,
                    implementAliasMap = True,
                    implementShapePair = True,
                    implementBoolOpType = True,
                    implementRefine = True,
                    isFeatureOperation = True,
                    typeName = "Unimplemented"
    ):
        if not hasattr(obj, "AliasMap") and implementAliasMap:
            obj.addProperty("App::PropertyString", "AliasMap")
            obj.AliasMap = "{}"
        
        if implementShapePair:
            if not hasattr(obj, "TShape"):
                obj.addProperty("App::PropertyPythonObject", "TShape")
                obj.TShape = TShape()

            if not hasattr(obj, "LastShapeIteration"):
                obj.addProperty("App::PropertyPythonObject", "LastShapeIteration")
                obj.LastShapeIteration = TShape()
        
        if not hasattr(obj, "IsFeatureOperation"):
            obj.addProperty("App::PropertyBool", "IsFeatureOperation")
            obj.setEditorMode("IsFeatureOperation", 3)
            obj.IsFeatureOperation = isFeatureOperation
        
        if not hasattr(obj, "BooleanOperationType") and implementBoolOpType:
            obj.addProperty("App::PropertyEnumeration", "BooleanOperationType")
            obj.BooleanOperationType = ["Fuse", "Cut", "Intersection", "None", "Compound"]
        
        if not hasattr(obj, "StableDesignType"):
            obj.addProperty("App::PropertyString", "StableDesignType")
            obj.setEditorMode("StableDesignType", 3)
            obj.StableDesignType = typeName

        if not hasattr(obj, "Refine") and implementRefine:
            obj.addProperty("App::PropertyBool", "Refine")
            obj.Refine = True
    
    def execute(self, obj, forceCompute = False):
        if forceCompute:
            self.computeShape(obj)
        else:
            parent = ObjectUtils.getParentBody(obj)

            if parent != None:
                parent.recompute(False)

    def computeShape(self, obj):
        pass
    
    def attach(self, obj):
        if hasattr(obj, "AliasMap"):
            self.aliasMap = ObjectUtils.convertAliasMapFromString(obj.AliasMap)

        if hasattr(obj, "TShape"):
            elementMap = ElementMap.fromAliasMap(json.loads(obj.AliasMap))
            obj.TShape = TShape(obj.Shape, elementMap)
            obj.TShape.buildCache()
    
    def onChanged(self, obj, prop):
        if prop == "Visibility" and obj.Visibility == True and obj.IsFeatureOperation:
            parent = ObjectUtils.getParentBody(obj)

            if parent != None:
                parent.Proxy.showFeature(parent, obj)
    
    # we override these to allow for saving w/o errors
    def __str__(self):
        return ""
    
    def __setstate__(self, state):
        return None

    def __getstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None