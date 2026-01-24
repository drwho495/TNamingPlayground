from enum import Enum

class OpCode(Enum):
    EXTRUSION = 1
    DRESSUP = 5
    SKETCH = 7
    REFINE = 8
    BOOLEAN = 9
    THICKNESS = 10
    COMPOUND = 11

class MapModifier(Enum):
    COPY = 1
    REMAP = 2
    MERGE = 3
    SOURCE = 5
    EXTRUDED = 6

class BooleanType(Enum):
    FUSE = 1
    CUT = 2
    INTERSECTION = 3

class DressupType(Enum):
    FILLET = 1
    CHAMFER = 2