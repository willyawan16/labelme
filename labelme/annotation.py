from qtpy.QtCore import Qt
from qtpy import QtGui
from qtpy import QtWidgets

from . import utils
from labelme.config import get_config
from labelme.label_file import LabelFile
from labelme.widgets import Canvas
from labelme.widgets import ImageList
from labelme.widgets import ToolBar

class Annotation(QtWidgets.QWidget):

    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = 0, 1, 2

    def __init__(
        self,
        parent,
        config
    ):
        super(Annotation, self).__init__(parent)

        # see labelme/config/default_config.yaml for valid configuration
        if config is None:
            config = get_config()
        self._config = config

        self.initWidgets()

    def initWidgets(self):
        def toolbar(title, actions=None):
            toolbar = ToolBar(title)
            toolbar.setObjectName("%sToolBar" % title)
            toolbar.setOrientation(Qt.Horizontal)
            toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

            toolButton = QtWidgets.QToolButton()
            toolButton.setText("Apple")
            toolButton.setCheckable(True)
            toolButton.setAutoExclusive(True)
            toolbar.addWidget(toolButton)

            if actions:
                utils.addActions(toolbar, actions)
            return toolbar
    
        def initCanvas(self):
            self.canvas = Canvas(
                epsilon=self._config["epsilon"],
                double_click=self._config["canvas"]["double_click"],
                num_backups=self._config["canvas"]["num_backups"],
                crosshair=self._config["canvas"]["crosshair"],
            )

            filename = "C:/AOI/上蓋標記檔/白色上蓋標記檔/13_1_1_8000.jpg"
            self.imageData = LabelFile.load_image_file(filename)
            image = QtGui.QImage.fromData(self.imageData)
            self.canvas.loadPixmap(QtGui.QPixmap.fromImage(image))
            self.canvas.scale = 0.2

        self.layout = QtWidgets.QHBoxLayout(self)
        self.setLayout(self.layout)

        # Left widget
        leftWidget = QtWidgets.QWidget()
        leftWidget.layout = QtWidgets.QVBoxLayout(leftWidget)
        leftWidget.setLayout(leftWidget.layout)

        leftTabs = QtWidgets.QTabWidget()
        leftWidget.layout.addWidget(leftTabs)

        self.tabVal = ImageList(self)
        self.tabTrain = ImageList(self)
        leftTabs.addTab(self.tabVal, "Validation")
        leftTabs.addTab(self.tabTrain, "Training")

        # Middle widget
        middleWidget = QtWidgets.QWidget()
        middleWidget.layout = QtWidgets.QVBoxLayout(middleWidget)
        middleWidget.setLayout(middleWidget.layout)

        self.tools = toolbar("Tools")
        middleWidget.layout.addWidget(self.tools)

        initCanvas(self)
        middleWidget.layout.addWidget(self.canvas)

        # Right widget
        rightWidget = QtWidgets.QScrollArea()
        rightWidget.layout = QtWidgets.QVBoxLayout(rightWidget)
        rightWidget.setLayout(rightWidget.layout)

        self.layout.addWidget(leftWidget)
        self.layout.addWidget(middleWidget)
        self.layout.addWidget(rightWidget)
