from enum import Enum

class OpCode(Enum):
    EXTRUSION = 1
    DRESSUP = 5
    SKETCH = 7
    REFINE = 8
    BOOLEAN = 9

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

class DressupType(Enum):
    FILLET = 1
    CHAMFER = 2