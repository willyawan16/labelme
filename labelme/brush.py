from qtpy import QtCore
from qtpy import QtGui
from qtpy.QtGui import QImage, QPixmap, QColor, QPainter, QPen
from qtpy.QtCore import QPoint, QPointF

from labelme.logger import logger
import time
import numpy as np

class Brush(object):

    MIN_SIZE = 1
    MAX_SIZE = 256
    DEFAULT_SIZE = 32
    MAX_HISTORY_LEN = 10

    def __init__(self):
        self.brushSize = 1
        self.brushMask = QPixmap()
        self.history = []

        self.pen = QPen(QColor(0, 255, 0))
        self.pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
    
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
        painter = QPainter(self.brushMask)

        if isDraw:
            self.pen.setColor(QColor(0, 255, 0))
        else:
            self.pen.setColor(QColor(0, 0, 0))
        
        #penWidths = [8, 16, 32, 64, 128, 256]
        self.pen.setWidth(self.brushSize)

        painter.setPen(self.pen)

        if prevPoint:
            painter.drawLine(prevPoint, point)
        else:
            painter.drawPoint(point)

    def brushPainter(self, painterx: QPainter, mousePos: QPointF, mode: str):
        painterx.setOpacity(0.4)
        painterx.drawPixmap(0, 0, self.brushMask)

        if mode != "fill":
            if mousePos.x() >= 0 and mousePos.x() <= self.brushMask.width() and mousePos.y() >= 0 and mousePos.y() <= self.brushMask.height():
                if mode == "draw":
                    self.pen.setColor(QColor(0, 255, 0))
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
        self.history.append(self.brushMask.copy())

    def undoStroke(self):
        if self.history is not None and len(self.history) >= 2:
            self.history.pop()
            self.brushMask = self.history[-1].copy()
        else:
            logger.info("No stroke history...")
    
    def fillBucket(self, seedPos: QPoint):
        startTime = time.time()

        img = self.brushMask.toImage()
        ptr = img.bits()
        ptr.setsize(img.byteCount())

        arr = np.asarray(ptr).reshape(img.height(), img.width(), 4)

        if type(seedPos) is QPointF:
            seedPos = QPoint(int(seedPos.x()), int(seedPos.y()))
        stack = []
        processed = set()
        stack.append(seedPos)
        xIt = [-1, 1, 0, 0]
        yIt = [0, 0, -1, 1]

        print(seedPos.x(), ", ", seedPos.y())

        while len(stack) > 0:
            pos = stack.pop(0)

            condition = pos.x() >= 0 and pos.x() < img.width() and pos.y() >= 0 and pos.y() < img.height()
            if not condition:
                continue
            
            if arr[pos.y(), pos.x(), 1] == 0:
                arr[pos.y(), pos.x(), 1] = 255
                processed.add(Brush.pointToTuple(pos))

                for i in range(4):
                    ipos = QPoint(pos.x() + xIt[i], pos.y() + yIt[i])
                    if not (Brush.pointToTuple(ipos) in processed):
                        stack.append(ipos)

        self.brushMask = QPixmap().fromImage(img)

        logger.info("Time taken: " + str(time.time() - startTime))
    
    @staticmethod
    def pointToTuple(point: QPoint):
        return tuple([point.x(), point.y()])