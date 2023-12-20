import functools

from qtpy.QtCore import Qt
from qtpy import QtWidgets

from labelme import utils
from . import ToolBar

class ImageList(QtWidgets.QWidget):
    def __init__(
        self,
        parent
    ):
        super(ImageList, self).__init__(parent)

        self.initActions()

        self.initWidgets()

    def initWidgets(self):
        # Init functions
        def toolbar(title, actions=None):
            toolbar = ToolBar(title)
            toolbar.setObjectName("%sToolBar" % title)
            toolbar.setOrientation(Qt.Horizontal)

            if actions:
                utils.addActions(toolbar, actions)
            return toolbar

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.tools = toolbar("Tools", self.actions)
        self.layout.addWidget(self.tools)

        self.list = QtWidgets.QScrollArea(self)
        self.layout.addWidget(self.list)
    
    def initActions(self):
        # Actions
        action = functools.partial(utils.newAction, self)
        open_ = action(
            slot=self.placeholder,##self.openFile,
            icon="open",
            tip=self.tr("Open image or label file"),
        )
        opendir = action(
            slot=self.placeholder,##self.openDirDialog,
            icon="open",
            tip=self.tr("Open Dir"),
        )
        deleteFile = action(
            slot=self.placeholder,##self.deleteFile,
            icon="delete",
            tip=self.tr("Delete current label file"),
            enabled=False,
        )

        self.actions = (
            open_,
            opendir,
            deleteFile
        )

    def placeholder(self):
        pass