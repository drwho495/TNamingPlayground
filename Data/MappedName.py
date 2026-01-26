import json
import copy
import time
from Data.MappedSection import MappedSection
import PerformanceTimer as PerformanceTimer

class MappedName:
    def __init__(self, mappedSections = []):
        self.mappedSections = mappedSections
    
    def toDictionary(self):
        PerformanceTimer.GlobalTimer.addKey("MappedNameToDictionary")
        returnDict = {"Sections": []}

        for mappedSection in self.mappedSections:
            returnDict["Sections"].append(mappedSection.toDictionary())
        
        PerformanceTimer.GlobalTimer.pauseKey("MappedNameToDictionary")
        
        return returnDict

    def copy(self):
        return copy.deepcopy(self)
    
    @staticmethod
    def fromDictionary(dictionary):
        PerformanceTimer.GlobalTimer.addKey("MappedNameFromDictionary")
        mappedSections = []

        for section in dictionary["Sections"]:
            mappedSections.append(MappedSection.fromDictionary(section))
        
        newName = MappedName(mappedSections)

        PerformanceTimer.GlobalTimer.pauseKey("MappedNameFromDictionary")

        return newName
    
    # needed so that a MappedName can be a key in a dictionary.
    def __hash__(self):
        return hash(json.dumps(self.toDictionary()))
    
    def __eq__(self, value):
        if isinstance(value, MappedName) or isinstance(value, str):
            return self.equal(value)
        return False
    
    def masterIDs(self, includeLinkedNames = False):
        ids = []

        if len(self.mappedSections) != 0:
            ids.extend(self.mappedSections[0].referenceIDs)
        
            if includeLinkedNames:
                for linkedName in self.mappedSections[0].linkedNames:
                    ids.extend(linkedName.masterIDs())
        
        return ids
    
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