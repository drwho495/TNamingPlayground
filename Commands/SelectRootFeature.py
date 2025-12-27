import sys
import os

sys.path.append(os.path.dirname(__file__))

import Features.FeatureUtils as FeatureUtils
from Data.MappedName import MappedName
from Data.IndexedName import IndexedName
import FreeCAD as App
import FreeCADGui as Gui

class SelectRootFeature:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "Extrusion.svg"),
            'MenuText': "Highlights the feature that created the selected element in the tree view.",
            'ToolTip': "Highlights the feature that created the selected element in the tree view."
        }
        
    def Activated(self):
        if App.GuiUp:
            selection = Gui.Selection.getCompleteSelection()
            mappedName = MappedName()
            document = None

            if len(selection) != 0:
                element = selection[0]

                if element.HasSubObjects:
                    elementMap = element.Object.TShape.elementMap
                    indexedName = IndexedName.fromString(element.SubElementNames[0])
                            
                    mappedName = elementMap.getMappedName(indexedName)
                    document = element.Object.Document
            
                if len(mappedName.mappedSections) != 0:
                    for obj in document.Objects:
                        if obj.ID == abs(mappedName.mappedSections[0].iterationTag):
                            Gui.Selection.clearSelection()
                            Gui.Selection.addSelection(document.Name, obj.Name)

                            features, index = FeatureUtils.getFeaturesAndIndex(obj)

                            for i, feature in enumerate(features):
                                feature.Visibility = (i == index)

                            break
                    
    def IsActive(self):
        return App.ActiveDocument != None

Gui.addCommand('SelectRootFeature', SelectRootFeature())