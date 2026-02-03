import sys
import os
import copy

sys.path.append(os.path.dirname(__file__))

from Data.IndexedName import IndexedName
from Data.MappedName import MappedName
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX
from Data.DataEnums import *

def masterIDsCheck(name1: MappedName, name2: MappedName):
    return len(list(set(name1.referenceIDs()) & set(name2.referenceIDs()))) >= 2

def sortLists(list1: list, list2: list):
    if len(list1) < len(list2):
        return (list2, list1)
    else:
        return (list1, list2)

def complexCompare(searchName, searchShape, oldShape, loopName, allowVaryingHistory = True, recursionList = [], debugCheckName = None):
    # searchName = searchName.copy()
    # loopName = loopName.copy()

    # if len(loopName.mappedSections) == 0:
    #     return False
    
    # if len(searchName.mappedSections) != len(loopName.mappedSections) and not allowVaryingHistory:
    #     if loopName == debugCheckName: print("Section size mismatch.")
    #     return False
    
    # namesList = [loopName, searchName]
    # namesListReverse = [searchName, loopName]
    
    # for i, mainName in enumerate(namesList):
    #     otherName = namesListReverse[i]
    #     mainCopy = mainName.copy()

    #     for sectionI, mainSection in enumerate(mainName.mappedSections):
    #         if len(mainSection.deletedNames) != 0:
    #             for deletedName in mainSection.deletedNames:
    #                 extendedDeletedName = deletedName.copy()

    #                 if (len(mainName.mappedSections) - 1) != i:
    #                     extendedDeletedName.mappedSections.extend(mainCopy.mappedSections[(sectionI + 1):])

    #                 if complexCompare(extendedDeletedName, searchShape, oldShape, otherName, allowVaryingHistory = allowVaryingHistory):
    #                     return True

    # if searchName.masterIDs() == loopName.masterIDs() or masterIDsCheck(loopName, searchName):
    #     largestList, _ = sortLists(searchName.mappedSections, loopName.mappedSections)

    #     for i in range(0, len(largestList)):
    #         if len(loopName.mappedSections) <= i or len(searchName.mappedSections) <= i:
    #             break

    #         searchSection = searchName.mappedSections[i]
    #         loopSection = loopName.mappedSections[i]

    #         if searchSection.iterationTag != loopSection.iterationTag:
    #             if i == 0:
    #                 # the first sections in names MUST be the same!
    #                 return False

    #             if searchSection.iterationTag in loopName.getIterationTags():
    #                 newMappedSections = loopName.copy().mappedSections
    #                 sectionI = i

    #                 while len(newMappedSections) > (sectionI + 1):
    #                     loopSectionCopy = newMappedSections[sectionI]

    #                     if loopSectionCopy.iterationTag != searchSection.iterationTag:
    #                         newMappedSections.remove(loopSectionCopy)
    #                     else:
    #                         break
                    
    #                 loopName.mappedSections = newMappedSections
    #                 loopSection = loopName.mappedSections[i]
    #             elif loopSection.iterationTag in searchName.getIterationTags():
    #                 newMappedSections = searchName.copy().mappedSections
    #                 sectionI = i

    #                 while len(newMappedSections) > sectionI:
    #                     searchSectionCopy = newMappedSections[sectionI]

    #                     if searchSectionCopy.iterationTag != loopSection.iterationTag:
    #                         newMappedSections.remove(searchSectionCopy)
    #                     else:
    #                         break
                    
    #                 searchName.mappedSections = newMappedSections
    #                 searchSection = searchName.mappedSections[i]

    #         simpleSectionCheck =   (searchSection.opCode          == loopSection.opCode
    #                             and searchSection.mapModifier     == loopSection.mapModifier
    #                             and searchSection.elementType     == loopSection.elementType)
            
    #         if simpleSectionCheck and len(searchSection.linkedNames) == len(loopSection.linkedNames):
    #             if searchSection.opCode == OpCode.BOOLEAN:
    #                 if loopSection.forkedElement and searchSection.forkedElement:
    #                     indexPass = False
                
    #                     searchSectionFirstElement = searchSection.index == 0
    #                     searchSectionLastElement = ((searchSection.index + 1) / searchSection.totalNumberOfSectionElements) == 1
    #                     searchSectionHalfElement =  (searchSection.totalNumberOfSectionElements > 1 
    #                                                 and (searchSection.index / (searchSection.totalNumberOfSectionElements - 1)) == .5)
                        
    #                     loopSectionFirstElement = loopSection.index == 0
    #                     loopSectionLastElement = ((loopSection.index + 1) / loopSection.totalNumberOfSectionElements) == 1
    #                     loopSectionHalfElement =  (loopSection.totalNumberOfSectionElements > 1 
    #                                                 and (loopSection.index / (loopSection.totalNumberOfSectionElements - 1)) == .5)

    #                     if loopSectionHalfElement and searchSectionHalfElement:
    #                         indexPass = True
    #                     elif ((loopSectionLastElement and searchSectionLastElement) 
    #                         or (loopSectionFirstElement and searchSectionFirstElement)
    #                     ):
    #                         indexPass = True
    #                     elif (searchSection.totalNumberOfSectionElements > 1 
    #                         and loopSection.totalNumberOfSectionElements > 1 
    #                         and (searchSection.index / (searchSection.totalNumberOfSectionElements - 1)) < .5
    #                         and (loopSection.index / (loopSection.totalNumberOfSectionElements - 1)) < .5
    #                         and searchSection.index == loopSection.index
    #                     ):
    #                         indexPass = True
    #                     elif (searchSection.totalNumberOfSectionElements > 1 
    #                         and loopSection.totalNumberOfSectionElements > 1 
    #                         and (searchSection.totalNumberOfSectionElements - 1) % 2 == 0
    #                         and (loopSection.totalNumberOfSectionElements - 1) % 2 == 0
    #                         and (searchSection.index / (searchSection.totalNumberOfSectionElements - 1)) > .5
    #                         and (loopSection.index / (loopSection.totalNumberOfSectionElements - 1)) > .5
    #                         and ((searchSection.index - ((searchSection.totalNumberOfSectionElements - 1) / 2)) 
    #                             == (loopSection.index - ((loopSection.totalNumberOfSectionElements - 1) / 2)))
    #                     ):
    #                         indexPass = True
    #                     elif (not loopSectionLastElement 
    #                         and not searchSectionLastElement
    #                         and not loopSectionFirstElement
    #                         and not searchSectionFirstElement
    #                         and not loopSectionHalfElement
    #                         and not searchSectionHalfElement
    #                         and loopSection.index == searchSection.index
    #                     ):
    #                         indexPass = True

    #                     if not indexPass:
    #                         return False
    #             else:
    #                 if searchSection.index != loopSection.index:
    #                     return False

    #             for i, linkedName1 in enumerate(searchSection.linkedNames):
    #                 linkedName2 = loopSection.linkedNames[i]

    #                 if linkedName1 != linkedName2 and not complexCompare(linkedName1, searchShape, oldShape, linkedName2, allowVaryingHistory, [], debugCheckName):
    #                     return False
    #         else:
    #             return False
        
    #     return True
    # else:
    #     return False
    return False
    
def searchForSimilarNames(searchName, searchShape, oldShape = None, allowVaryingHistory = True, debugCheckName = None):
    foundNames = []

    for loopIndexedNameString, loopMappedName in searchShape.elementMap.internalMap.items():
        if complexCompare(searchName, searchShape, oldShape, loopMappedName, allowVaryingHistory, [], debugCheckName):
            foundNames.append((loopMappedName, IndexedName.fromString(loopIndexedNameString)))
    
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