from qtpy import QtCore
from qtpy import QtWidgets

class ToolBar(QtWidgets.QToolBar):
    def __init__(self, title):
        super(ToolBar, self).__init__(title)
        layout = self.layout()
        m = (0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setContentsMargins(*m)
        self.setContentsMargins(*m)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        ##lay = self.findChild(QtWidgets.QLayout)
        ##if lay is not None:
        ##    lay.setExpanded(True)
        QtCore.QTimer.singleShot(0, self.on_timeout)

    @QtCore.Slot()
    def on_timeout(self):
        button = self.findChild(QtWidgets.QToolButton, "qt_toolbar_ext_button")
        if button is not None:
            button.setFixedSize(0, 0)

    def event(self, e):
        if e.type() == QtCore.QEvent.Leave:
            return True
        return super().event(e)

    def addAction(self, action):
        if isinstance(action, QtWidgets.QWidgetAction):
            return super(ToolBar, self).addAction(action)
        btn = QtWidgets.QToolButton()
        btn.setDefaultAction(action)
        btn.setToolButtonStyle(self.toolButtonStyle())
        self.addWidget(btn)

        # center align
        for i in range(self.layout().count()):
            if isinstance(
                self.layout().itemAt(i).widget(), QtWidgets.QToolButton
            ):
                self.layout().itemAt(i).setAlignment(QtCore.Qt.AlignCenter)
    
    def addSlider(self, action: QtWidgets.QSlider):
        label = QtWidgets.QLabel(self.tr("Set brush size"))
        label.setAlignment(QtCore.Qt.AlignCenter)
        action.setBaseSize(240, 24)
        action.setMaximumSize(360, 24)
        self.addWidget(action)
        self.addWidget(label)

        # center align
        for i in range(self.layout().count()):
            if isinstance(
                self.layout().itemAt(i).widget(), QtWidgets.QSlider
            ):
                self.layout().itemAt(i).setAlignment(QtCore.Qt.AlignCenter)
    
    def addTextBox(self, action: QtWidgets.QSpinBox):
        self.addWidget(action)

        # center align
        for i in range(self.layout().count()):
            if isinstance(
                self.layout().itemAt(i).widget(), QtWidgets.QSpinBox
            ):
                self.layout().itemAt(i).setAlignment(QtCore.Qt.AlignCenter)
        
