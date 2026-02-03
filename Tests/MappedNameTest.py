import sys
import os
import timeit

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Data.MappedName import MappedName

sketchName = MappedName.makeName(["g1","g2","g3"], initialTag = 5, mapperInfo = "SRC")
extrusionName = MappedName(f"{','.join(sketchName.referenceIDs(True))};_;6;0;E;0;TOP")
boolLikeName = MappedName("_;g1\:519\:0\;_\;520\;0\;F\;0\;EXT,g1\:522\:0\;_\;523\;0\;F\;0\;SRC;523;0;E;0;BGG")

sketchName.setInitialTag(4)

print(f"{sketchName.toString()}")
print(f"{sketchName.referenceIDs(True)}")
print(f"{sketchName.getMapperInfo()}")

print(f"{extrusionName.toString()}")
print(f"{extrusionName.referenceIDs()}")
print(f"{extrusionName.getMapperInfo()}")

print(f"\n{boolLikeName.toString()}")
print(f"{boolLikeName.referenceNames()}")

# time = timeit.timeit(lambda: extrusionName1.toSections(), number=10000)

# print(f"time: {round(time * 1000, 1)}")