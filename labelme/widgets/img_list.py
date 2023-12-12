from qtpy.QtCore import Qt
from qtpy import QtWidgets

from labelme import utils
from . import ToolBar

class ImageList(QtWidgets.QWidget):
    def __init__(
        self,
        parent,
    ):
        super(ImageList, self).__init__(parent)

        # Init functions
        def toolbar(title, actions=None):
            toolbar = ToolBar(title)
            toolbar.setObjectName("%sToolBar" % title)
            toolbar.setOrientation(Qt.Horizontal)
            toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

            if actions:
                utils.addActions(toolbar, actions)
            return toolbar

        self.layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.layout)

        self.tools = toolbar("Tools")
        self.layout.addWidget(self.tools)

        self.list = QtWidgets.QScrollArea(self)
        self.layout.addWidget(self.list)