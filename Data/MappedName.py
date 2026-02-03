import json
import copy
import time
# import PerformanceTimer as PerformanceTimer

# Layout for MappedName's sections:
# IterationTag and OpCode do not determine an element's qualification, but everything after it does.
# Those initial two entries tell the design intent algorithm what to look for in a loop name. They're used as a
# `key` of sorts.
# ReferenceIDs;ReferenceNames;InitialTag;Index;ElementType;DuplicateCount;MapperInfo
#      ^     other mapped names   ^        0      E/V/F           0        anything
# g1:1233:0,g2:1233:1,g3:1233:0  1234
class MappedName:
    def __init__(self, baseString = ""):
        self.baseString = baseString
    
    @staticmethod
    def makeName(referenceIDs = ["_"],
                 referenceNames = ["_"],
                 initialTag = 0,
                 index = 0,
                 elementType = "E",
                 duplicateCount = 0,
                 mapperInfo = "_"
    ):
        formattedRefNames = ""

        for i, name in enumerate(referenceNames):
            if i != 0:
                formattedRefNames += ","

            formattedRefNames += MappedName.escapeDeliminators(name, [";", ":", ","])

        return MappedName(f"{','.join(referenceIDs)};{formattedRefNames};{str(initialTag)};{str(index)};{elementType};{str(duplicateCount)};{mapperInfo}")
    
    def copy(self):
        return copy.deepcopy(self)
        # return MappedName(self.toString())
    
    # needed so that a MappedName can be a key in a dictionary.
    def __hash__(self):
        return hash(self.toString())
    
    def __eq__(self, value):
        if isinstance(value, MappedName) or isinstance(value, str):
            return self.equal(value)
        return False
    
    def toString(self):
        return self.baseString

    @staticmethod
    def stringToSections(str, deliminator = "|"):
        sections = []
        sectionString = ""
        escapeNumber = 0
        escapedChar = ""

        for i, char in enumerate(str):
            lastChar = (i == (len(str) - 1))

            if char == "\\":
                escapeNumber += 1

                if escapeNumber == 1:
                    continue
            elif (char == deliminator and escapeNumber == 0) or lastChar:
                if lastChar and char != deliminator:
                    sectionString += char

                sections.append(sectionString)
                sectionString = ""
                continue
            elif escapeNumber > 0:
                escapedChar = char
                escapeNumber = 0
            
            sectionString += char
        
        return sections

    @staticmethod
    def stringGetTag(string: str):
        return MappedName.stringGetSectionData(string, 2, True)

    @staticmethod
    def stringGetIndex(string: str):
        return MappedName.stringGetSectionData(string, 3, True)

    @staticmethod
    def stringGetSectionData(string: str, sectionIndex: int, convertToInt: bool = False):
        sections = MappedName.stringToSections(string, ";")

        if len(sections) > sectionIndex:
            returnString = sections[sectionIndex]

            if not convertToInt or not returnString.isdigit():
                return returnString
            else:
                return int(returnString)
        else:
            if convertToInt:
                return 0
            else:
                return "_"
            
    @staticmethod
    def escapeDeliminators(string: str, delims = [";"]):
        newStr = ""

        for char in string:
            if char in delims:
                newStr += "\\"
            
            newStr += char
        
        return newStr
    
    @staticmethod
    def unescapeString(string: str):
        newStr = ""
        escapeLevel = 0

        for char in string:
            if char == "\\":
                escapeLevel += 1

                if escapeLevel == 1:
                    continue
            else:
                escapeLevel = 0
            
            newStr += char
        
        return newStr

    @staticmethod
    def stringSetSectionData(string: str, sectionIndex: int, editString):
        sections = MappedName.stringToSections(string, ";")

        if len(sections) > sectionIndex:
            sections[sectionIndex] = str(editString)

            return ";".join(sections)
        return string

    @staticmethod
    def stringGetIDs(string: str):
        IDs = []
        IDstr = MappedName.stringGetSectionData(string, 0)

        if IDstr != "_":
            if "," in IDstr:
                IDs.extend(IDstr.split(","))
            elif IDstr != "_":
                IDs.append(IDstr)

        return IDs
    
    @staticmethod
    def stringGetNames(string: str):
        names = []
        nameStr = MappedName.stringGetSectionData(string, 1)

        if nameStr != "_":
            if "," in nameStr:
                names.extend(MappedName.stringToSections(nameStr, ","))
            else:
                names.append(nameStr)
        
        return names

    @staticmethod
    def makeSection():
        return ""
    
    def setInitialTag(self, newTag: int):
        self.baseString = MappedName.stringSetSectionData(self.baseString, 2, newTag)
    
    def setIndex(self, newIndex: int):
        self.baseString = MappedName.stringSetSectionData(self.baseString, 3, newIndex)

    def referenceIDs(self, packageInfo = False):
        nameString = self.toString()
        IDs = MappedName.stringGetIDs(nameString)

        if packageInfo:
            packagedIDs = []
            tag = MappedName.stringGetTag(nameString)
            index = MappedName.stringGetIndex(nameString)

            for idStr in IDs:
                if ":" in idStr:
                    idStr = idStr.split(":")[0]
                
                packagedIDs.append(f"{idStr}:{tag}:{index}")
            return packagedIDs
        else:
            return IDs
    
    def referenceNames(self):
        return MappedName.stringGetNames(self.toString())
    
    def packageReferenceIDs(self):
        IDs = self.referenceIDs(True)

        self.baseString = MappedName.stringSetSectionData(self.toString(), 0, ','.join(IDs))
    
    def getMapperInfo(self):
        return MappedName.stringGetSectionData(self.toString(), 6)

    # this is a base equality check, we will do more complicated searching checks later
    def equal(self, otherMappedName):
        return self.toString() == otherMappedName.toString()