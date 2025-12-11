import FreeCAD as App
import FreeCADGui as Gui
import Part
from statistics import mode

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
