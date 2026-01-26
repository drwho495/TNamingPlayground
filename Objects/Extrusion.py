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

class Extrusion(SDObject):
    def __init__(self, obj):
        super().__init__()

        obj.Proxy = self
        self.updateProps(obj)
    
    def updateProps(self, obj):
        super().updateProps(obj,
                            implementAliasMap = True, 
                            implementShapePair = True,
                            implementBoolOpType = True,
                            implementRefine = True,
                            isFeatureOperation = True,
                            typeName = "Extrusion")
        
        if not hasattr(obj, "Length"):
            obj.addProperty("App::PropertyDistance", "Length")
            obj.Length = 10
        
        if not hasattr(obj, "Support"):
            obj.addProperty("App::PropertyLink", "Support")
        
        if not hasattr(obj, "Refine"):
            obj.addProperty("App::PropertyBool", "Refine")
            obj.Refine = True
    
    def attach(self, obj):
        super().attach(obj)

        self.updateProps(obj)

    def onDocumentRestored(self, obj):
        self.attach(obj)

    def computeShape(self, obj):
        self.updateProps(obj)

        if obj.Support != None:
            features, index = ObjectUtils.getFeaturesAndIndex(ObjectUtils.getParentBody(obj), obj)

            sketchShape = GeometryManager.getFaceOfSketch(obj.Support)
            normal = obj.Support.Placement.Rotation.multVec(App.Vector(0, 0, 1))
            extrusionDirection = normal.multiply(obj.Length.Value)
            tag = obj.ID

            if index > 0 and obj.BooleanOperationType != "None":
                tag = -tag

            mappedExtrusion = GeometryManager.makeMappedExtrusion(sketchShape, extrusionDirection, tag)

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
            else:
                obj.TShape = mappedExtrusion
                obj.Shape = mappedExtrusion.getShape()
            
            self.aliasMap = ObjectUtils.updateAliasMap(self.aliasMap, obj.TShape)
            obj.AliasMap = ObjectUtils.convertAliasMapToString(self.aliasMap)
            ObjectUtils.updateShapeMap(self.aliasMap, obj)

            obj.Support.purgeTouched()

            GeometryManager.colorElementsFromSupport(obj, obj.Shape, obj.TShape.elementMap)

class ExtrusionViewObject:
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
            parent = ObjectUtils.getParentBody(selObj)

            if parent == None:
                parent = ObjectUtils.getActiveBody()

            if parent != None:
                obj = App.ActiveDocument.addObject("Part::FeaturePython", "Extrusion")

                Extrusion(obj)
                ExtrusionViewObject(obj)

                obj.Support = selObj
                group = parent.Group

                group.append(obj)
                parent.Group = group

                parent.Proxy.showFeature(parent, obj)
            else:
                error = "Please select a sketch that is in a DesignBody to extrude!"
    
    if error != None:
        App.Console.PrintError(error)