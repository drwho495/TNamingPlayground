import sys
import os

sys.path.append(os.path.dirname(__file__))

import Geometry.GeometryUtils as GeometryUtils
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

                for element in obj.Elements:
                    mappedName = MappedName.fromDictionary(json.loads(element))
                    indexedNames = MappingUtils.searchForSimilarNames(mappedName, lastFeature.TShape, lastFeature.LastShapeIteration)

                    indexedElements.extend(indexedNames)
            
                mappedResult = GeometryUtils.makeMappedDressup(lastFeature.TShape,
                                                               DressupType.FILLET if obj.DressupType == "Fillet" else DressupType.CHAMFER,
                                                               indexedElements)
                
                obj.TShape = mappedResult
                obj.Shape = mappedResult.getShape()
                obj.TElementMap = json.dumps(mappedResult.elementMap.toDictionary())

                GeometryUtils.colorElementsFromSupport(obj, obj.Shape, obj.TShape.elementMap)

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
        return os.path.join(os.path.dirname(__file__), "..", "icons", "Extrusion.svg")
    
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None
    
def makeDressup(dressupType = DressupType.FILLET):
    obj = App.ActiveDocument.addObject("Part::FeaturePython", "Fillet" if dressupType == DressupType.FILLET else "Chamfer")

    TDressup(obj)
    TDressupViewObject(obj)

    selection = Gui.Selection.getCompleteSelection()
    elements = []

    for element in selection:
        if element.HasSubObjects:
            elementMap = element.Object.TShape.elementMap
            indexedName = IndexedName.fromString(element.SubElementNames[0])
                    
            elements.append(json.dumps(elementMap.getMappedName(indexedName).toDictionary()))
    
    obj.Elements = elements