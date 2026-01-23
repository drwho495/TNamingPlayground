import sys
import os

sys.path.append(os.path.dirname(__file__))

import Geometry.GeometryManager as GeometryManager
import Features.FeatureUtils as FeatureUtils
from Geometry.TShape import TShape
from Data.ElementMap import ElementMap
from Data.DataEnums import *
import FreeCADGui as Gui
import FreeCAD as App
import json

class TExtrusion:
    def __init__(self, obj):
        obj.Proxy = self
        self.updateProps(obj)
    
    def updateProps(self, obj):
        if not hasattr(obj, "TElementMap"):
            obj.addProperty("App::PropertyString", "TElementMap")
            obj.TElementMap = "{}"

        if not hasattr(obj, "Length"):
            obj.addProperty("App::PropertyDistance", "Length")
            obj.Length = 10
        
        if not hasattr(obj, "Support"):
            obj.addProperty("App::PropertyLink", "Support")

        if not hasattr(obj, "TShape"):
            obj.addProperty("App::PropertyPythonObject", "TShape")
            obj.TShape = TShape()
        
        if not hasattr(obj, "LastShapeIteration"):
            obj.addProperty("App::PropertyPythonObject", "LastShapeIteration")
            obj.LastShapeIteration = TShape()

        if not hasattr(obj, "TNamingType"):
            obj.addProperty("App::PropertyString", "TNamingType")
            obj.TNamingType = "TExtrusion"

        if not hasattr(obj, "BooleanOperationType"):
            obj.addProperty("App::PropertyEnumeration", "BooleanOperationType")
            obj.BooleanOperationType = ["Fuse", "Cut", "Intersection", "None", "Compound"]
        
        if not hasattr(obj, "Refine"):
            obj.addProperty("App::PropertyBool", "Refine")
            obj.Refine = True
    
    def attach(self, obj):
        self.updateProps(obj)

        elementMap = ElementMap.fromDictionary(json.loads(obj.TElementMap))
        obj.TShape = TShape(obj.Shape, elementMap)
        obj.TShape.buildCache()

    def onDocumentRestored(self, obj):
        self.attach(obj)

    def execute(self, obj):
        self.updateProps(obj)

        if obj.Support != None:
            features, index = FeatureUtils.getFeaturesAndIndex(obj)

            sketchShape = GeometryManager.getFaceOfSketch(obj.Support)
            normal = obj.Support.Placement.Rotation.multVec(App.Vector(0, 0, 1))
            extrusionDirection = normal.multiply(obj.Length.Value)
            tag = obj.ID

            if index > 0 and obj.BooleanOperationType != "None":
                tag = -tag

            mappedExtrusion = GeometryManager.makeMappedExtrusion(sketchShape, extrusionDirection, tag)[0]

            obj.LastShapeIteration = obj.TShape.copy()           

            if index > 0 and obj.BooleanOperationType != "None":
                lastFeatureTShape = features[index - 1].TShape
                booleanType = None
                mappedResult = TShape()

                if obj.BooleanOperationType == "Fuse":
                    booleanType = BooleanType.FUSE
                elif obj.BooleanOperationType == "Cut":
                    booleanType = BooleanType.CUT
                elif obj.BooleanOperationType == "Intersection":
                    booleanType = BooleanType.INTERSECTION

                if booleanType != None:
                    mappedResult = GeometryManager.makeMappedBooleanOperation(lastFeatureTShape, mappedExtrusion, booleanType, obj.ID)[0]

                    if obj.Refine:
                        mappedResult = GeometryManager.makeMappedRefineOperation(mappedResult, abs(lastFeatureTShape.tag), obj.ID)
                elif obj.BooleanOperationType == "Compound":
                    mappedResult = GeometryManager.makeMappedCompound([lastFeatureTShape, mappedExtrusion], obj.ID)

                obj.TShape = mappedResult
                obj.Shape = mappedResult.getShape()
                obj.TElementMap = json.dumps(mappedResult.elementMap.toDictionary())
            else:
                obj.TShape = mappedExtrusion
                obj.Shape = mappedExtrusion.getShape()
                obj.TElementMap = json.dumps(mappedExtrusion.elementMap.toDictionary())
            
            GeometryManager.colorElementsFromSupport(obj, obj.Shape, obj.TShape.elementMap)

            
    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None

class TExtrusionViewObject:
    def __init__(self, obj):
        obj.ViewObject.Proxy = self
        self.updateProps(obj.ViewObject)

        self.Object = obj.ViewObject
    
    def updateProps(self, vobj):
        pass

    def attach(self, vobj):
        self.Object = vobj

    def claimChildren(self):
        if hasattr(self, "Object") and self.Object.Object.Support != None:
            return [self.Object.Object.Support]
        return []

    def setEdit(self, vobj, mode):
        return False

    def getIcon(self):
        return os.path.join(os.path.dirname(__file__), "..", "Icons", "Extrusion.png")
    
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None
    
def makeExtrusion():
    selection = Gui.Selection.getSelection()
    error = "Please select a sketch to extrude!"

    if len(selection) == 1:
        selObj = selection[0]

        if selObj.TypeId == "Sketcher::SketchObject":
            error = None
            parent = selObj.getParent()

            if parent != None:
                obj = App.ActiveDocument.addObject("Part::FeaturePython", "Extrusion")

                TExtrusion(obj)
                TExtrusionViewObject(obj)

                obj.Support = selObj
                group = parent.Group

                group.append(obj)
                parent.Group = group

                FeatureUtils.showFeature(obj)
            else:
                error = "Please select a sketch that is in a part to extrude!"
    
    if error != None:
        App.Console.PrintError(error)