import json
import copy
from Data.MappedSection import MappedSection

class MappedName:
    def __init__(self, mappedSections = []):
        self.mappedSections = mappedSections
    
    def toDictionary(self):
        returnDict = {"Sections": []}

        for mappedSection in self.mappedSections:
            returnDict["Sections"].append(mappedSection.toDictionary())
        
        return returnDict

    def copy(self):
        return copy.deepcopy(self)
    
    @staticmethod
    def fromDictionary(dictionary):
        mappedSections = []

        for section in dictionary["Sections"]:
            mappedSections.append(MappedSection.fromDictionary(section))
        
        return MappedName(mappedSections)
    
    # needed so that a MappedName can be a key in a dictionary.
    def __hash__(self):
        return hash(json.dumps(self.toDictionary()))
    
    def __eq__(self, value):
        if isinstance(value, MappedName) or isinstance(value, str):
            return self.equal(value)
        return False
    
    def masterIDs(self):
        if len(self.mappedSections) != 0:
            return self.mappedSections[0].referenceIDs
        
        return ""
    
    def getIterationTags(self):
        tags = []

        for section in self.mappedSections:
            tags.append(section.iterationTag)
        
        return tags
    
    # this is a base equality check, we will do more complicated searching checks later
    def equal(self, otherMappedName):
        if len(otherMappedName.mappedSections) != len(self.mappedSections):
            return False
        
        for i, section in enumerate(self.mappedSections):
            otherSection = otherMappedName.mappedSections[i]

            if section != otherSection:
                return False
        
        return True