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
    returnShape.tag = tag
    returnShape.buildCache()

    generatedShapes = ShapeHistoryList(0)
    modifiedShapes = ShapeHistoryList(1)
    history = maker.History()

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

    mapShapeHistory(returnShape, "RFI", [shape], generatedShapes, modifiedShapes)

    PerformanceTimer.GlobalTimer.pauseKey("Refine")

    return returnShape

def mapShapeHistory(mapShape: TShape, opCode: str, sourceShapes: List[TShape], generatedShapes: ShapeHistoryList, modifiedShapes: ShapeHistoryList):
    for sourceShape in sourceShapes:
        mapSubElement(mapShape, sourceShape)

    for sourceName, newShapes in modifiedShapes.historyList.items():
        for i, newShapeIndexedName in enumerate(newShapes):
            newMappedName = None

            for sourceShape in sourceShapes:
                if sourceName.parentIdentifier == sourceShape.tag:
                    newMappedName = sourceShape.elementMap.getMappedName(sourceName)
                    
                    if newMappedName != None:
                        newMappedName = newMappedName.copy()

            if newMappedName != None:
                if len(newShapes) > 1:
                    newMappedName.addSection(MappedName.makeSection(index = i, operationCode = opCode, elementType = newShapeIndexedName.elementType[0]))

                mapShape.elementMap.setElement(newShapeIndexedName, newMappedName)

    for newShapeIndexedName, sourceShapeNames in generatedShapes.reverseHistoryList.items():
        mappedNames = []
        if mapShape.elementMap.hasIndexedName(newShapeIndexedName): continue

        for name in sourceShapeNames:
            mappedName = None

            for sourceShape in sourceShapes:
                if name.parentIdentifier == sourceShape.tag:
                    mappedName = sourceShape.elementMap.getMappedName(name)
            
                    if mappedName != None:
                        mappedName = mappedName.copy()

            if mappedName != None:
                mappedNames.append(mappedName.toString())

        if len(mappedNames) > 0:
            if len(newShapeIndexedName.elementType) != 0:
                newName = MappedName.makeName([MappedName.makeSection(referenceNames = mappedNames,
                                                                    iterationTag = mapShape.tag,
                                                                    elementType = newShapeIndexedName.elementType[0],
                                                                    operationCode = opCode)])

                mapShape.elementMap.setElement(newShapeIndexedName, newName)

    # let's try to map anything that wasn't caught with Modified or Generated with by finding partner elements

    elementTypeMap = {"Edge": "Face", "Vertex": "Edge", "Face": "Edge"}

    for elementNameStr, elementShape in mapShape.getShapeMap().items():
        mapped = False
        elementName = IndexedName.fromString(elementNameStr)

        if not mapShape.elementMap.hasIndexedName(elementName):
            for elementMappedName, elementShape2 in mapShape.getIDShapeMap().items():
                if elementShape.IsPartner(elementShape2):
                    if len(elementName.elementType) != 0:
                        newName = MappedName.makeName([MappedName.makeSection(referenceNames = [elementMappedName.toString()],
                                                                              iterationTag = mapShape.tag,
                                                                              elementType = elementName.elementType[0],
                                                                              operationCode = opCode)])
                        
                        mapShape.elementMap.setElement(elementName, newName)
                        mapped = True
                        break
            
            if mapped: continue

            ancestors = mapShape.getAncestorsOfType(elementShape, elementTypeMap[elementName.elementType])
            names = []

            for ancestor in ancestors:
                ancestorIndexedName = mapShape.getIndexedNameOfShape(ancestor)

                if mapShape.elementMap.hasIndexedName(ancestorIndexedName):
                    ancestorMappedName = mapShape.elementMap.getMappedName(ancestorIndexedName)

                    names.append(ancestorMappedName.toString())
            
            if len(names) > 0:
                newName = MappedName.makeName([MappedName.makeSection(referenceNames = names,
                                                                      iterationTag = mapShape.tag,
                                                                      elementType = elementName.elementType[0],
                                                                      operationCode = opCode)])
                mapShape.elementMap.setElement(elementName, newName)

                # if elementName.elementType == "Edge":
                #     vertexes = mapShape.getSubElementsOfChild(elementShape, "Vertex")

                #     for i, vertex in enumerate(vertexes):
                #         vertexIndexName = mapShape.getIndexedNameOfShape(vertex)

                #         if mapShape.elementMap.hasIndexedName(vertexIndexName):
                #             section = newName.toSections()[0]
                #             section = MappedName.stringSetSectionData(section, 4, str(i))
                #             section = MappedName.stringSetSectionData(section, 5, vertexIndexName.elementType[0])

                #             mapShape.elementMap.setElement(vertexIndexName, MappedName(section))

    return mapShape

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
    
    generatedShapes.updateReverseList()
    modifiedShapes.updateReverseList()

    returnShape = mapShapeHistory(returnShape, "DSP", [baseShape], generatedShapes, modifiedShapes)
    
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
        
    generatedShapes.updateReverseList()
    modifiedShapes.updateReverseList()

    returnShape = mapShapeHistory(returnShape, "THK", [baseShape], generatedShapes, modifiedShapes)
        
    return returnShape

def makeMappedExtrusion(supportTShape: TShape, direction: App.Vector, tag: int = 0):
    PerformanceTimer.GlobalTimer.addKey("Extrusion")
    vec = gp_Vec(direction.x, direction.y, direction.z)
    maker = BRepPrimAPI_MakePrism(supportTShape.getOCCTShape(), vec)
    maker.Build()

    supportTShape.buildShapeMap()
    supportTShape.tag = -tag

    extrusionTShape = TShape(sourceShape = maker.Shape(), elementMap = ElementMap())
    extrusionTShape.tag = tag
    extrusionTShape.buildCache()

    generatedShapes = ShapeHistoryList(0)
    modifiedShapes = ShapeHistoryList(1)

    for indexedNameStr, subElement in supportTShape.getShapeMap().items():
        indexedName = IndexedName.fromString(indexedNameStr)
        indexedName.parentIdentifier = supportTShape.tag

        generatedShapes.extendList(indexedName,
                                   maker.Generated(subElement),
                                   extrusionTShape)

    for indexedNameStr, subElement in supportTShape.getShapeMap().items():
        indexedName = IndexedName.fromString(indexedNameStr)
        indexedName.parentIdentifier = supportTShape.tag

        modifiedShapes.extendList(indexedName,
                                  maker.Modified(subElement),
                                  extrusionTShape)

    modifiedShapes.updateReverseList()
    generatedShapes.updateReverseList()

    extrusionTShape = mapShapeHistory(extrusionTShape, "XTR", [supportTShape], generatedShapes, modifiedShapes)
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

    mapShapeHistory(returnShape, "BOL", [baseShape, operatorShape], generatedShapes, modifiedShapes)

    return (returnShape,)

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

                if sourceName != None and len(sourceName.toString()) != 0:
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
                        name = MappedName.makeName([MappedName.makeSection(referenceIDs = [f"g{geoF.Id}"],
                                                                           iterationTag = sketch.ID,
                                                                           operationCode = "SKT",
                                                                           elementType = "E")])
                        
                        # name.packageReferenceIDs()
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
                name = MappedName.makeName([MappedName.makeSection(referenceIDs = IDs,
                                                                   iterationTag = sketch.ID,
                                                                   operationCode = "SKT",
                                                                   elementType = "V")])
                
                # name.packageReferenceIDs()
                elementMap.setElement(IndexedName.fromString(vertexName), name)
        
        for face in supportFace.Faces:
            faceName = getNameOfElement(face, supportFace)

            for faceEdge in face.Edges:
                faceEdgeName = IndexedName.fromString(getNameOfElement(faceEdge, supportFace))

                if elementMap.hasIndexedName(faceEdgeName):
                    if faceName not in facesMap:
                        facesMap[faceName] = []
                    
                    facesMap[faceName].extend(elementMap.getMappedName(faceEdgeName).masterIDs())
        
        for faceName, IDs in facesMap.items():
            name = MappedName.makeName([MappedName.makeSection(referenceIDs = IDs,
                                                               iterationTag = sketch.ID,
                                                               operationCode = "SKT",
                                                               elementType = "F")])
                
            # name.packageReferenceIDs()
            elementMap.setElement(IndexedName.fromString(faceName), name)

        supportFace.Placement = App.Placement()
        tSupportFace = TShape(supportFace, elementMap)

        return tSupportFace
    else:
        return TShape()
