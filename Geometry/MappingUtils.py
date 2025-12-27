import sys
import os
import copy

sys.path.append(os.path.dirname(__file__))

from Data.IndexedName import IndexedName
from Data.MappedName import MappedName
from Data.MappedSection import MappedSection
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX
from Data.DataEnums import *

def getNewHistoryCount(mappedName: MappedName):
    count = 0

    for section in mappedName.mappedSections:
        if section.historyModifier == HistoryModifier.NEW:
            count += 1
    
    return count

def masterIDsCheck(name1: MappedName, name2: MappedName):
    return len(list(set(name1.masterIDs()) & set(name2.masterIDs()))) >= 2

def sortLists(list1: list, list2: list):
    if len(list1) < len(list2):
        return (list2, list1)
    else:
        return (list1, list2)

def complexCompare(searchName, searchShape, oldShape, loopName, allowVaryingHistory = True, recursionList = [], debugCheckName = None):
    # if loopName == searchName:
        # return True
    
    if getNewHistoryCount(searchName) != getNewHistoryCount(loopName):
        if loopName == debugCheckName: print("New history count failure.")
        return False
    
    if len(loopName.mappedSections) == 0:
        return False
    
    if len(searchName.mappedSections) != len(loopName.mappedSections) and not allowVaryingHistory:
        if loopName == debugCheckName: print("Section size mismatch.")
        return False

    if searchName.masterIDs() == loopName.masterIDs() or masterIDsCheck(loopName, searchName):
        largerList, smallerList = sortLists(searchName.mappedSections, loopName.mappedSections)

        for i, section1 in enumerate(largerList):
            if len(smallerList) <= i:
                break

            section2 = smallerList[i]

            if section1.iterationTag != section2.iterationTag:
                continue

            simpleSectionCheck =   (section1.opCode          == section2.opCode
                                and section1.historyModifier == section2.historyModifier
                                and section1.mapModifier     == section2.mapModifier
                                and section1.elementType     == section2.elementType
                                and section1.index           == section2.index)
            
            if simpleSectionCheck and len(section1.linkedNames) == len(section2.linkedNames):
                for i, linkedName1 in enumerate(section1.linkedNames):
                    linkedName2 = section2.linkedNames[i]

                    if linkedName1 != linkedName2 and not complexCompare(linkedName1, searchShape, oldShape, linkedName2, allowVaryingHistory, [], debugCheckName):
                        return False
            else:
                return False
        
        return True
    else:
        return False
    
def searchForSimilarNames(searchName, searchShape, oldShape, allowVaryingHistory = True, debugCheckName = None):
    foundNames = []

    for loopIndexedNameString, loopMappedName in searchShape.elementMap.internalMap.items():
        if complexCompare(searchName, searchShape, oldShape, loopMappedName, allowVaryingHistory, [], debugCheckName):
            foundNames.append(IndexedName.fromString(loopIndexedNameString))
    
    return foundNames

def getElementTypeName(occtTypeIndex):
    if occtTypeIndex == 4:
        return "Face"
    elif occtTypeIndex == 6:
        return "Edge"
    elif occtTypeIndex == 7:
        return "Vertex"

def getElementTypeIndex(typeName: str):
    if typeName == "Face":
        return 4
    elif typeName == "Edge":
        return 6
    elif typeName == "Vertex":
        return 7
    
def occtLOStoList(listOfShapes):
    returnList = []

    while listOfShapes.Size() > 0:
        returnList.append(listOfShapes.First())
        listOfShapes.RemoveFirst()
    
    return returnList

def addAncestorsToSection(mappedSection: MappedSection, elementTShape, parentTShape):
    from Geometry.TShape import TShape # include here to avoid cyclical import

    ancestors = []
    elementIndexedName = parentTShape.getIndexedNameOfShape(elementTShape)

    if elementTShape.ShapeType() == TopAbs_EDGE:
        vertexes = parentTShape.getSubElementsOfChild(elementTShape, "Vertex")

        for vertex in vertexes:
            edgeAncestors = parentTShape.getAncestorsOfType(vertex, "Edge")

            for edge in edgeAncestors:
                edgeIndexedName = parentTShape.getIndexedNameOfShape(edge).toString()

                if edgeIndexedName not in ancestors and edgeIndexedName != elementIndexedName.toString():
                    ancestors.append(edgeIndexedName)
    elif elementTShape.ShapeType() == TopAbs_FACE:
        edges = parentTShape.getSubElementsOfChild(elementTShape, "Edge")

        for edge in edges:
            faceAncestors = parentTShape.getAncestorsOfType(edge, "Face")

            for face in faceAncestors:
                faceIndexedName = parentTShape.getIndexedNameOfShape(face).toString()

                if faceIndexedName not in ancestors and faceIndexedName != elementIndexedName.toString():
                    ancestors.append(faceIndexedName)
    elif elementTShape.ShapeType() == TopAbs_VERTEX:
        edges = parentTShape.getSubElementsOfChild(elementTShape, "Edge")

        for edge in edges:
            edgeIndexedName = parentTShape.getIndexedNameOfShape(edge).toString()

            if edgeIndexedName not in ancestors and edgeIndexedName != elementIndexedName.toString():
                ancestors.append(edgeIndexedName)
    
    mappedSection.ancestors = ancestors