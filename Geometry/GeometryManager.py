import sys
import os

sys.path.append(os.path.dirname(__file__))

from Data.ElementMap import ElementMap
from Data.IndexedName import IndexedName
from Data.MappedName import MappedName
from Data.DataEnums import *
import PerformanceTimer as PerformanceTimer
import FreeCAD as App
import FreeCADGui as Gui
import Part
from OCC.Core.TopoDS import TopoDS_Compound
from OCC.Core.BRep import BRep_Builder
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeChamfer
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Core.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCC.Core.TopTools import TopTools_ListOfShape
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakeThickSolid
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.gp import gp_Vec
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX
from OCC.Core.BRepAlgoAPI import (
    BRepAlgoAPI_Fuse,
    BRepAlgoAPI_Cut,
    BRepAlgoAPI_Common
)
from statistics import mode
from TShape import TShape
import Geometry.MappingUtils as MappingUtils
from typing import List
from OCC.Core.GeomAbs import GeomAbs_Arc

class ShapeHistoryList:
    def __init__(self, historyType: int):
        self.historyList = {}
        self.reverseHistoryList = {}
        self.historyType = historyType

    def extendList(self, indexedName: IndexedName, OCCTList, parentShape: TShape):
        if OCCTList.Size() == 0: return

        self.historyList[indexedName] = []

        for element in MappingUtils.occtLOStoList(OCCTList):
            foundName = parentShape.getIndexedNameOfShape(element)
            foundName.parentIdentifier = parentShape.tag

            if foundName not in self.historyList[indexedName]:
                self.historyList[indexedName].append(foundName)

    def getHistoryOfElement(self, indexedName: IndexedName):
        if indexedName in self.reverseHistoryList:
            return self.reverseHistoryList[indexedName]
    
    def getReverseHistoryOfElement(self, indexedName: IndexedName):
        if indexedName in self.historyList:
            return self.historyList[indexedName]
    
    def updateReverseList(self):
        self.reverseHistoryList = {}

        for sourceIndexedName, destinationNames in self.historyList.items():
            for name in destinationNames:
                if name not in self.reverseHistoryList: self.reverseHistoryList[name] = []

                self.reverseHistoryList[name].append(sourceIndexedName)

def makeMappedRefineOperation(shape: TShape, baseShapeTag: int, tag: int = 0):
    PerformanceTimer.GlobalTimer.addKey("Refine")

    maker = ShapeUpgrade_UnifySameDomain(shape.getOCCTShape(), True, True, True)
    maker.Build()

    returnShape = TShape(maker.Shape(), ElementMap())

    generatedShapes = ShapeHistoryList(0)
    modifiedShapes = ShapeHistoryList(1)
    history = maker.History()
    returnShape.tag = tag

    for indexedNameStr, subElement in shape.getShapeMap().items():
        indexedName = IndexedName.fromString(indexedNameStr)
        indexedName.parentIdentifier = shape.tag

        generatedShapes.extendList(indexedName,
                                   history.Generated(subElement),
                                   returnShape)
    
    for indexedNameStr, subElement in shape.getShapeMap().items():
        indexedName = IndexedName.fromString(indexedNameStr)
        indexedName.parentIdentifier = shape.tag

        modifiedShapes.extendList(indexedName,
                                  history.Modified(subElement),
                                  returnShape)
    
    generatedShapes.updateReverseList()
    modifiedShapes.updateReverseList()
    
    mapSubElement(returnShape, shape)

    # for newIndexedName, sourceShapes in modifiedShapes.reverseHistoryList.items():
    #     newMappedName = None
    #     otherMappedNames = []
    #     foundNameHasIDs = False

    #     if len(sourceShapes) == 0:
    #         continue
            
    #     for sourceShapeIndexedName in sourceShapes:
    #         foundName = shape.elementMap.getMappedName(sourceShapeIndexedName).copy()

    #         otherMappedNames.append(foundName)

    #         if len(foundName.mappedSections) > 1 and foundName.mappedSections[-2].iterationTag == baseShapeTag:
    #             if not foundNameHasIDs:
    #                 newMappedName = foundName
                    
    #                 if len(foundName.masterIDs()) != 0:
    #                     foundNameHasIDs = True

    #     if newMappedName == None:
    #         newMappedName = shape.elementMap.getMappedName(sourceShapes[0])

    #     otherMappedNames.remove(newMappedName)
        
    #     newSection = MappedSection(opCode = OpCode.REFINE,
    #                                mapModifier = MapModifier.REMAP,
    #                                iterationTag = returnShape.tag,
    #                                elementType = newIndexedName.elementType,
    #                                ancestors = [],
    #                                deletedNames = []).copy()
        
    #     for otherMappedName in otherMappedNames:
    #         newSection.deletedNames.append(otherMappedName.copy())
 
    #     newMappedName.mappedSections.append(newSection)
    #     returnShape.elementMap.setElement(newIndexedName, newMappedName.copy())

    PerformanceTimer.GlobalTimer.pauseKey("Refine")

    return returnShape

def mapPrismLikeShape(supportTShape: TShape, prismLikeTShape: TShape, opCode: OpCode):
    topVertexes = []

    mapSubElement(prismLikeTShape, supportTShape, newInitialTag = prismLikeTShape.tag)
    prismLikeTShape.buildShapeMap(False)

    for mappedName, shape in prismLikeTShape.getIDShapeMap().items():
        if shape.ShapeType() == TopAbs_EDGE:
            faceAncestors = prismLikeTShape.getAncestorsOfType(shape, "Face")

            for face in faceAncestors:
                faceIndexedName = prismLikeTShape.getIndexedNameOfShape(face)

                if not prismLikeTShape.elementMap.hasIndexedName(faceIndexedName):
                    prismLikeTShape.elementMap.setElement(faceIndexedName, MappedName.makeName(initialTag = prismLikeTShape.tag,
                                                                                                referenceIDs = mappedName.referenceIDs(),
                                                                                                elementType = "F",
                                                                                                mapperInfo = "EXT")
                    )
        elif shape.ShapeType() == TopAbs_VERTEX:
            edgeAncestors = prismLikeTShape.getAncestorsOfType(shape, "Edge")

            for edge in edgeAncestors:
                edgeIndexedName = prismLikeTShape.getIndexedNameOfShape(edge)

                if not prismLikeTShape.elementMap.hasIndexedName(edgeIndexedName):
                    prismLikeTShape.elementMap.setElement(edgeIndexedName, MappedName.makeName(initialTag = prismLikeTShape.tag,
                                                                                                referenceIDs = mappedName.referenceIDs(),
                                                                                                elementType = "E",
                                                                                                mapperInfo = "EXT")
                    )
                
                vertexes = prismLikeTShape.getSubElementsOfChild(edge, "Vertex")

                for vertex in vertexes:
                    vertexIndexedName = prismLikeTShape.getIndexedNameOfShape(vertex)

                    if not prismLikeTShape.elementMap.hasIndexedName(vertexIndexedName):
                        prismLikeTShape.elementMap.setElement(vertexIndexedName, MappedName.makeName(initialTag = prismLikeTShape.tag,
                                                                                                        referenceIDs = mappedName.referenceIDs(),
                                                                                                        elementType = "V",
                                                                                                        mapperInfo = "EXT")
                        )

                        topVertexes.append(vertexIndexedName)
    topEdges = {}

    for vertexIndexedName in topVertexes:
        edgeAncestors = prismLikeTShape.getAncestorsOfType(prismLikeTShape.getElement(vertexIndexedName), "Edge")

        for edge in edgeAncestors:
            edgeIndexedName = prismLikeTShape.getIndexedNameOfShape(edge)

            if not prismLikeTShape.elementMap.hasIndexedName(edgeIndexedName):
                if edgeIndexedName not in topEdges:
                    topEdges[edgeIndexedName] = []
                
                topEdges[edgeIndexedName].extend(prismLikeTShape.elementMap.getMappedName(vertexIndexedName).referenceIDs())
    
    topFaces = {}

    for edgeIndexedName, IDs in topEdges.items():
        formattedIDs = []

        for id in IDs:
            refID = id
            idSuffix = ""

            if ":" in id:
                idSplit = id.split(":")
                refID = idSplit[0]
                idSuffix = f":{':'.join(idSplit[1:])}"
            
            if "v" not in id: continue

            formattedIDs.append(f"{refID.split('v')[0]}{idSuffix}")
        
        modeID = mode(formattedIDs)

        prismLikeTShape.elementMap.setElement(edgeIndexedName, MappedName.makeName(initialTag = prismLikeTShape.tag,
                                                                                   referenceIDs = [modeID],
                                                                                   elementType = "E",
                                                                                   mapperInfo = "CPY")
        )

        faceAncestors = prismLikeTShape.getAncestorsOfType(prismLikeTShape.getElement(edgeIndexedName), "Face")

        for face in faceAncestors:
            faceIndexedName = prismLikeTShape.getIndexedNameOfShape(face)

            if not prismLikeTShape.elementMap.hasIndexedName(faceIndexedName):
                if faceIndexedName not in topFaces:
                    topFaces[faceIndexedName] = []

                if modeID not in topFaces[faceIndexedName]: topFaces[faceIndexedName].append(modeID)
        
    for topFaceIndexedName, ids in topFaces.items():
        prismLikeTShape.elementMap.setElement(topFaceIndexedName, MappedName.makeName(initialTag = prismLikeTShape.tag,
                                                                                        referenceIDs = ids,
                                                                                        elementType = "F",
                                                                                        mapperInfo = "CPY")
        )

def mapShapeWithMaker(mapTShape: TShape, sourceShapes: List[TShape], maker, tag: int = 0):
    pass

def makeMappedDressup(baseShape: TShape, dressupType: DressupType, dressupElements: List[IndexedName], radius: float = 1, tag: int = 0):
    PerformanceTimer.GlobalTimer.addKey("Dressup")

    baseShape.buildCache()
    maker = None

    if dressupType == DressupType.FILLET:
        maker = BRepFilletAPI_MakeFillet(baseShape.getOCCTShape())
    else:
        maker = BRepFilletAPI_MakeChamfer(baseShape.getOCCTShape())

    for element in dressupElements:
        if element.elementType == "Edge":
            maker.Add(radius, baseShape.getElement(element))
        if element.elementType == "Face":
            for edge in baseShape.getSubElementsOfChild(baseShape.getElement(element), "Edge"):
                maker.Add(radius, edge)
    
    maker.Build()

    returnShape = TShape(maker.Shape(), ElementMap())
    returnShape.tag = tag
    returnShape.buildCache()

    mapSubElement(returnShape, baseShape)

    generatedShapes = ShapeHistoryList(0)
    modifiedShapes = ShapeHistoryList(1)

    for indexedNameStr, subElement in baseShape.getShapeMap().items():
        indexedName = IndexedName.fromString(indexedNameStr)
        indexedName.parentIdentifier = baseShape.tag

        generatedShapes.extendList(indexedName,
                                   maker.Generated(subElement),
                                   returnShape)

    for indexedNameStr, subElement in baseShape.getShapeMap().items():
        indexedName = IndexedName.fromString(indexedNameStr)
        indexedName.parentIdentifier = baseShape.tag

        modifiedShapes.extendList(indexedName,
                                  maker.Modified(subElement),
                                  returnShape)
        
    # for sourceName, newShapes in modifiedShapes.historyList.items():
    #     for i, newShapeIndexedName in enumerate(newShapes):
    #         if returnShape.elementMap.hasIndexedName(newShapeIndexedName): continue

    #         newMappedName = baseShape.elementMap.getMappedName(sourceName).copy()
            
    #         newMappedName.mappedSections.append(MappedSection(opCode = OpCode.DRESSUP,
    #                                                           mapModifier = MapModifier.REMAP,
    #                                                           iterationTag = returnShape.tag,
    #                                                           elementType = newShapeIndexedName.elementType,
    #                                                           index = i,
    #                                                           totalNumberOfSectionElements = len(newShapes),
    #                                                           ancestors = [])
    #         )

    #         returnShape.elementMap.setElement(newShapeIndexedName, newMappedName)
    
    # for sourceName, newShapes in generatedShapes.historyList.items():
    #     for i, newShapeIndexedName in enumerate(newShapes):
    #         if returnShape.elementMap.hasIndexedName(newShapeIndexedName): continue

    #         newMappedName = MappedName([MappedSection(opCode = OpCode.DRESSUP,
    #                                                   mapModifier = MapModifier.REMAP,
    #                                                   iterationTag = returnShape.tag,
    #                                                   elementType = newShapeIndexedName.elementType,
    #                                                   linkedNames = [baseShape.elementMap.getMappedName(sourceName).copy()],
    #                                                   index = i,
    #                                                   totalNumberOfSectionElements = len(newShapes),
    #                                                   ancestors = [])
    #                                     ]
    #         ).copy()

    #         newShape = returnShape.getElement(newShapeIndexedName)
    #         faceEdges = returnShape.getSubElementsOfChild(newShape, "Edge")

    #         for edgeI, edge in enumerate(faceEdges):
    #             edgeIndexedName = returnShape.getIndexedNameOfShape(edge)

    #             if not returnShape.elementMap.hasIndexedName(edgeIndexedName):
    #                 newEdgeMappedName = MappedName([MappedSection(opCode = OpCode.DRESSUP,
    #                                                           mapModifier = MapModifier.REMAP,
    #                                                           iterationTag = returnShape.tag,
    #                                                           elementType = "Edge",
    #                                                           linkedNames = [newMappedName.copy()],
    #                                                           index = edgeI,
    #                                                           totalNumberOfSectionElements = len(faceEdges),
    #                                                           ancestors = [])
    #                                            ]
    #                 ).copy()

    #                 edgeVertexes = returnShape.getSubElementsOfChild(edge, "Vertex")

    #                 for vertexI, vertex in enumerate(edgeVertexes):
    #                     vertexIndexedName = returnShape.getIndexedNameOfShape(vertex)

    #                     if not returnShape.elementMap.hasIndexedName(vertexIndexedName):
    #                         newVertexMappedName = MappedName([MappedSection(opCode = OpCode.DRESSUP,
    #                                                                         mapModifier = MapModifier.REMAP,
    #                                                                         iterationTag = returnShape.tag,
    #                                                                         elementType = "Vertex",
    #                                                                         linkedNames = [newEdgeMappedName.copy()],
    #                                                                         index = vertexI,
    #                                                                         totalNumberOfSectionElements = len(edgeVertexes),
    #                                                                         ancestors = [])
    #                                                          ]
    #                         ).copy()

    #                         returnShape.elementMap.setElement(vertexIndexedName, newVertexMappedName)

    #                 returnShape.elementMap.setElement(edgeIndexedName, newEdgeMappedName)

    #         returnShape.elementMap.setElement(newShapeIndexedName, newMappedName)

    PerformanceTimer.GlobalTimer.pauseKey("Dressup")

    return returnShape

def makeMappedCompound(compoundShapes: List[TShape], tag: int = 0):
    builder = BRep_Builder()
    compound = TopoDS_Compound()

    builder.MakeCompound(compound)

    for shape in compoundShapes:
        builder.Add(compound, shape.getOCCTShape())
    
    returnShape = TShape(compound, ElementMap())
    returnShape.tag = tag

    for shape in compoundShapes:
        mapSubElement(returnShape, shape)
    
    return returnShape

def makeMappedThickness(baseShape: TShape, faces: List[IndexedName], offset: int, tag: int = 0):
    PerformanceTimer.GlobalTimer.addKey("Thickness")

    baseShape.buildCache()

    facesShapes = TopTools_ListOfShape()

    for element in faces:
        if element.elementType == "Face":
            facesShapes.Append(baseShape.getElement(element))
    
    maker = BRepOffsetAPI_MakeThickSolid()
    maker.MakeThickSolidByJoin(
        baseShape.getOCCTShape(),
        facesShapes,
        offset,
        1e-4,
    )

    maker.Build()

    returnShape = TShape(maker.Shape(), ElementMap())
    returnShape.tag = tag
    returnShape.buildCache()

    mapSubElement(returnShape, baseShape)

    # generatedShapes = ShapeHistoryList(0)
    # modifiedShapes = ShapeHistoryList(1)

    # for indexedNameStr, subElement in baseShape.getShapeMap().items():
    #     indexedName = IndexedName.fromString(indexedNameStr)
    #     indexedName.parentIdentifier = baseShape.tag

    #     generatedShapes.extendList(indexedName,
    #                                maker.Generated(subElement),
    #                                returnShape)

    # for indexedNameStr, subElement in baseShape.getShapeMap().items():
    #     indexedName = IndexedName.fromString(indexedNameStr)
    #     indexedName.parentIdentifier = baseShape.tag

    #     modifiedShapes.extendList(indexedName,
    #                               maker.Modified(subElement),
    #                               returnShape)
        
    # generatedShapes.updateReverseList()
        
    # for sourceName, newShapes in modifiedShapes.historyList.items():
    #     for i, newShapeIndexedName in enumerate(newShapes):
    #         if returnShape.elementMap.hasIndexedName(newShapeIndexedName): continue

    #         newMappedName = baseShape.elementMap.getMappedName(sourceName).copy()
            
    #         newMappedName.mappedSections.append(MappedSection(opCode = OpCode.THICKNESS,
    #                                                           mapModifier = MapModifier.REMAP,
    #                                                           iterationTag = returnShape.tag,
    #                                                           elementType = newShapeIndexedName.elementType,
    #                                                           index = i,
    #                                                           totalNumberOfSectionElements = len(newShapes),
    #                                                           ancestors = [])
    #         )

    #         returnShape.elementMap.setElement(newShapeIndexedName, newMappedName)
    
    # for newShapeIndexedName, sourceShapeNames in generatedShapes.reverseHistoryList.items():
    #     mappedNames = []
    #     if returnShape.elementMap.hasIndexedName(newShapeIndexedName): continue

    #     for indexedName in sourceShapeNames:
    #         mappedNames.append(baseShape.elementMap.getMappedName(indexedName))

    #     if len(mappedNames) > 0:
    #         returnShape.elementMap.setElement(newShapeIndexedName, MappedName([MappedSection(opCode = OpCode.THICKNESS,
    #                                                                            mapModifier = MapModifier.MERGE,
    #                                                                            iterationTag = returnShape.tag,
    #                                                                            linkedNames = mappedNames,
    #                                                                            elementType = newShapeIndexedName.elementType)]
    #             )
    #         )
    
    # unmappedEdges = []

    # for name, _ in returnShape.getShapeMap().items():
    #     nameFormatted = IndexedName.fromString(name)

    #     if not returnShape.elementMap.hasIndexedName(nameFormatted):
    #         unmappedEdges.append(nameFormatted)

    # for edge in unmappedEdges:
    #     edgeShape = returnShape.shapeMap[edge.toString()]
    #     faceAncestors = returnShape.getAncestorsOfType(edgeShape, "Face")
    #     linkedNames = []

    #     for face in faceAncestors:
    #         faceIndexedName = returnShape.getIndexedNameOfShape(face)

    #         if returnShape.elementMap.hasIndexedName(faceIndexedName):
    #             faceMappedName = returnShape.elementMap.getMappedName(faceIndexedName)

    #             if faceMappedName not in linkedNames:
    #                 linkedNames.append(faceMappedName)
        
    #     if len(linkedNames) > 0:
    #         returnShape.elementMap.setElement(edge, MappedName([MappedSection(opCode = OpCode.THICKNESS,
    #                                                                           mapModifier = MapModifier.MERGE,
    #                                                                           iterationTag = returnShape.tag,
    #                                                                           linkedNames = linkedNames,
    #                                                                           elementType = newShapeIndexedName.elementType).copy()]
    #             )
    #         )

    # PerformanceTimer.GlobalTimer.pauseKey("Thickness")
    
    return returnShape

def makeMappedExtrusion(supportTShape: TShape, direction: App.Vector, tag: int = 0):
    PerformanceTimer.GlobalTimer.addKey("Extrusion")
    vec = gp_Vec(direction.x, direction.y, direction.z)
    maker = BRepPrimAPI_MakePrism(supportTShape.getOCCTShape(), vec)
    maker.Build()

    supportTShape.buildShapeMap()
    supportTShape.tag = tag

    extrusionTShape = TShape(sourceShape = maker.Shape(), elementMap = ElementMap())
    extrusionTShape.tag = tag
    extrusionTShape.buildCache()

    mapPrismLikeShape(supportTShape, extrusionTShape, OpCode.EXTRUSION)
    PerformanceTimer.GlobalTimer.pauseKey("Extrusion")

    return extrusionTShape

def makeMappedBooleanOperation(baseShape: TShape, operatorShape: TShape, booleanType: BooleanType, tag: int = 0):
    maker = None

    if booleanType == BooleanType.FUSE:
        maker = BRepAlgoAPI_Fuse(baseShape.getOCCTShape(), operatorShape.getOCCTShape())
    elif booleanType == BooleanType.CUT:
        maker = BRepAlgoAPI_Cut(baseShape.getOCCTShape(), operatorShape.getOCCTShape())
    elif booleanType == BooleanType.INTERSECTION:
        maker = BRepAlgoAPI_Common(baseShape.getOCCTShape(), operatorShape.getOCCTShape())

    maker.Build()

    returnShape = TShape(maker.Shape(), ElementMap())
    returnShape.tag = tag
    returnShape.buildCache()

    mapSubElement(returnShape, operatorShape)
    mapSubElement(returnShape, baseShape)

    generatedShapes = ShapeHistoryList(0)
    modifiedShapes = ShapeHistoryList(1)

    for shape in [baseShape, operatorShape]:
        for indexedNameStr, subElement in shape.getShapeMap().items():
            indexedName = IndexedName.fromString(indexedNameStr)
            indexedName.parentIdentifier = shape.tag

            generatedShapes.extendList(indexedName,
                                      maker.Generated(subElement),
                                      returnShape)
    
    for shape in [baseShape, operatorShape]:
        for indexedNameStr, subElement in shape.getShapeMap().items():
            indexedName = IndexedName.fromString(indexedNameStr)
            indexedName.parentIdentifier = shape.tag

            modifiedShapes.extendList(indexedName,
                                      maker.Modified(subElement),
                                      returnShape)
    
    generatedShapes.updateReverseList()
    modifiedShapes.updateReverseList()

    for sourceName, newShapes in modifiedShapes.historyList.items():
        for i, newShapeIndexedName in enumerate(newShapes):
            if returnShape.elementMap.hasIndexedName(newShapeIndexedName): continue

            newMappedName = None

            if sourceName.parentIdentifier == baseShape.tag:
                newMappedName = baseShape.elementMap.getMappedName(sourceName).copy()
            elif sourceName.parentIdentifier == operatorShape.tag:
                newMappedName = operatorShape.elementMap.getMappedName(sourceName).copy()

            newMappedName.setIndex(i)
            returnShape.elementMap.setElement(newShapeIndexedName, newMappedName)

    for newShapeIndexedName, sourceShapeNames in generatedShapes.reverseHistoryList.items():
        mappedNames = []
        if returnShape.elementMap.hasIndexedName(newShapeIndexedName): continue

        for name in sourceShapeNames:
            mappedName = None

            if name.parentIdentifier == baseShape.tag:
                mappedName = baseShape.elementMap.getMappedName(name)
            elif name.parentIdentifier == operatorShape.tag:
                mappedName = operatorShape.elementMap.getMappedName(name)
            
            mappedNames.append(mappedName.toString())

        if len(mappedNames) > 0:
            returnShape.elementMap.setElement(newShapeIndexedName, MappedName.makeName(referenceNames = mappedNames,
                                                                                       initialTag = returnShape.tag,
                                                                                       mapperInfo = "BGG")
            )

    return (returnShape, maker, generatedShapes, modifiedShapes)

def colorElementsFromSupport(obj, shape: Part.Shape, elementMap: ElementMap):
    edgeColors =   [(1.0, 0.0, 0.0)] * len(shape.Edges)
    faceColors   = [(1.0, 0.0, 0.0)] * len(shape.Faces)
    vertexColors = [(1.0, 0.0, 0.0)] * len(shape.Vertexes)

    for i, _ in enumerate(shape.Edges):
        edgeName = f"Edge{i + 1}"

        if elementMap.hasIndexedName(IndexedName.fromString(edgeName)):
            edgeColors[i] = (0.0, 1.0, 0.0)

    for i, _ in enumerate(shape.Faces):
        faceName = f"Face{i + 1}"

        if elementMap.hasIndexedName(IndexedName.fromString(faceName)):
            faceColors[i] = (0.0, 1.0, 0.0)
    
    for i, _ in enumerate(shape.Vertexes):
        vertexName = f"Vertex{i + 1}"

        if elementMap.hasIndexedName(IndexedName.fromString(vertexName)):
            vertexColors[i] = (0.0, 1.0, 0.0)

    obj.ViewObject.LineColorArray = edgeColors
    obj.ViewObject.DiffuseColor = faceColors
    obj.ViewObject.PointColorArray = vertexColors

def mapSubElement(baseShape: TShape, sourceShape: TShape, newInitialTag = None):
    if sourceShape.getShapeMap() == {}: sourceShape.buildShapeMap()
    if baseShape.getShapeMap() == {}: baseShape.buildShapeMap()

    for sIndexedNameStr, sShape in sourceShape.getShapeMap().items():
        for bIndexedNameStr, bShape in baseShape.getShapeMap().items():
            if sShape.IsSame(bShape):
                baseIndexedName = IndexedName.fromString(bIndexedNameStr)

                sourceName = sourceShape.elementMap.getMappedName(IndexedName.fromString(sIndexedNameStr))

                if len(sourceName.toString()) != 0:
                    newName = sourceName.copy()

                    if newInitialTag != None:
                        newName.setInitialTag(newInitialTag)
                    
                    baseShape.elementMap.setElement(baseIndexedName, newName)

def getNameOfElement(elementShape, shape):
    if isinstance(elementShape, Part.Vertex):
        for i, vertex in enumerate(shape.Vertexes):
            if elementShape.isSame(vertex):
                return f"Vertex{i + 1}"
    elif isinstance(elementShape, Part.Edge):
        for i, edge in enumerate(shape.Edges):
            if elementShape.isSame(edge):
                return f"Edge{i + 1}"
    elif isinstance(elementShape, Part.Face):
        for i, face in enumerate(shape.Faces):
            if elementShape.isSame(face):
                return f"Face{i + 1}"

def getFaceOfSketch(sketch):
    elementMap = ElementMap()
    vertexesMap = {}
    facesMap = {}

    sketchWires = list(filter(lambda w: w.isClosed(), sketch.Shape.Wires))

    try:
        supportFace = Part.makeFace(sketchWires)
    except:
        supportFace = None
    
    if supportFace != None:
        supportFace.Placement = sketch.Placement.inverse()

        for geoF in sketch.GeometryFacadeList:
            geom = geoF.Geometry
            geomShape = geom.toShape()

            if geom.TypeId != "Part::GeomPoint":
                for i, edge in enumerate(supportFace.Edges):
                    if edge.Curve.isSame(geomShape.Curve, 1e-6, 1e-6):
                        name = MappedName.makeName(referenceIDs = [f"g{geoF.Id}"],
                                                   initialTag = sketch.ID,
                                                   elementType = "E",
                                                   mapperInfo = "SRC")
                        
                        name.packageReferenceIDs()
                        elementMap.setElement(IndexedName.fromString(f"Edge{i + 1}"), name)

                        if len(edge.Vertexes) > 1:
                            for vertex in edge.Vertexes:
                                vertexName = getNameOfElement(vertex, supportFace)

                                if vertexName != None:
                                    if vertexName not in vertexesMap:
                                        vertexesMap[vertexName] = []
                                    
                                    if vertex.Point.isEqual(geom.StartPoint, 1e-6):
                                        vertexesMap[vertexName].append(f"g{geoF.Id}v1")

                                    if vertex.Point.isEqual(geom.EndPoint, 1e-6):
                                        vertexesMap[vertexName].append(f"g{geoF.Id}v2")
                        elif len(edge.Vertexes) == 1:
                            vertexName = getNameOfElement(edge.Vertexes[0], supportFace)
                            
                            if vertexName != None:
                                vertexesMap[vertexName] = []

                            vertexesMap[vertexName].append(f"g{geoF.Id}v1")
    
        for vertexName, IDs in vertexesMap.items():
            if len(IDs) != 0:
                name = MappedName.makeName(referenceIDs = IDs,
                                           initialTag = sketch.ID,
                                           elementType = "V",
                                           mapperInfo = "SRC")
                
                name.packageReferenceIDs()
                elementMap.setElement(IndexedName.fromString(vertexName), name)
        
        for face in supportFace.Faces:
            faceName = getNameOfElement(face, supportFace)

            for faceEdge in face.Edges:
                faceEdgeName = getNameOfElement(faceEdge, supportFace)

                if elementMap.hasIndexedName(IndexedName.fromString(faceEdgeName)):
                    if faceName not in facesMap:
                        facesMap[faceName] = []
                    
                    facesMap[faceName].extend(elementMap.getMappedName(IndexedName.fromString(faceEdgeName)).referenceIDs())
        
        for faceName, IDs in facesMap.items():
            name = MappedName.makeName(referenceIDs = IDs,
                                       initialTag = sketch.ID,
                                       elementType = "F",
                                       mapperInfo = "SRC")
                
            name.packageReferenceIDs()
            elementMap.setElement(IndexedName.fromString(faceName), name)

        supportFace.Placement = App.Placement()
        tSupportFace = TShape(supportFace, elementMap)

        return tSupportFace
    else:
        return TShape()
