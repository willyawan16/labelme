from qtpy import QtCore
from qtpy import QtGui
from qtpy.QtGui import QImage, QPixmap, QColor, QPainter, QPen
from qtpy.QtCore import QPoint, QPointF

from labelme.logger import logger
import time
import numpy as np
import random, string

import copy

DEFAULT_PEN_COLOR = QColor(0, 255, 0, 255)
DEFAULT_ERASER_COLOR = QColor(0, 0, 0, 255)
DEFAULT_BG_COLOR = QColor(0, 0, 0, 0)
WHITE_COLOR = QColor(255, 255, 255)

class Brush(object):

    pen_color = DEFAULT_PEN_COLOR

    MIN_SIZE = 1
    MAX_SIZE = 256
    DEFAULT_SIZE = 32
    MAX_HISTORY_LEN = 10
    DEFAULT_OPACITY = 0.82

    def __init__(
        self,
        label=None,
        flags=None,
        group_id=None,
        description=None,):

        self.brushSize = self.DEFAULT_SIZE
        self.brushMaskBG = QPixmap()
        self.brushMaskDraft = QPixmap()
        self.brushMaskCopy = QImage()
        self.history = []
        self.label = label
        self.group_id = group_id
        self.flags = flags
        self.description = description
        self.brushMaskFinal = QPixmap()
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.opacity = self.DEFAULT_OPACITY
        
        self.left = 0
        self.right = 0
        self.top = 0
        self.bottom = 0

        self.pen = QPen(DEFAULT_PEN_COLOR)
        self.pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
    
    def setSize(self, value) -> int:
        self.brushSize = value
        return self.brushSize
    
    def isUndoable(self) -> bool:
        return len(self.history) > 0
    
    
    def setCurrentBrushValue(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.brushMaskFinal = self.brushMaskDraft.copy(x, y, width, height)

    # Temporary
    def initBrushCanvas(self, width: int, height: int, initBoundary: bool = True):
        self.brushMaskDraft = QPixmap(width, height)
        self.brushMaskDraft.fill(DEFAULT_BG_COLOR)
        if initBoundary:
            self.left = width
            self.right = 0
            self.top = height
            self.bottom = 0

    def updateBoundingBox(self, currentPoint: QPoint):
        halfBrushSize = self.brushSize / 2
        xMin = currentPoint.x() - halfBrushSize
        xMax = currentPoint.x() + halfBrushSize
        yMin = currentPoint.y() - halfBrushSize
        yMax = currentPoint.y() + halfBrushSize

        self.left = min(self.left, xMin)
        self.right = max(self.right, xMax)
        self.top = min(self.top, yMin)
        self.bottom = max(self.bottom, yMax)
    
    def updateBoundingBoxWhileFilling(self, x, y):
        self.left = min(self.left, x)
        self.right = max(self.right, x)
        self.top = min(self.top, y)
        self.bottom = max(self.bottom, y)
    
    def getBoundingBox(self):
        return QtCore.QRect(int(self.left), int(self.top), int(self.right - self.left), int(self.bottom - self.top))

    def drawToBrushCanvas(self, isDraw, point, prevPoint=None):
        painter = QPainter(self.brushMaskDraft)

        if isDraw:
            self.pen.setColor(self.pen_color)
        else:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
            self.pen.setColor(DEFAULT_ERASER_COLOR)
        
        self.pen.setWidth(self.brushSize)

        painter.setPen(self.pen)

        if prevPoint:
            painter.drawLine(prevPoint, point)
        else:
            painter.drawPoint(point)
    
    def resetCanvasDraft(self):
        self.brushMaskDraft.fill(DEFAULT_BG_COLOR)
    
    def pasteToBrushCanvas(self, otherBrushData):
        painter = QtGui.QPainter(self.brushMaskDraft)
        painter.setOpacity(0.6)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
        painter.setPen(otherBrushData.pen_color)
        painter.drawPixmap(otherBrushData.x, otherBrushData.y, otherBrushData.brushMaskFinal)
        painter.setOpacity(1)

    def brushPainter(self, currentPainter: QPainter, mousePos: QPointF, mode: str, opacity: float = 0.6):
        currentPainter.setOpacity(opacity)
        currentPainter.drawPixmap(0, 0, self.brushMaskDraft)

        if mode in ("draw", "erase"):
            if mousePos.x() >= 0 and mousePos.x() <= self.brushMaskDraft.width() and mousePos.y() >= 0 and mousePos.y() <= self.brushMaskDraft.height():
                if mode == "draw":
                    self.pen.setColor(self.pen_color)
                else:
                    self.pen.setColor(WHITE_COLOR)
                self.pen.setWidth(self.brushSize) 
                currentPainter.setPen(self.pen)
                currentPainter.drawPoint(mousePos)

        currentPainter.setOpacity(1)
    
    def addStrokeToHistory(self):
        logger.info("Add stroke history")
        if len(self.history) >= self.MAX_HISTORY_LEN:
            self.history = self.history[1:]
        self.history.append(self.brushMaskDraft.copy())

    def undoStroke(self):
        if self.history is not None and len(self.history) >= 2:
            self.history.pop()
            self.brushMaskDraft = self.history[-1].copy()
        else:
            logger.info("No stroke history...")
    
    def fillBucket(self, seedPos: QPoint):
        startTime = time.time()

        print(seedPos.x(), ", ", seedPos.y())

        img = self.brushMaskDraft.toImage()
        ptr = img.bits()
        ptr.setsize(img.byteCount())
        w, h = img.width(), img.height()

        arr = np.asarray(ptr).reshape(h, w, 4)

        have_seen = set()
        queue = [(int(seedPos.x()), int(seedPos.y()))]

        def get_points(have_seen, pos):
            points = []
            cx, cy = pos
            for x, y in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                xx, yy = cx + x, cy + y
                if xx >= 0 and xx < w and yy >= 0 and yy < h and (xx, yy) not in have_seen:
                    points.append((xx, yy))
                    have_seen.add((xx, yy))
            return points

        while queue:
            x, y = queue.pop()
            if arr[y, x, 1] == 0:
                arr[y, x, 1] = 255
                arr[y, x, 3] = 255
                queue[0:0] = get_points(have_seen, (x, y))
                self.updateBoundingBoxWhileFilling(x, y)

        self.brushMaskDraft = QPixmap().fromImage(img)

        logger.info("Time taken: " + str(time.time() - startTime))

    def moveBy(self, offset: QPoint):
        self.x += int(offset.x())
        self.y += int(offset.y())
        self.left += int(offset.x())
        self.right += int(offset.x())
        self.top += int(offset.y())
        self.bottom += int(offset.y())
        # print(self.x, self.y)
    
    def copy(self):
        return copy.copy(self)