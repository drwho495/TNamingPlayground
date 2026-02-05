from Data.MappedName import MappedName
from Data.IndexedName import IndexedName
import copy

class ElementMap:
    def __init__(self):
        self.internalMap = {}

    def setElement(self, indexedName, mappedName: MappedName):
        self.internalMap[mappedName] = IndexedName.fromString(indexedName.toString())
    
    def hasIndexedName(self, indexedName):
        return IndexedName.fromString(indexedName.toString()) in self.internalMap.values()
    
    def getMappedNames(self, indexedName):
        names = []

        for mappedName, loopIndexName in self.internalMap.items():
            if loopIndexName.toString() == indexedName.toString():
                names.append(mappedName)

        return names

    def getMappedName(self, indexedName):
        names = self.getMappedNames(indexedName)

        if len(names) == 0:
            return None

        return names[0]
    
    def getMap(self):
        return self.internalMap
    
    def copy(self):
        return copy.deepcopy(self)
    
    def toDictionary(self):
        returnDict = {}

        for mappedName, indexedName in self.internalMap.items():
            returnDict[mappedName.toString()] = indexedName.toString()
        
        return returnDict
    
    def __eq__(self, value):
        if isinstance(value, ElementMap):
            return value.internalMap == self.internalMap
    
    @staticmethod
    def fromAliasMap(aliasMap: dict):
        newElementMap = ElementMap()

        for _, namePair in aliasMap.items():
            newElementMap.internalMap[MappedName(namePair[0])] = IndexedName.fromString(namePair[1])

        return newElementMap

    @staticmethod
    def fromDictionary(dictionary):
        newElementMap = ElementMap()

        for mappedNameStr, indexNameStr in dictionary.items():
            newElementMap.internalMap[MappedName(mappedNameStr)] = IndexedName.fromString(indexNameStr)
        
        return newElementMap

    def getIndexedName(self, mappedName: MappedName):
        if mappedName not in self.internalMap:
            return IndexedName()
        
        return self.internalMap[mappedName]