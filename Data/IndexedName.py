class IndexedName:
    def __init__(self, elementType = "", indexNumber = 1):
        self.elementType = elementType
        self.indexNumber = indexNumber

    def toString(self):
        return f"{self.elementType}{self.indexNumber}"