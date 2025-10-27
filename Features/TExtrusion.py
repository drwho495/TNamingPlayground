import FreeCADGui as Gui
import FreeCAD as App
import os
import BenchUtils as Utils

class TExtrusion:
    def __init__(self, obj):
        obj.Proxy = self
        self.updateProps(obj)
    
    def updateProps(self, obj):
        if not hasattr(obj, "TElementMap"):
            obj.addProperty("App::PropertyString", "TElementMap")
            obj.TElementMap = "{}"
        
        if not hasattr(obj, "Support"):
            obj.addProperty("App::PropertyLink", "Support")
    
    def attach(self, obj):
        self.updateProps(obj)

    def execute(self, obj):
        print(f"recompute: {obj.Label}")

        self.updateProps(obj)

        if obj.Support != None:
            sketchFace, sketchElementMap = Utils.getFaceOfSketch(obj.Support)
            elementMap = {}

            print(sketchElementMap)
            
            featureShape, elementMap = Utils.makeMappedExtrusion(sketchFace, sketchElementMap, 10)
            obj.Shape = featureShape
            print(f"mapped elmap: {elementMap}")

            Utils.colorElementsFromSupport(obj, obj.Shape, elementMap)
    
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None

class TExtrusionViewObject:
    def __init__(self, obj):
        obj.ViewObject.Proxy = self
        self.updateProps(obj.ViewObject)

        self.Object = obj.ViewObject
    
    def updateProps(self, vobj):
        pass

    def attach(self, vobj):
        self.Object = vobj

    def claimChildren(self):
        if hasattr(self, "Object") and self.Object.Object.Support != None:
            return [self.Object.Object.Support]
        return []

    def setEdit(self, vobj, mode):
        return False

    def getIcon(self):
        return os.path.join(os.path.dirname(__file__), "..", "icons", "Extrusion.svg")
    
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None
    
def makeExtrusion():
    obj = App.ActiveDocument.addObject("Part::FeaturePython", "Extrusion")

    TExtrusion(obj)
    TExtrusionViewObject(obj)