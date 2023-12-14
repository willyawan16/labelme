import PIL.Image
import PIL.ImageEnhance
from qtpy.QtCore import Qt
from qtpy import QtGui
from qtpy import QtWidgets

from .. import utils


class BrushOptionsDialog(QtWidgets.QDialog):
    def __init__(self, curOpacity, callback, parent=None):
        super(BrushOptionsDialog, self).__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Brush Options")

        self.slider_opacity = self._create_slider(curOpacity)

        formLayout = QtWidgets.QFormLayout()
        formLayout.addRow(self.tr("Opacity"), self.slider_opacity)
        self.setLayout(formLayout)
        self.callback = callback

    def onNewValue(self):
        opacity = self.slider_opacity.value()
        self.callback(opacity)

    def _create_slider(self, curOpacity):
        slider = QtWidgets.QSlider(Qt.Horizontal)
        slider.setRange(50, 210)
        slider.setValue(curOpacity)
        slider.valueChanged.connect(self.onNewValue)
        return slider
