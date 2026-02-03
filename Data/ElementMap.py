from Data.MappedName import MappedName
from Data.IndexedName import IndexedName
import copy

class ElementMap:
    def __init__(self):
        self.internalMap = {}

    def setElement(self, indexedName, mappedName: MappedName):
        self.internalMap[indexedName.toString()] = mappedName

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
            returnDict[indexedName] = mappedName.toString()
        
        return returnDict
    
    def __eq__(self, value):
        if isinstance(value, ElementMap):
            return value.internalMap == self.internalMap
    
    @staticmethod
    def fromAliasMap(aliasMap: dict):
        newElementMap = ElementMap()

        for _, namePair in aliasMap.items():
            newElementMap.internalMap[namePair[1]] = MappedName(namePair[0])

        return newElementMap

    @staticmethod
    def fromDictionary(dictionary):
        newElementMap = ElementMap()

        for indexNameStr, mappedNameStr in dictionary.items():
            newElementMap.internalMap[indexNameStr] = MappedName(mappedNameStr)
        
        return newElementMap

    def getIndexedName(self, mappedName: MappedName):
        for loopIndexedName, loopMappedName in self.internalMap.items():
            if loopMappedName.equal(mappedName):
                return IndexedName.fromString(loopIndexedName)
        
        return IndexedName()