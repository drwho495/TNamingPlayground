import sys
import os
import copy

sys.path.append(os.path.dirname(__file__))

from Data.IndexedName import IndexedName
from Data.MappedName import MappedName
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX
from Data.DataEnums import *

def IDsCheck(idList1, idList2):
    return len(list(set(idList1) & set(idList2))) >= 2

def sortLists(list1: list, list2: list):
    if len(list1) < len(list2):
        return (list2, list1)
    else:
        return (list1, list2)

def complexCompare(searchName, searchShape, oldShape, loopName, allowVaryingHistory = True, recursionList = [], debugCheckName = None):
    searchSections = searchName.toSections()
    loopSections = loopName.toSections()

    for searchI, searchSection in enumerate(searchSections):
        searchSectionTag = MappedName.stringGetTag(searchSection)
        searchSectionOpCode = MappedName.stringGetOpCode(searchSection)

        for loopI, loopSection in enumerate(loopSections):
            checkSections = False
            loopSectionTag = MappedName.stringGetTag(loopSection)
            loopSectionOpCode = MappedName.stringGetOpCode(loopSection)

            if searchSection == loopSection:
                continue

            if (searchSectionTag == loopSectionTag
                and searchSectionOpCode == loopSectionOpCode
            ):
                checkSections = True

            if searchI == 0 and loopI == 0 :
                checkSections = True
            
            if checkSections:
                if not IDsCheck(MappedName.stringGetIDs(loopSection), MappedName.stringGetIDs(searchSection)):
                    return False
                
                nameOccurences = 0
                occurenceMin = 1
                searchRefNames = MappedName.stringGetNames(searchSection)

                for loopRefName in MappedName.stringGetNames(loopSection):
                    for searchRefName in searchRefNames:
                        if loopRefName == searchRefName or complexCompare(searchRefName, searchShape, oldShape, loopRefName):
                            nameOccurences += 1
                            
                            if nameOccurences >= occurenceMin:
                                break
                
                if (nameOccurences < occurenceMin
                    or searchSectionTag != loopSectionTag
                    or searchSectionOpCode != loopSectionOpCode
                    or MappedName.stringGetIndex(loopSection) != MappedName.stringGetIndex(searchSection)
                    or MappedName.stringGetElementType(loopSection) != MappedName.stringGetElementType(searchSection)
                    or MappedName.stringGetDuplicateCount(loopSection) != MappedName.stringGetDuplicateCount(searchSection)
                    or MappedName.stringGetMapperInfo(loopSection) != MappedName.stringGetMapperInfo(searchSection)
                ):
                    return False
    
    return True
    
def searchForSimilarNames(searchName, searchShape, oldShape = None, allowVaryingHistory = True, debugCheckName = None):
    foundNames = []

    for loopMappedName, loopIndexedName in searchShape.elementMap.internalMap.items():
        if searchName.toString() == loopMappedName.toString() or complexCompare(searchName, searchShape, oldShape, loopMappedName, allowVaryingHistory, [], debugCheckName):
            foundNames.append((loopMappedName, loopIndexedName))
    
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