import sys
import os

sys.path.append(os.path.dirname(__file__))

import Geometry.GeometryUtils as GeometryUtils
import Geometry.MappingUtils as MappingUtils
from Geometry.TShape import TShape
from Data.IndexedName import IndexedName
from Data.ElementMap import ElementMap
from Data.MappedName import MappedName
from Data.DataEnums import *
import FreeCADGui as Gui
import FreeCAD as App
import Part
import json

class Selector:
    def updateProps(self, obj):
        if not hasattr(obj, "LinkedMappedName"):
            obj.addProperty("App::PropertyString", "LinkedMappedName")
            obj.LinkedMappedName = "{}"
        
        if not hasattr(obj, "LinkedObjectName"):
            obj.addProperty("App::PropertyString", "LinkedObjectName")
            obj.LinkedObjectName = ""

    def __init__(self, obj):
        obj.Proxy = self
        self.updateProps(obj)

    def updateLink(self, obj, newLinkObj, newLinkName: MappedName):
        obj.LinkedObjectName = newLinkObj.Name
        obj.LinkedMappedName = json.dumps(newLinkName.toDictionary())
    
    def execute(self, obj):
        self.updateProps(obj)

        if obj.Shape.isNull():
            obj.Shape = Part.makeSphere(2)
        
        linkedObject = obj.Document.getObject(obj.LinkedObjectName)

        if hasattr(linkedObject, "TNamingType") and hasattr(linkedObject, "TShape"):
            mappedName = MappedName.fromDictionary(json.loads(obj.LinkedMappedName))
            indexedNames = MappingUtils.searchForSimilarNames(mappedName, linkedObject.TShape, linkedObject.LastShapeIteration)

            if len(indexedNames) != 0:
                obj.Label = f"Selected Element: {indexedNames[0].toString()}"
                elementShape = Part.__fromPythonOCC__(linkedObject.TShape.getElement(indexedNames[0]))

                obj.Placement.Base = elementShape.CenterOfGravity

                print(f"Indexed Names: {indexedNames}")
            else:
                obj.Label = f"Broken Reference"
    
    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None

class SelectionViewObject:
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
    
def makeSelector():
    obj = App.ActiveDocument.addObject("Part::FeaturePython", "Selector")

    Selector(obj)
    SelectionViewObject(obj)

    selection = Gui.Selection.getCompleteSelection()

    for element in selection:
        if element.HasSubObjects:
            elementMap = element.Object.TShape.elementMap
            indexedName = IndexedName.fromString(element.SubElementNames[0])
                    
            obj.Proxy.updateLink(obj, element.Object, elementMap.getMappedName(indexedName))
            break