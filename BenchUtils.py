import FreeCAD as App
import FreeCADGui as Gui
import Part
from statistics import mode

def getFaceOfSketch(sketch):
    elementMap = {} # "Edge1": "g1"
    vertexesMap = {}
    facesMap = {}

    sketchWires = list(filter(lambda w: w.isClosed(), sketch.Shape.Wires))

    try:
        supportFace = Part.makeFace(sketchWires)
    except:
        supportFace = None
    
    if supportFace != None:
        for geoF in sketch.GeometryFacadeList:
            geom = geoF.Geometry
            geomShape = geom.toShape()

            if geom.TypeId != "Part::GeomPoint":
                for i, edge in enumerate(supportFace.Edges):
                    if edge.Curve.isSame(geomShape.Curve, 1e-6, 1e-6):
                        print("edge is same")
                        elementMap[f"Edge{i + 1}"] = f"g{geoF.Id};"

                        if len(edge.Vertexes) > 1:
                            for vertex in edge.Vertexes:
                                vertexName = getNameOfElement(vertex, supportFace)

                                if vertexName != None:
                                    if vertexName not in vertexesMap:
                                        vertexesMap[vertexName] = []
                                    
                                    if vertex.Point.isEqual(geom.StartPoint, 1e-6):
                                        vertexesMap[vertexName].append(f"g{geoF.Id}v1")

                                    if vertex.Point.isEqual(geom.EndPoint, 1e-6):
                                        vertexesMap[vertexName].append(f"g{geoF.Id}v2")
                        elif len(edge.Vertexes) == 1:
                            vertexName = getNameOfElement(edge.Vertexes[0], supportFace)
                            
                            if vertexName != None:
                                vertexesMap[vertexName] = []

                            vertexesMap[vertexName].append(f"g{geoF.Id}v1")
    
        for vertexName, IDs in vertexesMap.items():
            if len(IDs) != 0:
                print(IDs)
                
                elementMap[vertexName] = f"{','.join(IDs)};"
        
        for face in supportFace.Faces:
            faceName = getNameOfElement(face, supportFace)

            for faceEdge in face.Edges:
                faceEdgeName = getNameOfElement(faceEdge, supportFace)

                if faceEdgeName in elementMap:
                    if faceName not in facesMap:
                        facesMap[faceName] = []
                    
                    facesMap[faceName].append(elementMap[faceEdgeName].removesuffix(";"))
        
        for faceName, ids in facesMap.items():
            elementMap[faceName] = f"{','.join(ids)};"
        
        return (supportFace, elementMap)
    else:
        return (supportFace, {})
    
def colorElementsFromSupport(obj, shape, elementMap):
    edgeColors = [(1.0, 0.0, 0.0)] * len(shape.Edges)
    faceColors = [(1.0, 0.0, 0.0)] * len(shape.Faces)

    for i, _ in enumerate(shape.Edges):
        edgeName = f"Edge{i + 1}"

        if edgeName in elementMap:
            edgeColors[i] = (0.0, 1.0, 0.0)

    for i, _ in enumerate(shape.Faces):
        faceName = f"Face{i + 1}"

        if faceName in elementMap:
            faceColors[i] = (0.0, 1.0, 0.0)

    obj.ViewObject.LineColorArray = edgeColors
    obj.ViewObject.DiffuseColor = faceColors

def mapSubElement(mapToShape, mapToElementMap, mapFromShape, mapFromElementMap, opCode = "EXT", mapArea = "BAS", mappedEdgesList = None, mappedVertexesList = None, mappedFacesList = None):
    suffix = ""

    if len(opCode) != 0:
        suffix = f"{opCode}"

        if len(mapArea) != 0:
            suffix = f"{suffix}[{mapArea}];"
        else:
            suffix = f"{suffix};"

    for sEdgeI, supportEdge in enumerate(mapFromShape.Edges):
        for finalEdgeI, finalEdge in enumerate(mapToShape.Edges):
            if supportEdge.isSame(finalEdge):
                supportName = f'Edge{sEdgeI + 1}'

                if supportName in mapFromElementMap:
                    mapToElementMap[f"Edge{finalEdgeI + 1}"] = f"{mapFromElementMap[supportName].removesuffix(';')};{suffix}"

                    if mappedEdgesList != None:
                        mappedEdgesList.append(f"Edge{finalEdgeI + 1}")
    
    for sVertexI, supportVertex in enumerate(mapFromShape.Vertexes):
        for finalVertexI, finalVertex in enumerate(mapToShape.Vertexes):
            if supportVertex.isSame(finalVertex):
                supportName = f'Vertex{sVertexI + 1}'

                if supportName in mapFromElementMap:
                    mapToElementMap[f"Vertex{finalVertexI + 1}"] = f"{mapFromElementMap[supportName].removesuffix(';')};{suffix}"

                    if mappedVertexesList != None:
                        mappedVertexesList.append(f"Vertex{finalVertexI + 1}")
    
    for sFaceI, supportFace in enumerate(mapFromShape.Faces):
        for finalFaceI, finalFace in enumerate(mapToShape.Faces):
            if supportFace.isSame(finalFace):
                supportName = f'Face{sFaceI + 1}'

                if supportName in mapFromElementMap:
                    mapToElementMap[f"Face{finalFaceI + 1}"] = f"{mapFromElementMap[supportName].removesuffix(';')};{suffix}"

                    if mappedVertexesList != None:
                        mappedVertexesList.append(f"Face{finalFaceI + 1}")
    
    return mapToElementMap

def getNameOfElement(elementShape, shape):
    if isinstance(elementShape, Part.Vertex):
        for i, vertex in enumerate(shape.Vertexes):
            if elementShape.isSame(vertex):
                return f"Vertex{i + 1}"
    elif isinstance(elementShape, Part.Edge):
        for i, edge in enumerate(shape.Edges):
            if elementShape.isSame(edge):
                return f"Edge{i + 1}"
    elif isinstance(elementShape, Part.Face):
        for i, face in enumerate(shape.Faces):
            if elementShape.isSame(face):
                return f"Face{i + 1}"

def mapPrism(shapeToMap, supportFace, supportElementMap, elementMap, opCode = "EXT"):
    baseEdges     = []
    extrudedEdges = {}
    copiedEdges   = {}

    # first we map the sketch face to the bottom of the extrusion shape.
    elementMap = mapSubElement(shapeToMap,
                               elementMap,
                               supportFace,
                               supportElementMap,
                               opCode = opCode,
                               mapArea = "0",
                               mappedEdgesList = baseEdges)
    
    # now we will map the edges that are drawn up from each edge vertex
    for edgeName in baseEdges:
        edgeShape = shapeToMap.getElement(edgeName)

        if not edgeShape.isNull():
            for vertex in edgeShape.Vertexes:
                vertexName = getNameOfElement(vertex, shapeToMap)

                if vertexName != None and vertexName in elementMap:
                    extrudeAncestors = shapeToMap.ancestorsOfType(vertex, Part.Edge)

                    for extrudedAncestor in extrudeAncestors:
                        ancestorName = getNameOfElement(extrudedAncestor, shapeToMap)

                        if ancestorName not in elementMap:
                            if ancestorName not in extrudedEdges:
                                extrudedEdges[ancestorName] = []
                            
                            # will put these in the element map later for faster mapping (we don't want to edit old entries)
                            extrudedEdges[ancestorName].append(f"{elementMap[vertexName].removesuffix(';')}")

                            # now find the top element and store it for mapping later
                            if len(extrudedAncestor.Vertexes) > 1:
                                topVertex = extrudedAncestor.Vertexes[1] if extrudedAncestor.Vertexes[0].isSame(vertex) else extrudedAncestor.Vertexes[0]
                                topAncestors = shapeToMap.ancestorsOfType(topVertex, Part.Edge)

                                for topAncestor in topAncestors:
                                    topAncestorName = getNameOfElement(topAncestor, shapeToMap)

                                    if topAncestorName not in elementMap and topAncestorName not in extrudedEdges:
                                        if topAncestorName not in copiedEdges:
                                            copiedEdges[topAncestorName] = []
                                        
                                        copiedEdges[topAncestorName].append(elementMap[vertexName].removesuffix(';'))
    
    # now we need to go thru the copied edges and properly add them to the map
    for copiedEdge, IDs in copiedEdges.items():
        filteredIDs = []

        for ID in IDs:
            idList = [ID]

            if "," in ID:
                idList = ID.split(",")
            
            for ID2 in idList:
                if "v" in ID2:
                    filteredIDs.append(ID2.split("v")[0])
        
        if len(filteredIDs) != 0:
            edgeID = mode(filteredIDs)
            print(f"mode edge id: {edgeID} from IDs: {filteredIDs} for {copiedEdge}")

            elementMap[copiedEdge] = f"{edgeID};{opCode}[2];"

    for edgeName, IDs in extrudedEdges.items():
        elementMap[edgeName] = f"{','.join(IDs)};{opCode}[1];"

    return elementMap

def makeMappedExtrusion(supportFace, supportElementMap, length):
    returnShape = supportFace.extrude(App.Vector(0, 0, length))
    elementMap  = {}

    print(f"support elmap: {supportElementMap}")

    mapPrism(returnShape, supportFace, supportElementMap, elementMap)
    
    return (returnShape, elementMap)