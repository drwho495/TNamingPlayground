from Data.MappedName import MappedName
from Data.IndexedName import IndexedName
import copy

class ElementMap:
    def __init__(self):
        self.internalMap = {}
        self.tagsInHistory = []

    def setElement(self, indexedName, mappedName):
        self.internalMap[indexedName.toString()] = mappedName

        for section in mappedName.mappedSections:
            if section.iterationTag not in self.tagsInHistory:
                self.tagsInHistory.append(section.iterationTag)
    
    def hasTag(self, tag):
        return tag in self.tagsInHistory

    def hasIndexedName(self, indexedName):
        return indexedName.toString() in self.internalMap
    
    def getMappedName(self, indexedName):
        if indexedName.toString() not in self.internalMap:
            return MappedName()

        return self.internalMap[indexedName.toString()]
    
    def getMap(self):
        return self.internalMap
    
    def copy(self):
        return copy.deepcopy(self)
    
    def toDictionary(self):
        returnDict = {}

        for indexedName, mappedName in self.internalMap.items():
            returnDict[indexedName] = mappedName.toDictionary()
        
        return returnDict
    
    def __eq__(self, value):
        if isinstance(value, ElementMap):
            return value.internalMap == self.internalMap
    
    @staticmethod
    def fromDictionary(dictionary):
        newElementMap = ElementMap()

        for indexNameStr, mappedNameDict in dictionary.items():
            newElementMap.internalMap[indexNameStr] = MappedName.fromDictionary(mappedNameDict)
        
        return newElementMap

    def getIndexedName(self, mappedName: MappedName):
        for loopIndexedName, loopMappedName in self.internalMap.items():
            if loopMappedName.equal(mappedName):
                return IndexedName.fromString(loopIndexedName)
        
        return IndexedName()