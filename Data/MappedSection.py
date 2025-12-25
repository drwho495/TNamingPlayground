# import DataEnums
import sys
import os

sys.path.append(os.path.dirname(__file__))

from DataEnums import *

class MappedSection:
    def __init__(self,
                 opCode = OpCode.EXTRUSION,
                 historyModifier = HistoryModifier.NEW,
                 mapModifier = MapModifier.REMAP,
                 iterationTag = 0,
                 linkedNames = [],
                 referenceIDs = "",
                 elementType = "",
                 index = 0,
                 ancestors = []

    ):
        self.opCode = opCode
        self.historyModifier = historyModifier
        self.mapModifier = mapModifier
        self.iterationTag = iterationTag
        self.linkedNames = linkedNames
        self.referenceIDs = [referenceIDs] if isinstance(referenceIDs, str) else referenceIDs
        self.elementType = elementType
        self.index = index
        self.ancestors = ancestors
    
    def toDictionary(self):
        returnDict = {"ElementType": self.elementType,
                      "OpCode": self.opCode.value,
                      "HistoryModifier": self.historyModifier.value,
                      "MapModifier": self.mapModifier.value,
                      "IterationTag": self.iterationTag,
                      "ReferenceIDs": self.referenceIDs,
                      "LinkedNames": [],
                      "Ancestors": self.ancestors,
                      "Index": self.index}

        for linkedName in self.linkedNames:
            returnDict["LinkedNames"].append(linkedName.toDictionary())

        return returnDict
    
    @staticmethod
    def fromDictionary(dictionary):
        from Data.MappedName import MappedName # import here to avoid cyclic import issues

        newMappedSection = MappedSection(elementType = dictionary["ElementType"],
                                         opCode = OpCode(dictionary["OpCode"]),
                                         historyModifier = HistoryModifier(dictionary["HistoryModifier"]),
                                         mapModifier = MapModifier(dictionary["MapModifier"]),
                                         iterationTag = dictionary["IterationTag"],
                                         referenceIDs = dictionary["ReferenceIDs"],
                                         ancestors = dictionary["Ancestors"],
                                         index = dictionary["Index"])
        
        for linkedName in dictionary["LinkedNames"]:
            newMappedSection.linkedNames.append(MappedName.fromDictionary(linkedName))

        return newMappedSection