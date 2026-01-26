# import DataEnums
import sys
import os
import copy

sys.path.append(os.path.dirname(__file__))

from Data.DataEnums import *

class MappedSection:
    def __init__(self,
                 opCode = OpCode.EXTRUSION,
                 mapModifier = MapModifier.REMAP,
                 iterationTag = 0,
                 linkedNames = [],
                 referenceIDs = "",
                 elementType = "",
                 index = 0,
                 totalNumberOfSectionElements = 1,
                 forkedElement = False,
                 deletedNames = [],
                 ancestors = []

    ):
        self.opCode = opCode
        self.mapModifier = mapModifier
        self.iterationTag = iterationTag
        self.linkedNames = linkedNames
        self.referenceIDs = [referenceIDs] if isinstance(referenceIDs, str) else referenceIDs
        self.elementType = elementType
        self.index = index

        # these variables do not change the history of an element, they are just used in searching algorithms
        # to improve the quality of their outputs. they are not to be used in equality checks!
        self.totalNumberOfSectionElements = totalNumberOfSectionElements
        self.deletedNames = deletedNames
        self.forkedElement = forkedElement 
        self.ancestors = ancestors
    
    def copy(self):
        return copy.deepcopy(self)
    
    def toDictionary(self):
        returnDict = {"ElementType": self.elementType,
                      "OpCode": self.opCode.value,
                      "MapModifier": self.mapModifier.value,
                      "IterationTag": self.iterationTag,
                      "ReferenceIDs": self.referenceIDs,
                      "ForkedElement": self.forkedElement,
                      "LinkedNames": [],
                      "DeletedNames": [],
                      "TotalNumberOfSectionElements": self.totalNumberOfSectionElements,
                      "Ancestors": [],
                      "Index": self.index}

        for linkedName in self.linkedNames:
            returnDict["LinkedNames"].append(linkedName.toDictionary())
        
        for deletedName in self.deletedNames:
            returnDict["DeletedNames"].append(deletedName.toDictionary())
        
        for ancestorName in self.ancestors:
            returnDict["Ancestors"].append(ancestorName.toDictionary())

        return returnDict
    
    def __hash__(self):
        return hash(str(self.toDictionary()))
    
    def __eq__(self, value):
        if isinstance(value, MappedSection):
            check = (self.opCode == value.opCode
                     and self.referenceIDs == value.referenceIDs
                     and self.mapModifier == value.mapModifier
                     and self.iterationTag == value.iterationTag
                     and self.elementType == value.elementType
                     and self.index == value.index)
            
            if check:
                if len(self.linkedNames) == len(value.linkedNames):
                    for i, name1 in enumerate(self.linkedNames):
                        name2 = value.linkedNames[i]

                        if name1 != name2:
                            return False
                    return True
        return False
    
    @staticmethod
    def fromDictionary(dictionary):
        from Data.MappedName import MappedName # import here to avoid cyclic import issues

        newMappedSection = MappedSection(elementType = dictionary["ElementType"],
                                         opCode = OpCode(dictionary["OpCode"]),
                                         mapModifier = MapModifier(dictionary["MapModifier"]),
                                         iterationTag = dictionary["IterationTag"],
                                         referenceIDs = dictionary["ReferenceIDs"],
                                         totalNumberOfSectionElements = dictionary["TotalNumberOfSectionElements"],
                                         forkedElement = dictionary["ForkedElement"],
                                         index = dictionary["Index"]).copy()
        
        for linkedName in dictionary["LinkedNames"]:
            newMappedSection.linkedNames.append(MappedName.fromDictionary(linkedName))

        if "DeletedNames" in dictionary:
            for deletedName in dictionary["DeletedNames"]:
                newMappedSection.deletedNames.append(MappedName.fromDictionary(deletedName))
        elif "AlternativeNames" in dictionary:
            for alternativeName in dictionary["AlternativeNames"]:
                newMappedSection.deletedNames.append(MappedName.fromDictionary(alternativeName))
        
        for ancestorName in dictionary["Ancestors"]:
            newMappedSection.ancestors.append(MappedName.fromDictionary(ancestorName))

        return newMappedSection