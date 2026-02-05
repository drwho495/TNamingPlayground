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

class Thickness(SDObject):
    def __init__(self, obj):
        super().__init__()

        obj.Proxy = self
        self.updateProps(obj)
    
    def updateProps(self, obj):
        super().updateProps(obj,
                            implementAliasMap = True, 
                            implementShapePair = True,
                            implementBoolOpType = False,
                            implementRefine = True,
                            isFeatureOperation = True,
                            typeName = "Thickness")
        
        if not hasattr(obj, "Offset"):
            obj.addProperty("App::PropertyDistance", "Offset")
            obj.Offset = 1

        if not hasattr(obj, "Faces"):
            obj.addProperty("App::PropertyStringList", "Faces")

    def attach(self, obj):
        self.updateProps(obj)
        super().attach(obj)

    def onDocumentRestored(self, obj):
        self.attach(obj)

    def computeShape(self, obj):
        self.updateProps(obj)

        obj.LastShapeIteration = obj.TShape.copy()

        if len(obj.Faces) != 0:
            features, index = ObjectUtils.getFeaturesAndIndex(ObjectUtils.getParentBody(obj), obj)

            if index != 0:
                lastFeature = features[index - 1]

                indexedElements = []
                mappedNames = []

                for element in obj.Faces:
                    mappedName = MappedName(element)
                    foundNames = MappingUtils.searchForSimilarNames(mappedName, lastFeature.TShape, lastFeature.LastShapeIteration)

                    for foundName in foundNames:
                        if foundName[1] not in indexedElements:
                            mappedNames.append(foundName[0].toString())
                            indexedElements.append(foundName[1])
            
                mappedResult = GeometryManager.makeMappedThickness(lastFeature.TShape, indexedElements, obj.Offset.Value, obj.ID)

                if obj.Refine:
                    mappedResult = GeometryManager.makeMappedRefineOperation(mappedResult, lastFeature.ID, mappedResult.tag)
                
                obj.TShape = mappedResult
                obj.Shape = mappedResult.getShape()
                obj.Faces = mappedNames
                
                self.aliasMap = ObjectUtils.updateAliasMap(self.aliasMap, mappedResult)
                obj.AliasMap = ObjectUtils.convertAliasMapToString(self.aliasMap)

                ObjectUtils.updateShapeMap(self.aliasMap, obj)
                GeometryManager.colorElementsFromSupport(obj, obj.Shape, obj.TShape.elementMap)

class ThicknessViewObject:
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
        return os.path.join(os.path.dirname(__file__), "..", "Icons", "Thickness.png")
    
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

        if ObjectUtils.isSDObject(featureObj):
            lastFeature = ObjectUtils.getFeaturesAndIndex(ObjectUtils.getParentBody(featureObj), featureObj)[0][-1]
            obj = App.ActiveDocument.addObject("Part::FeaturePython", "Thickness")

            Thickness(obj)
            ThicknessViewObject(obj)

            parent = lastFeature.getParent()

            group = parent.Group
            group.append(obj)
            parent.Group = group

            elements = []

            for element in selection:
                if element.HasSubObjects:
                    if ObjectUtils.isSDObject(element.Object):
                        elementMap = element.Object.TShape.elementMap
                        indexedName = IndexedName.fromString(element.SubElementNames[0])
                                
                        elements.append(elementMap.getMappedName(indexedName).toString())
            
            obj.Faces = elements
            obj.recompute()

            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(obj.Document.Name, obj.Name)

            parent.Proxy.showFeature(parent, obj)
            obj.purgeTouched()