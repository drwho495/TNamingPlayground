def getFeaturesAndIndex(featureObj):
    part = featureObj.getParent()
    features = []
    index = 0

    for groupObj in part.Group:
        if hasattr(groupObj, "TNamingType") and hasattr(groupObj, "TShape"):
            if groupObj.Name == featureObj.Name:
                index = len(features)

            features.append(groupObj) 
    
    return (features, index)