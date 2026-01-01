import sys
import os

sys.path.append(os.path.dirname(__file__))

from Data.MappedName import MappedName
from Data.IndexedName import IndexedName
import FreeCAD as App
import FreeCADGui as Gui

from PySide.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
    QVBoxLayout,
    QDockWidget,
)
from PySide.QtCore import Qt

WINDOW_TITLE = "TNaming History Viewer"

class HistoryViewerWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setColumnCount(2)
        self.setHeaderLabels(["Entry", "Value"])
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(True)

    def loadMappedName(self, mappedName: MappedName):
        self.clear()

        for i, section in enumerate(mappedName.mappedSections):
            sectionDict = section.toDictionary()

            self.addTopLevelItem(self._createItem("Operation Code", section.opCode.name))
            self.addTopLevelItem(self._createItem("History Modifier", section.historyModifier.name))
            self.addTopLevelItem(self._createItem("Map Modifier", section.mapModifier.name))
            self.addTopLevelItem(self._createItem("Iteration Tag", section.iterationTag))
            self.addTopLevelItem(self._createItem("Linked Names", sectionDict["LinkedNames"]))
            self.addTopLevelItem(self._createItem("Reference ID(s)", ",".join(section.referenceIDs)))
            self.addTopLevelItem(self._createItem("Element Type", section.elementType))
            self.addTopLevelItem(self._createItem("Element is Split", section.forkedElement))
            self.addTopLevelItem(self._createItem("Index", section.index))
            self.addTopLevelItem(self._createItem("Number Of Split Elements", section.totalNumberOfSectionElements))
            self.addTopLevelItem(self._createItem("Deleted Name(s)", sectionDict["DeletedNames"]))
            self.addTopLevelItem(self._createItem("Ancestor(s)", sectionDict["Ancestors"]))
            if (i + 1) != len(mappedName.mappedSections): self.addTopLevelItem(self._createItem())

        self.expandAll()

    def _createItem(self, name = "", value = ""):
        item = QTreeWidgetItem([str(name), ""])

        if isinstance(value, dict):
            for k, v in value.items():
                item.addChild(self._createItem(k, v))
        else:
            item.setText(1, str(value))
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            item.setData(1, Qt.UserRole, type(value))

        return item

    def extractProperties(self):
        out = {}
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            out[item.text(0)] = self._extractItem(item)
        return out

    def _extractItem(self, item):
        if item.childCount() == 0:
            raw = item.text(1)
            typ = item.data(1, Qt.UserRole)
            return self._cast(raw, typ)

        return {
            item.child(i).text(0): self._extractItem(item.child(i))
            for i in range(item.childCount())
        }

    @staticmethod
    def _cast(value, typ):
        try:
            if typ is bool:
                return value.lower() in ("1", "true", "yes")
            return typ(value)
        except Exception:
            return value


class HistoryViewerWindow(QDockWidget):
    def __init__(self):
        super().__init__(WINDOW_TITLE)

        container = QWidget(self)
        layout = QVBoxLayout(container)

        self.viewerWidget = HistoryViewerWidget()
        layout.addWidget(self.viewerWidget)

        container.setLayout(layout)
        self.setWidget(container)
    
    def loadMappedName(self, name: MappedName):
        self.viewerWidget.loadMappedName(name)


class DisplayElementHistory:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "Extrusion.svg"),
            'MenuText': "Displays the history of the selected element.",
            'ToolTip': "Displays the history of the selected element."
        }
        
    def Activated(self):
        if App.GuiUp:
            selection = Gui.Selection.getCompleteSelection()
            mappedName = MappedName()

            for element in selection:
                if element.HasSubObjects:
                    elementMap = element.Object.TShape.elementMap
                    indexedName = IndexedName.fromString(element.SubElementNames[0])
                            
                    mappedName = elementMap.getMappedName(indexedName)
                    
            mw = Gui.getMainWindow()

            for dock in mw.findChildren(QDockWidget):
                if dock.windowTitle() == WINDOW_TITLE:
                    dock.setParent(None)
                    dock.close()
                    dock.deleteLater()

            dock = HistoryViewerWindow()
            dock.loadMappedName(mappedName)

            mw.addDockWidget(Qt.RightDockWidgetArea, dock)

            dock.show()
            
    def IsActive(self):
        return App.ActiveDocument != None

Gui.addCommand('DisplayElementHistory', DisplayElementHistory())