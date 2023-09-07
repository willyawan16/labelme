from qtpy import QtCore
from qtpy import QtGui
from qtpy.QtGui import QImage, QPixmap, QColor, QPainter, QPen

from labelme.logger import logger

DEFAULT_PEN_COLOR = QColor(0, 255, 0)
DEFAULT_BG_COLOR = QColor(0, 0, 0)

class Brush(object):

    MIN_SIZE = 1
    MAX_SIZE = 256
    MAX_HISTORY_LEN = 10

    pen_color = DEFAULT_PEN_COLOR

    def __init__(
        self, 
        label=None,
        flags=None,
        group_id=None,
        description=None,):

        self.brushSize = 1
        self.brushMask = QPixmap()
        self.brushMaskDraft = QPixmap()
        self.brushMaskCopy = QImage()
        self.history = []
        self.label = label
        self.group_id = group_id
        self.flags = flags
        self.description = description

        self.pen = QPen(QColor(0, 255, 0))
        self.pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
    
    def setSize(self, value) -> int:
        self.brushSize = value
        return self.brushSize
    
    def isUndoable(self) -> bool:
        return len(self.history) > 0

    # Temporary
    def initBrushCanvas(self, width: int, height: int):
        # self.brushMask = QPixmap(width, height)
        # self.brushMask.fill(DEFAULT_BG_COLOR)
        self.brushMaskDraft = QPixmap(width, height)
        self.brushMaskDraft.fill(DEFAULT_BG_COLOR)

    def drawToBrushCanvas(self, isDraw, point, prevPoint=None):
        painter = QtGui.QPainter(self.brushMaskDraft)

        if isDraw:
            self.pen.setColor(self.pen_color)
        else:
            self.pen.setColor(DEFAULT_BG_COLOR)
        
        #penWidths = [8, 16, 32, 64, 128, 256]
        self.pen.setWidth(self.brushSize)

        painter.setPen(self.pen)

        if prevPoint:
            painter.drawLine(prevPoint, point)
        else:
            painter.drawPoint(point)

    def brushPainter(self, painterx: QPainter, mousePos: QtCore.QPointF, isDraw: bool):
        # painterx.setOpacity(0.25)
        # painterx.drawPixmap(0, 0, self.brushMask)
        painterx.setOpacity(0.4)
        painterx.drawPixmap(0, 0, self.brushMaskDraft)

        if mousePos.x() >= 0 and mousePos.x() <= self.brushMaskDraft.width() and mousePos.y() >= 0 and mousePos.y() <= self.brushMaskDraft.height():
            if isDraw:
                self.pen.setColor(self.pen_color)
            else:
                self.pen.setColor(QColor(255, 255, 255))
            self.pen.setWidth(self.brushSize) 
            painterx.setPen(self.pen)
            painterx.drawPoint(mousePos)

        painterx.setOpacity(1)
    
    def addStrokeToHistory(self):
        logger.info("Add stroke history")
        if len(self.history) >= self.MAX_HISTORY_LEN:
            self.history = self.history[1:]
        self.history.append(self.brushMaskDraft.copy())

    def undoStroke(self):
        if self.history is not None and len(self.history) >= 1:
            self.history.pop()
            self.brushMaskDraft = self.history[-1].copy()
        else:
            logger.info("No stroke history...")
    
    def fillBucket(self, seedPos: QtCore.QPoint, init = False):
        if seedPos.x() >= 0 and seedPos.x() <= self.brushMask.width() and seedPos.y() >= 0 and seedPos.y() <= self.brushMask.height():
            if init:
                self.brushMaskCopy = self.brushMask.copy().toImage()

            if self.brushMaskCopy.pixelColor[seedPos] == QColor(0, 0, 0):
                self.brushMaskCopy.setPixelColor(seedPos, QColor(0, 255, 0))

            self.fillBucket(QtCore.QPoint(seedPos.x() - 1, seedPos.y()))
            self.fillBucket(QtCore.QPoint(seedPos.x() + 1, seedPos.y()))
            self.fillBucket(QtCore.QPoint(seedPos.x(), seedPos.y() - 1))
            self.fillBucket(QtCore.QPoint(seedPos.x(), seedPos.y() + 1))