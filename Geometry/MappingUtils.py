def searchForSimilarNames(searchName, oldShape, searchShape, allowRecursion = True):
    pass

def getElementTypeName(occtTypeIndex):
    if occtTypeIndex == 4:
        return "Face"
    elif occtTypeIndex == 6:
        return "Edge"
    elif occtTypeIndex == 7:
        return "Vertex"
    
def occtLOStoList(listOfShapes):
    returnList = []

    while listOfShapes.Size() > 0:
        returnList.append(listOfShapes.First())
        listOfShapes.RemoveFirst()
    
    return returnList