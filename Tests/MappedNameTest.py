import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Data.MappedName import MappedName
from Data.IndexedName import IndexedName
from Data.MappedSection import MappedSection
from Data.DataEnums import OpCode, HistoryModifier, MapModifier

testNameSection1 = MappedSection(mapModifier = MapModifier.COPY, iterationTag = 1234, elementType = "Edge")
testNameSection2 = MappedSection(opCode = OpCode.BOOLEAN_FUSE, mapModifier = MapModifier.COPY, iterationTag = 2345, historyModifier = HistoryModifier.ITERATION, elementType = "Edge")
testNameSection3 = MappedSection(opCode = OpCode.BOOLEAN_CUT, mapModifier = MapModifier.SPLIT, linkedNames = [testNameSection1, testNameSection2], iterationTag = 3456, historyModifier = HistoryModifier.NEW, elementType = "Face")
testName = MappedName("g1", [testNameSection1, testNameSection2, testNameSection3])

print(testName.toDictionary())