import FreeCAD as App
import FreeCADGui as Gui
import Part

def getFaceOfSketch(sketch):
    wireEdges = []
    wireVertexes = []
    elementMap = {} # "Edge1": "g1"

    for geom in sketch.GeometryFacadeList:
        geomShape = geom.Geometry.toShape()
        edges = geomShape.Edges
        vertexes = geomShape.Vertexes

        for i, _ in enumerate(edges):
            elementMap[f"Edge{len(wireEdges) + (i + 1)}"] = f"g{geom.Id}"

        for i, vertex in enumerate(vertexes):
            if hasattr(geom.Geometry, "EndPoint"):
                pointNum = 1

                if geom.Geometry.EndPoint.isEqual(vertex.Point, 1e-6):
                    pointNum = 2

                elementMap[f"Vertex{len(wireVertexes) + (i + 1)}"] = f"g{geom.Id}v{pointNum}"
            else:
                elementMap[f"Vertex{len(wireVertexes) + (i + 1)}"] = f"g{geom.Id}"

        wireEdges.extend(edges)
        wireVertexes.extend(vertexes)
    
    if len(wireEdges) != 0:
        wire = Part.Wire(wireEdges)
        face = Part.makeFace(wire)

        return (face, elementMap)
    
def colorElementsFromSupport(obj, shape, elementMap):
    colors = [(1.0, 0.0, 0.0)] * len(shape.Edges)

    for i, _ in enumerate(shape.Edges):
        edgeName = f"Edge{i + 1}"

        if edgeName in elementMap:
            colors[i] = (0.0, 1.0, 0.0)

    obj.ViewObject.LineColorArray = colors

def makeElementExtrusion(supportFace, supportElementMap, length):
    returnShape = supportFace.extrude(App.Vector(0, 0, length))
    elementMap = {}

    # first we map the sketch face to the bottom of the extrusion shape.
    for supportI, supportEdge in enumerate(supportFace.Edges):
        for finalI, finalEdge in enumerate(returnShape.Edges):
            if supportEdge.isSame(finalEdge):
                elementMap[f"Edge{finalI + 1}"] = supportElementMap[f"Edge{supportI + 1}"]

    return (returnShape, elementMap)