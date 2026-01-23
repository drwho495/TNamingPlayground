import sys
import os

sys.path.append(os.path.dirname(__file__))

import Geometry.GeometryManager as GeometryManager
import Geometry.MappingUtils as MappingUtils
import Features.FeatureUtils as FeatureUtils
from Geometry.TShape import TShape
from Data.ElementMap import ElementMap
from Data.MappedName import MappedName
from Data.IndexedName import IndexedName
from Data.DataEnums import *
import FreeCADGui as Gui
import FreeCAD as App
import json

class TDressup:
    def __init__(self, obj):
        obj.Proxy = self
        self.updateProps(obj)
    
    def updateProps(self, obj):
        if not hasattr(obj, "TElementMap"):
            obj.addProperty("App::PropertyString", "TElementMap")
            obj.TElementMap = "{}"
        
        if not hasattr(obj, "TShape"):
            obj.addProperty("App::PropertyPythonObject", "TShape")
            obj.TShape = TShape()

        if not hasattr(obj, "Radius"):
            obj.addProperty("App::PropertyLength", "Radius")
            obj.Radius = 1
        
        if not hasattr(obj, "LastShapeIteration"):
            obj.addProperty("App::PropertyPythonObject", "LastShapeIteration")
            obj.LastShapeIteration = TShape()

        if not hasattr(obj, "TNamingType"):
            obj.addProperty("App::PropertyString", "TNamingType")
            obj.TNamingType = "TDressup"
        
        if not hasattr(obj, "DressupType"):
            obj.addProperty("App::PropertyEnumeration", "DressupType")
            obj.DressupType = ["Fillet", "Chamfer"]
        
        if not hasattr(obj, "Elements"):
            obj.addProperty("App::PropertyStringList", "Elements")

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

        obj.LastShapeIteration = obj.TShape.copy()

        if len(obj.Elements) != 0:
            features, index = FeatureUtils.getFeaturesAndIndex(obj)

            if index != 0:
                lastFeature = features[index - 1]

                indexedElements = []
                mappedNames = []

                for element in obj.Elements:
                    mappedName = MappedName.fromDictionary(json.loads(element))
                    foundNames = MappingUtils.searchForSimilarNames(mappedName, lastFeature.TShape, lastFeature.LastShapeIteration)

                    for foundName in foundNames:
                        if foundName[1] not in indexedElements:
                            mappedNames.append(json.dumps(foundName[0].toDictionary()))
                            indexedElements.append(foundName[1])
            
                mappedResult = GeometryManager.makeMappedDressup(lastFeature.TShape,
                                                               DressupType.FILLET if obj.DressupType == "Fillet" else DressupType.CHAMFER,
                                                               indexedElements,
                                                               radius = obj.Radius.Value,
                                                               tag = obj.ID)

                if obj.Refine:
                    mappedResult = GeometryManager.makeMappedRefineOperation(mappedResult, lastFeature.ID, mappedResult.tag)
                
                obj.TShape = mappedResult
                obj.Shape = mappedResult.getShape()
                obj.Elements = mappedNames
                obj.TElementMap = json.dumps(mappedResult.elementMap.toDictionary())

                GeometryManager.colorElementsFromSupport(obj, obj.Shape, obj.TShape.elementMap)

    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None

class TDressupViewObject:
    def __init__(self, obj):
        obj.ViewObject.Proxy = self
        self.updateProps(obj.ViewObject)

        self.Object = obj.ViewObject
    
    def updateProps(self, vobj):
        pass

    def attach(self, vobj):
        self.Object = vobj

    def claimChildren(self):
        return []

    def setEdit(self, vobj, mode):
        return False

    def getIcon(self):
        if hasattr(self.Object.Object, "DressupType"):
            if self.Object.Object.DressupType == "Fillet":
                return os.path.join(os.path.dirname(__file__), "..", "Icons", "Fillet.png")
            elif self.Object.Object.DressupType == "Chamfer":
                return os.path.join(os.path.dirname(__file__), "..", "Icons", "Chamfer.png")
        return ""
    
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None
    
def makeDressup(dressupType = DressupType.FILLET):
    selection = Gui.Selection.getCompleteSelection()
    dressupTypeName = "Fillet" if dressupType == DressupType.FILLET else "Chamfer";

    if len(selection) > 0:
        featureObj = selection[0].Object

        if FeatureUtils.isTNamingFeature(featureObj):
            lastFeature = FeatureUtils.getFeaturesAndIndex(featureObj)[0][-1]
            obj = App.ActiveDocument.addObject("Part::FeaturePython", dressupTypeName)

            TDressup(obj)
            TDressupViewObject(obj)

            parent = lastFeature.getParent()

            group = parent.Group
            group.append(obj)
            parent.Group = group

            elements = []

            for element in selection:
                if element.HasSubObjects:
                    if FeatureUtils.isTNamingFeature(element.Object):
                        elementMap = element.Object.TShape.elementMap
                        indexedName = IndexedName.fromString(element.SubElementNames[0])
                                
                        elements.append(json.dumps(elementMap.getMappedName(indexedName).toDictionary()))
            
            obj.Elements = elements
            obj.DressupType = dressupTypeName
            obj.recompute()

            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(obj.Document.Name, obj.Name)

            FeatureUtils.showFeature(obj)
            obj.purgeTouched()