import sys
import os
import copy

sys.path.append(os.path.dirname(__file__))

from Data.ElementMap import ElementMap
from Data.IndexedName import IndexedName
from Data.MappedName import MappedName
import MappingUtils as MappingUtils
import FreeCAD as App
import Part

from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.TopTools import TopTools_IndexedMapOfShape
from OCC.Core.TopExp import topexp
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX
from OCC.Core.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCC.Core.TopExp import TopExp_Explorer

class TShape:
    def __init__(self, sourceShape = Part.Shape(), elementMap = ElementMap()):
        if isinstance(sourceShape, Part.Shape):
            self.freecadShape = sourceShape
            self.cachedOCCTShape = None
        else:
            self.freecadShape = Part.__fromPythonOCC__(sourceShape)
            self.cachedOCCTShape = sourceShape

        self.elementMap = elementMap
        self.shapeMap = None
        self.ancestorsMap = None
        self.tag = self.freecadShape.Tag

    def __hash__(self):
        return hash(self.freecadShape)

    def __eq__(self, value):
        if isinstance(value, TShape):
            return hash(value) == hash(self)
    
    def copy(self):
        shapeCopy = TShape(self.freecadShape.copy(), self.elementMap.copy())

        return shapeCopy

    def clearCache(self):
        self.cachedOCCTShape = None
        self.shapeMap = None
        self.ancestorsMap = None
    
    def resetPlacement(self):
        newShape = self.freecadShape.copy()
        
        newShape.Placement = App.Placement()
        self.freecadShape = newShape

        self.clearCache()

    def buildAncestorsMap(self, clearCache = False):
        if clearCache: self.clearCache()

        if self.shapeMap == None:
            self.buildShapeMap(False)
            
        self.ancestorsMap = {}

        elementTypes = [TopAbs_EDGE, TopAbs_FACE, TopAbs_VERTEX]

        for sourceType in elementTypes:
            for ancestorType in elementTypes:
                if ancestorType == sourceType:
                    continue

                allAncestors = TopTools_IndexedDataMapOfShapeListOfShape()

                topexp.MapShapesAndAncestors(
                    self.getOCCTShape(),
                    sourceType,
                    ancestorType,
                    allAncestors
                )

                for indexedNameStr, shape in self.getShapeMap().items():
                    if shape.ShapeType() == sourceType and allAncestors.Contains(shape):
                        for ancestorShape in MappingUtils.occtLOStoList(allAncestors.FindFromKey(shape)):
                            indexedName = self.getIndexedNameOfShape(ancestorShape)

                            if indexedNameStr not in self.ancestorsMap: self.ancestorsMap[indexedNameStr] = []
                            
                            if indexedName.toString() not in self.ancestorsMap[indexedNameStr]:
                                self.ancestorsMap[indexedNameStr].append(indexedName.toString())

    def getAncestorsOfType(self, sourceShape: TopoDS_Shape, ancestorType: str):
        sourceIndexedNameStr = self.getIndexedNameOfShape(sourceShape).toString()
        returnList = []

        if sourceIndexedNameStr in self.ancestorsMap:
            ancestors = self.ancestorsMap[sourceIndexedNameStr]

            for ancestor in ancestors:
                if IndexedName.fromString(ancestor).elementType == ancestorType:
                    returnList.append(self.shapeMap[ancestor])
        
        return returnList
    
    def getSubElementsOfChild(self, childShape, type: str):
        subElements = []
        exp = TopExp_Explorer(childShape, MappingUtils.getElementTypeIndex(type))

        while exp.More():
            subElements.append(exp.Current())
            exp.Next()

        return subElements

    def getOCCTShape(self):
        if self.cachedOCCTShape == None:
            self.cachedOCCTShape = Part.__toPythonOCC__(self.freecadShape)

        return self.cachedOCCTShape
    
    def getShape(self):
        return self.freecadShape
    
    def getIDShapeMap(self):
        if self.shapeMap == None:
            self.buildShapeMap(False)

        returnMap = {}
        
        for indexString, shape in self.shapeMap.items():
            indexedName = IndexedName.fromString(indexString)

            if self.elementMap.hasIndexedName(indexedName):
                returnMap[self.elementMap.getMappedName(indexedName)] = shape
        
        return returnMap
    
    def getIndexedNameOfShape(self, childOCCTShape):
        if self.shapeMap == None: self.buildShapeMap(False)

        for indexedNameStr, shape in self.shapeMap.items():
            if shape.IsSame(childOCCTShape):
                returnName = IndexedName.fromString(indexedNameStr)

                return returnName
        
        return IndexedName()
    
    def getShapeMap(self):
        return ({} if self.shapeMap == None else self.shapeMap)
    
    def buildCache(self):
        self.buildShapeMap(True)
        self.buildAncestorsMap(False)
    
    def buildShapeMap(self, clearCache = True):
        if clearCache: self.clearCache()

        self.shapeMap = {}

        for elementType in [TopAbs_VERTEX, TopAbs_EDGE, TopAbs_FACE]:
            internalShapeMap = TopTools_IndexedMapOfShape()

            topexp.MapShapes(self.getOCCTShape(), elementType, internalShapeMap)

            for i in range(1, internalShapeMap.Size() + 1):
                self.shapeMap[f"{MappingUtils.getElementTypeName(elementType)}{i}"] = internalShapeMap.FindKey(i)

    def getIndexedName(self, searchName: MappedName):
        for loopName, shape in self.getIDShapeMap().items():
            if loopName == searchName:
                return self.getIndexedNameOfShape(shape)

    def getElement(self, name):
        if self.shapeMap == None: self.buildShapeMap(False)

        if isinstance(name, IndexedName):
            return self.shapeMap[name.toString()]