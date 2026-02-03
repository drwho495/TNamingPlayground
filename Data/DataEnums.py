from enum import Enum

class OpCode(Enum):
    EXTRUSION = "EXT"
    DRESSUP = "DRE"
    SKETCH = "SKT"
    REFINE = "RFI"
    BOOLEAN = "BOL"
    THICKNESS = "THK"
    COMPOUND = "CMP"

class BooleanType(Enum):
    FUSE = 1
    CUT = 2
    INTERSECTION = 3

class DressupType(Enum):
    FILLET = 1
    CHAMFER = 2