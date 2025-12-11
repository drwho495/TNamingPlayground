class MappedName:
    def __init__(self, masterID = "", mappedSections = []):
        self.masterID = masterID
        self.mappedSections = mappedSections
    
    def toDictionary(self):
        returnDict = {"Sections": [], "MasterID": self.masterID}

        for mappedSection in self.mappedSections:
            returnDict["Sections"].append(mappedSection.toDictionary())
        
        return returnDict
    
    # this is a base equality check, we will do more complicated searching checks later
    def equal(self, otherMappedName):
        return otherMappedName.toDictionary() == self.toDictionary()