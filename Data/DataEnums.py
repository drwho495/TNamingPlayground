from enum import Enum

class OpCode(Enum):
    EXTRUSION = 1
    BOOLEAN_CUT = 2
    BOOLEAN_FUSE = 3
    BOOLEAN_INTERSECTION = 4
    FILLET = 5
    CHAMFER = 6
    SKETCH = 7
    REFINE = 8

class MapModifier(Enum):
    COPY = 1
    REMAP = 2
    MERGE = 3
    SPLIT = 4
    SOURCE = 5
    EXTRUDED = 6

class HistoryModifier(Enum):
    NEW = 1
    ITERATION = 2

class BooleanType(Enum):
    FUSE = 1
    CUT = 2
    INTERSECTION = 3