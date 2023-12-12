import functools

from labelme import __appname__
from labelme.annotation import Annotation

from . import utils
from labelme.config import get_config

from qtpy import QtCore
from qtpy import QtWidgets

class TableWidget(QtWidgets.QWidget):
    
    def __init__(
            self, 
            parent,
            config=None,
            filename=None,
            output=None,
            output_file=None,
            output_dir=None,
        ):
        super(QtWidgets.QWidget, self).__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        
        # Initialize tab screen
        self.tabs = QtWidgets.QTabWidget()
        self.tab1 = QtWidgets.QWidget()
        self.tab2 = QtWidgets.QWidget()
        self.tab3 = QtWidgets.QWidget()
        self.tabs.resize(300,200)
        
        # Add tabs
        self.tabs.addTab(self.tab1,"Datasets")
        self.tabs.addTab(self.tab2,"Annotation")
        self.tabs.addTab(self.tab3,"Training")
        
        # Create first tab
        self.tab1.layout = QtWidgets.QVBoxLayout(self)
        self.pushButton1 = QtWidgets.QPushButton("PyQt5 button")
        self.tab1.layout.addWidget(self.pushButton1)
        self.tab1.setLayout(self.tab1.layout)

        # Create second tab
        self.tab2.layout = QtWidgets.QVBoxLayout(self)
        self.annotation = Annotation(self, config)
        self.tab2.layout.addWidget(self.annotation)
        self.tab2.setLayout(self.tab2.layout)
        
        # Add tabs to widget
        self.layout.addWidget(self.tabs)

class MainWindow(QtWidgets.QMainWindow):

    def __init__(
        self,
        config=None,
        filename=None,
        output=None,
        output_file=None,
        output_dir=None,
    ):
        # see labelme/config/default_config.yaml for valid configuration
        if config is None:
            config = get_config()
        self._config = config

        super(MainWindow, self).__init__()
        self.setWindowTitle(__appname__)

        self.table_widget = TableWidget(self, config, filename, output, output_file, output_dir)
        self.setCentralWidget(self.table_widget)

        actions = self.initActions()
        self.initMenus(actions)

        self.statusBar().showMessage(str(self.tr("%s started.")) % __appname__)
        self.statusBar().show()
        
        self.restoreSettings()
    
    def initActions(self):
        actions = {}
        action = functools.partial(utils.newAction, self)
        shortcuts = self._config["shortcuts"]

        actions['quit'] = action(
            self.tr("&Quit"),
            self.close,
            shortcuts["quit"],
            "quit",
            self.tr("Quit application"),
        )

        return actions

    def initMenus(self, actions):
        self.menus = utils.struct(
            file=self.menu(self.tr("&File")),
        )

        utils.addActions(
            self.menus.file,
            (
                None,
                actions['quit'],
            ),
        )
    
    def menu(self, title, actions=None):
        menu = self.menuBar().addMenu(title)
        if actions:
            utils.addActions(menu, actions)
        return menu
    
    def restoreSettings(self):
        self.settings = QtCore.QSettings("labelme", "labelme")
        self.recentFiles = self.settings.value("recentFiles", []) or []
        size = self.settings.value("window/size", QtCore.QSize(600, 500))
        position = self.settings.value("window/position", QtCore.QPoint(0, 0))
        state = self.settings.value("window/state", QtCore.QByteArray())
        self.resize(size)
        self.move(position)
        self.restoreState(state)