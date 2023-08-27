from qtpy import QtCore
from qtpy import QtGui
from qtpy.QtGui import QPixmap, QColor, QPen

from labelme.logger import logger

class Brush(object):

    MIN_SIZE = 1
    MAX_SIZE = 6
    MAX_HISTORY_LEN = 10

    def __init__(self):
        self.brushSize = 1
        self.brushMask = QPixmap()
        self.history = []
    
    def setSize(self, value) -> int:
        self.brushSize = value
        return self.brushSize
    
    def isUndoable(self) -> bool:
        return len(self.history) > 0

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
    
    def addStrokeToHistory(self):
        logger.info("Add stroke history")
        if len(self.history) >= self.MAX_HISTORY_LEN:
            self.history = self.history[1:]
        self.history.append(self.brushMask.copy())

    def undoStroke(self):
        if self.history is not None and len(self.history) >= 1:
            self.history.pop()
            self.brushMask = self.history[-1].copy()
        else:
            logger.info("No stroke history...")