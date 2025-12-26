# import DataEnums
import sys
import os
import copy

sys.path.append(os.path.dirname(__file__))

from Data.DataEnums import *

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
                 forkedElement = False,
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

        # this data point is used to simplify searching algorithms, it does not define an element's history!
        self.forkedElement = forkedElement 
    
    def copy(self):
        return copy.deepcopy(self)
    
    def toDictionary(self):
        returnDict = {"ElementType": self.elementType,
                      "OpCode": self.opCode.value,
                      "HistoryModifier": self.historyModifier.value,
                      "MapModifier": self.mapModifier.value,
                      "IterationTag": self.iterationTag,
                      "ReferenceIDs": self.referenceIDs,
                      "LinkedNames": [],
                      "ForkedElement": self.forkedElement,
                      "Ancestors": self.ancestors,
                      "Index": self.index}

        for linkedName in self.linkedNames:
            returnDict["LinkedNames"].append(linkedName.toDictionary())

        return returnDict
    
    def __hash__(self):
        return hash(str(self.toDictionary()))
    
    def __eq__(self, value):
        if isinstance(value, MappedSection):
            check = (self.opCode == value.opCode
                     and self.referenceIDs == value.referenceIDs
                     and self.historyModifier == value.historyModifier
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
                                         historyModifier = HistoryModifier(dictionary["HistoryModifier"]),
                                         mapModifier = MapModifier(dictionary["MapModifier"]),
                                         iterationTag = dictionary["IterationTag"],
                                         referenceIDs = dictionary["ReferenceIDs"],
                                         ancestors = dictionary["Ancestors"],
                                         linkedNames = [],
                                         forkedElement = dictionary["ForkedElement"],
                                         index = dictionary["Index"])
        
        print(f"linked name size: {len(dictionary['LinkedNames'])}")
        
        for linkedName in dictionary["LinkedNames"]:
            newMappedSection.linkedNames.append(MappedName.fromDictionary(linkedName))

        return newMappedSection