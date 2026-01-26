import sys
import os

sys.path.append(os.path.dirname(__file__))

from Objects.StableDesignObject import SDObject
import Objects.ObjectUtils as ObjectUtils
import Geometry.GeometryManager as GeometryManager
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

class Selector(SDObject):
    def updateProps(self, obj):
        super().updateProps(obj,
                            implementAliasMap = False, 
                            implementShapePair = False,
                            implementBoolOpType = False,
                            implementRefine = False,
                            isFeatureOperation = False,
                            typeName = "Selector")
        
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
        
        obj.Placement = App.Placement()
        linkedObject = obj.Document.getObject(obj.LinkedObjectName)

        if ObjectUtils.isSDObject(linkedObject):
            mappedName = MappedName.fromDictionary(json.loads(obj.LinkedMappedName))
            foundNames = MappingUtils.searchForSimilarNames(mappedName, linkedObject.TShape, linkedObject.LastShapeIteration)
            spheres = []

            print(f"Indexed Names: {foundNames}")

            for foundName in foundNames:
                obj.Label = f"Selected Element: {foundName[1].toString()}"
                elementShape = Part.__fromPythonOCC__(linkedObject.TShape.getElement(foundName[1]))

                sphere = Part.makeSphere(3)
                sphere.Placement.Base = elementShape.CenterOfGravity

                spheres.append(sphere)
            
            if len(foundNames) == 0:
                obj.ViewObject.DiffuseColor = (1.0, 0.0, 0.0)
                obj.Label = f"Broken Reference"
            else:
                obj.ViewObject.DiffuseColor = (0.0, 0.0, 1.0)
                
                obj.Shape = Part.makeCompound(spheres)

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