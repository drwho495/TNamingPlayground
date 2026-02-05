import sys
import os

sys.path.append(os.path.dirname(__file__))

from Objects.StableDesignObject import SDObject
import Geometry.GeometryManager as GeometryManager
import Geometry.MappingUtils as MappingUtils
import Objects.ObjectUtils as ObjectUtils
from Geometry.TShape import TShape
from Data.ElementMap import ElementMap
from Data.MappedName import MappedName
from Data.IndexedName import IndexedName
from Data.DataEnums import *
import FreeCADGui as Gui
import FreeCAD as App
import json

class Dressup(SDObject):
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
                            typeName = "Dressup")

        if not hasattr(obj, "Radius"):
            obj.addProperty("App::PropertyLength", "Radius")
            obj.Radius = 1
        
        if not hasattr(obj, "DressupType"):
            obj.addProperty("App::PropertyEnumeration", "DressupType")
            obj.DressupType = ["Fillet", "Chamfer"]
        
        if not hasattr(obj, "Elements"):
            obj.addProperty("App::PropertyStringList", "Elements")

    def attach(self, obj):
        self.updateProps(obj)
        super().attach(obj)

    def onDocumentRestored(self, obj):
        self.attach(obj)

    def computeShape(self, obj):
        self.updateProps(obj)

        obj.LastShapeIteration = obj.TShape.copy()

        if len(obj.Elements) != 0:
            features, index = ObjectUtils.getFeaturesAndIndex(ObjectUtils.getParentBody(obj), obj)

            if index != 0:
                lastFeature = features[index - 1]

                indexedElements = []
                mappedNames = []

                for element in obj.Elements:
                    mappedName = MappedName(element)
                    foundNames = MappingUtils.searchForSimilarNames(mappedName, lastFeature.TShape, lastFeature.LastShapeIteration)

                    for foundName in foundNames:
                        if foundName[1] not in indexedElements:
                            mappedNames.append(foundName[0].toString())
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

                self.aliasMap = ObjectUtils.updateAliasMap(self.aliasMap, mappedResult)
                obj.AliasMap = ObjectUtils.convertAliasMapToString(self.aliasMap)

                ObjectUtils.updateShapeMap(self.aliasMap, obj)
                GeometryManager.colorElementsFromSupport(obj, obj.Shape, obj.TShape.elementMap)

class DressupViewObject:
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

        if ObjectUtils.isSDObject(featureObj):
            lastFeature = ObjectUtils.getFeaturesAndIndex(ObjectUtils.getParentBody(featureObj), featureObj)[0][-1]
            obj = App.ActiveDocument.addObject("Part::FeaturePython", dressupTypeName)

            Dressup(obj)
            DressupViewObject(obj)

            parent = ObjectUtils.getParentBody(lastFeature)

            group = parent.Group
            group.append(obj)
            parent.Group = group

            elements = []

            for element in selection:
                if element.HasSubObjects:
                    if ObjectUtils.isSDObject(element.Object):
                        elementMap = element.Object.TShape.elementMap
                        indexedName = IndexedName.fromString(element.SubElementNames[0])
                        mappedName = elementMap.getMappedName(indexedName)

                        if mappedName != None:
                            elements.append(mappedName.toString())
            
            obj.Elements = elements
            obj.DressupType = dressupTypeName
            obj.recompute()

            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(obj.Document.Name, obj.Name)

            parent.Proxy.showFeature(parent, obj)
            obj.purgeTouched()