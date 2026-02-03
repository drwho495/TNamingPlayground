import sys
import os
import random
import string
import json

sys.path.append(os.path.dirname(__file__))

import Geometry.MappingUtils as MappingUtils
from Geometry.TShape import TShape
from Data.MappedName import MappedName
import FreeCADGui as Gui

def getFeaturesAndIndex(body, excludeFeature = None):
    if not isSDObject(body): return ([], 0)
    
    features = []
    index = 0

    for groupObj in body.Group:
        if isSDObject(groupObj):
            if excludeFeature != None and groupObj.Name == excludeFeature.Name:
                index = len(features)

            features.append(groupObj) 
    
    return (features, index)

def isSDObject(obj):
    return hasattr(obj, "StableDesignType")

def isSDFeatureOperation(obj):
    return isSDObject(obj) and hasattr(obj, "IsFeatureOperation") and obj.IsFeatureOperation

def ofType(obj, typeName):
    return isSDObject(obj) and obj.StableDesignType == typeName

def generateRandomName(map):
    keys = map.keys()
    newHash = ""

    while True:
        newHash = ''.join(random.choices(string.ascii_letters + string.digits, k = 10))

        if newHash not in keys:
            break
    
    return newHash

def convertAliasMapFromString(mapString: str):
    map = json.loads(mapString)
    formattedMap = {}

    for alias, namePair in map.items():
        formattedMap[alias] = (MappedName(namePair[0]), namePair[1])

    return formattedMap

def convertAliasMapToString(map: dict):
    formattedMap = {}

    for alias, namePair in map.items():
        formattedMap[alias] = (namePair[0].toString(), namePair[1])

    return json.dumps(formattedMap)

def updateAliasMap(oldMap: dict, shape: TShape) -> dict:
    newMap = {}

    for indexedName, mappedName in shape.elementMap.internalMap.items():
        resolvedName = False

        for alias, namePair in oldMap.items():
            if namePair[0] == mappedName and MappingUtils.complexCompare(namePair[0], shape, TShape(), mappedName):
                if alias not in newMap:
                    newMap[alias] = (mappedName, indexedName)

                    resolvedName = True
                    continue

        if not resolvedName: newMap[generateRandomName(oldMap)] = (mappedName, indexedName)
    
    return newMap

def getActiveBody():
    activeObj = Gui.ActiveDocument.ActiveView.getActiveObject("StableDesign")

    if ofType(activeObj, "DesignBody"):
        return activeObj
    else:
        return None

def getParentBody(obj):
    for parentObj in obj.InList:
        if ofType(parentObj, "DesignBody"):
            return parentObj
    return None

def updateShapeMap(aliasMap: dict, obj):
    if hasattr(obj, "Shape"):
        elementMap = {}
        shapeCopy = obj.Shape.copy()

        for aliasString, namePair in aliasMap.items():
            formattedStr = f"{aliasString};MKR"

            if formattedStr not in elementMap:
                elementMap[formattedStr] = namePair[1]
        
        shapeCopy.ElementMap = elementMap
        obj.Shape = shapeCopy