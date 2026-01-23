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

class TThickness:
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

        if not hasattr(obj, "Offset"):
            obj.addProperty("App::PropertyDistance", "Offset")
            obj.Offset = 1

        if not hasattr(obj, "LastShapeIteration"):
            obj.addProperty("App::PropertyPythonObject", "LastShapeIteration")
            obj.LastShapeIteration = TShape()

        if not hasattr(obj, "TNamingType"):
            obj.addProperty("App::PropertyString", "TNamingType")
            obj.TNamingType = "TDressup"
        
        if not hasattr(obj, "Faces"):
            obj.addProperty("App::PropertyStringList", "Faces")

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

        if len(obj.Faces) != 0:
            features, index = FeatureUtils.getFeaturesAndIndex(obj)

            if index != 0:
                lastFeature = features[index - 1]

                indexedElements = []
                mappedNames = []

                for element in obj.Faces:
                    mappedName = MappedName.fromDictionary(json.loads(element))
                    foundNames = MappingUtils.searchForSimilarNames(mappedName, lastFeature.TShape, lastFeature.LastShapeIteration)

                    for foundName in foundNames:
                        if foundName[1] not in indexedElements:
                            mappedNames.append(json.dumps(foundName[0].toDictionary()))
                            indexedElements.append(foundName[1])
            
                mappedResult = GeometryManager.makeMappedThickness(lastFeature.TShape, indexedElements, obj.Offset.Value, obj.ID)

                if obj.Refine:
                    pass
                    # mappedResult = GeometryManager.makeMappedRefineOperation(mappedResult, lastFeature.ID, mappedResult.tag)
                
                obj.TShape = mappedResult
                obj.Shape = mappedResult.getShape()
                obj.Faces = mappedNames
                obj.TElementMap = json.dumps(mappedResult.elementMap.toDictionary())

                GeometryManager.colorElementsFromSupport(obj, obj.Shape, obj.TShape.elementMap)

    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None

class TThicknessViewObject:
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
        return os.path.join(os.path.dirname(__file__), "..", "icons", "Extrusion.svg")
    
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None
    
def makeThickness():
    selection = Gui.Selection.getCompleteSelection()

    if len(selection) > 0:
        featureObj = selection[0].Object

        if FeatureUtils.isTNamingFeature(featureObj):
            lastFeature = FeatureUtils.getFeaturesAndIndex(featureObj)[0][-1]
            obj = App.ActiveDocument.addObject("Part::FeaturePython", "Thickness")

            TThickness(obj)
            TThicknessViewObject(obj)

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
            
            obj.Faces = elements
            obj.recompute()

            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(obj.Document.Name, obj.Name)

            FeatureUtils.showFeature(obj)
            obj.purgeTouched()