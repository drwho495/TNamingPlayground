class ElementMap:
    def __init__(self):
        self.internalMap = {}

    def setElement(self, indexedName, mappedName):
        self.internalMap[indexedName.toString()] = mappedName
    
    def getElementName(self, indexedName):
        return self.internalMap[indexedName.toString()]
    
    def getElementIndexedName(self, mappedName):
        for loopIName, loopMName in self.internalMap.items():
            if loopMName.equal(mappedName):
                return loopIName