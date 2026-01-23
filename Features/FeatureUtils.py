def getFeaturesAndIndex(featureObj):
    if not isTNamingFeature(featureObj): return ([], 0)
    
    part = featureObj.getParent()
    features = []
    index = 0

    for groupObj in part.Group:
        if isTNamingFeature(groupObj):
            if groupObj.Name == featureObj.Name:
                index = len(features)

            features.append(groupObj) 
    
    return (features, index)

def showFeature(featureObj):
    allFeatures, index = getFeaturesAndIndex(featureObj)

    for i, feature in enumerate(allFeatures):
        if i == index:
            feature.Visibility = True
        else:
            feature.Visibility = False

def isTNamingFeature(obj):
    return hasattr(obj, "TNamingType") and hasattr(obj, "TShape")