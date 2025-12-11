# import DataEnums
import sys
import os

sys.path.append(os.path.dirname(__file__))

import DataEnums

class MappedSection:
    def __init__(self,
                 opCode = DataEnums.OpCode.EXTRUSION,
                 historyModifier = DataEnums.HistoryModifier.NEW,
                 mapModifier = DataEnums.MapModifier.REMAP,
                 iterationTag = 0,
                 linkedNames = [],
                 elementType = ""

    ):
        self.opCode = opCode
        self.historyModifier = historyModifier
        self.mapModifier = mapModifier
        self.iterationTag = iterationTag
        self.linkedNames = linkedNames
        self.elementType = elementType
    
    def toDictionary(self):
        returnDict = {"ElementType": self.elementType,
                      "OpCode": self.opCode.value,
                      "HistoryModifier": self.historyModifier.value,
                      "MapModifier": self.mapModifier.value,
                      "IterationTag": self.iterationTag,
                      "LinkedNames": []}

        for linkedName in self.linkedNames:
            returnDict["LinkedNames"].append(linkedName.toDictionary())

        return returnDict