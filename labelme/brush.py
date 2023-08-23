from qtpy import QtCore
from qtpy import QtGui
from qtpy.QtGui import QPixmap, QColor, QPen

from labelme.logger import logger

class Brush(object):

    MIN_SIZE = 1
    MAX_SIZE = 6

    def __init__(self):
        self.brushSize = 1
        self.brushMask = QPixmap()

    def alterSize(self, incr=1) -> int:
        self.brushSize += incr
        return self.brushSize

    def isBrushIncreasable(self) -> bool:
        return self.brushSize < self.MAX_SIZE
    
    def isBrushDecreasable(self) -> bool:
        return self.brushSize > self.MIN_SIZE

    # Temporary
    def initBrushCanvas(self, width: int, height: int):
        self.brushMask = QPixmap(width, height)
        self.brushMask.fill(QColor(0, 0, 0))

    def drawToBrushCanvas(self, isDraw, point, prevPoint=None):
        painter = QtGui.QPainter(self.brushMask)
        pen = QPen(QColor(0, 0, 0)) # set black to default

        if isDraw:
            pen = QPen(QColor(0, 255, 0))
        else:
            pen = QPen(QColor(0, 0, 0))
        
        penWidths = [8, 16, 32, 64, 128, 256]
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        pen.setWidth(penWidths[self.brushSize - 1])  

        painter.setPen(pen)

        if prevPoint:
            painter.drawLine(prevPoint, point)
        else:
            painter.drawPoint(point)

    def brushPainter(self, painterx: QtGui.QPainter):
        painterx.setOpacity(0.4)
        painterx.drawPixmap(0, 0, self.brushMask)
        painterx.setOpacity(1)