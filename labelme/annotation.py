import functools
import html
import math
import imgviz
import os.path as osp
import re

from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy import QtGui
from qtpy import QtWidgets

from . import utils
from labelme.ai import MODELS
from labelme.brush import Brush, DEFAULT_PEN_COLOR
from labelme.config import get_config
from labelme.label_file import LabelFile
from labelme.logger import logger
from labelme.widgets import BrightnessContrastDialog
from labelme.widgets import Canvas
from labelme.widgets import ImageList
from labelme.widgets import LabelDialog
from labelme.widgets import LabelListWidget
from labelme.widgets import LabelListWidgetItem
from labelme.shape import Shape
from labelme.widgets import ToolBar
from labelme.widgets import UniqueLabelQListWidget
from labelme.widgets import ZoomWidget

LABEL_COLORMAP = imgviz.label_colormap()

class Annotation(QtWidgets.QWidget):

    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = 0, 1, 2

    def __init__(
        self,
        parent,
        config=None,
        filename=None,
    ):
        super(Annotation, self).__init__(parent)

        # see labelme/config/default_config.yaml for valid configuration
        if config is None:
            config = get_config()
        self._config = config

        # set default shape colors
        Shape.line_color = QtGui.QColor(*self._config["shape"]["line_color"])
        Shape.fill_color = QtGui.QColor(*self._config["shape"]["fill_color"])
        Shape.select_line_color = QtGui.QColor(
            *self._config["shape"]["select_line_color"]
        )
        Shape.select_fill_color = QtGui.QColor(
            *self._config["shape"]["select_fill_color"]
        )
        Shape.vertex_fill_color = QtGui.QColor(
            *self._config["shape"]["vertex_fill_color"]
        )
        Shape.hvertex_fill_color = QtGui.QColor(
            *self._config["shape"]["hvertex_fill_color"]
        )
        Shape.point_size = self._config["shape"]["point_size"]
        
        def initAIModel(self):
            selectAiModel = QtWidgets.QWidgetAction(self)
            selectAiModel.setDefaultWidget(QtWidgets.QWidget())
            selectAiModel.defaultWidget().setLayout(QtWidgets.QVBoxLayout())
            self._selectAiModelComboBox = QtWidgets.QComboBox()
            selectAiModel.defaultWidget().layout().addWidget(
                self._selectAiModelComboBox
            )
            self._selectAiModelComboBox.addItems([model.name for model in MODELS])
            self._selectAiModelComboBox.setCurrentIndex(1)
            self._selectAiModelComboBox.setEnabled(False)
            self._selectAiModelComboBox.currentIndexChanged.connect(
                lambda: self.canvas.initializeAiModel(
                    name=self._selectAiModelComboBox.currentText()
                )
            )
            selectAiModelLabel = QtWidgets.QLabel(self.tr("AI Model"))
            selectAiModelLabel.setAlignment(QtCore.Qt.AlignCenter)
            selectAiModelLabel.setFont(QtGui.QFont(None, 10))
            selectAiModel.defaultWidget().layout().addWidget(selectAiModelLabel)
            return selectAiModel

        def initActions(self):
            action = functools.partial(utils.newAction, self)
            slider = functools.partial(utils.newSlider, self)
            textBox = functools.partial(utils.newTextBox, self)
            shortcuts = self._config["shortcuts"]

            open_ = action(
                self.tr("&Open"),
                self.placeholder,# self.openFile,
                shortcuts["open"],
                "open",
                self.tr("Open image or label file"),
            )
            opendir = action(
                self.tr("&Open Dir"),
                self.placeholder,# self.openDirDialog,
                shortcuts["open_dir"],
                "open",
                self.tr("Open Dir"),
            )
            openNextImg = action(
                self.tr("&Next Image"),
                self.placeholder,# self.openNextImg,
                shortcuts["open_next"],
                "next",
                self.tr("Open next (hold Ctl+Shift to copy labels)"),
                enabled=False,
            )
            openPrevImg = action(
                self.tr("&Prev Image"),
                self.placeholder,# self.openPrevImg,
                shortcuts["open_prev"],
                "prev",
                self.tr("Open prev (hold Ctl+Shift to copy labels)"),
                enabled=False,
            )
            save = action(
                self.tr("&Save"),
                self.placeholder,# self.saveFile,
                shortcuts["save"],
                "save",
                self.tr("Save labels to file"),
                enabled=False,
            )
            saveAs = action(
                self.tr("&Save As"),
                self.placeholder,# self.saveFileAs,
                shortcuts["save_as"],
                "save-as",
                self.tr("Save labels to a different file"),
                enabled=False,
            )

            deleteFile = action(
                self.tr("&Delete File"),
                self.placeholder,# self.deleteFile,
                shortcuts["delete_file"],
                "delete",
                self.tr("Delete current label file"),
                enabled=False,
            )

            changeOutputDir = action(
                self.tr("&Change Output Dir"),
                slot=self.placeholder,# self.changeOutputDirDialog,
                shortcut=shortcuts["save_to"],
                icon="open",
                tip=self.tr("Change where annotations are loaded/saved"),
            )

            saveAuto = action(
                text=self.tr("Save &Automatically"),
                slot=lambda x: self.placeholder,# self.actions.saveAuto.setChecked(x),
                icon="save",
                tip=self.tr("Save automatically"),
                checkable=True,
                enabled=True,
            )
            saveAuto.setChecked(self._config["auto_save"])

            saveWithImageData = action(
                text="Save With Image Data",
                slot=self.placeholder,# self.enableSaveImageWithData,
                tip="Save image data in label file",
                checkable=True,
                checked=self._config["store_data"],
            )

            close = action(
                "&Close",
                self.placeholder,# self.closeFile,
                shortcuts["close"],
                "close",
                "Close current file",
            )

            toggle_keep_prev_mode = action(
                self.tr("Keep Previous Annotation"),
                self.placeholder,# self.toggleKeepPrevMode,
                shortcuts["toggle_keep_prev_mode"],
                None,
                self.tr('Toggle "keep pevious annotation" mode'),
                checkable=True,
            )
            toggle_keep_prev_mode.setChecked(self._config["keep_prev"])

            createMode = action(
                self.tr("Create Polygons"),
                lambda: self.toggleDrawMode(False, createMode="polygon"),
                shortcuts["create_polygon"],
                "objects",
                self.tr("Start drawing polygons"),
                enabled=False,
            )
            createRectangleMode = action(
                self.tr("Create Rectangle"),
                lambda: self.toggleDrawMode(False, createMode="rectangle"),
                shortcuts["create_rectangle"],
                "objects",
                self.tr("Start drawing rectangles"),
                enabled=False,
            )
            createCircleMode = action(
                self.tr("Create Circle"),
                lambda: self.toggleDrawMode(False, createMode="circle"),
                shortcuts["create_circle"],
                "objects",
                self.tr("Start drawing circles"),
                enabled=False,
            )
            createLineMode = action(
                self.tr("Create Line"),
                lambda: self.toggleDrawMode(False, createMode="line"),
                shortcuts["create_line"],
                "objects",
                self.tr("Start drawing lines"),
                enabled=False,
            )
            createPointMode = action(
                self.tr("Create Point"),
                lambda: self.toggleDrawMode(False, createMode="point"),
                shortcuts["create_point"],
                "objects",
                self.tr("Start drawing points"),
                enabled=False,
            )
            createLineStripMode = action(
                self.tr("Create LineStrip"),
                lambda: self.toggleDrawMode(False, createMode="linestrip"),
                shortcuts["create_linestrip"],
                "objects",
                self.tr("Start drawing linestrip. Ctrl+LeftClick ends creation."),
                enabled=False,
            )
            createAiPolygonMode = action(
                self.tr("Create AI-Polygon"),
                lambda: self.toggleDrawMode(False, createMode="ai_polygon"),
                None,
                "objects",
                self.tr("Start drawing ai_polygon. Ctrl+LeftClick ends creation."),
                enabled=False,
            )

            # Brush mode
            brushMode = action(
                self.tr("BrushMode"),                       # Text shown in UI
                lambda: self.toggleBrushMode(),             # Function
                None,                                       # Shortcut
                "objects",                                  # Icon
                self.tr("Toggle on brush mode"),            # Tooltip
                enabled=False,                              # isEnabled?
            )
            brushDrawMode = action(
                self.tr("Draw"),
                lambda: self.toggleBrushMode(True, "draw"),
                None,
                "color-line",
                self.tr("Start painting"),
                enabled=False,
            )
            brushEraseMode = action(
                self.tr("Erase"),
                lambda: self.toggleBrushMode(True, "erase"),
                None,
                "delete",
                self.tr("Start erasing"),
                enabled=False,
            )
            brushFillMode = action(
                self.tr("Fill"),
                lambda: self.toggleBrushMode(True, "fill"),
                None,
                "color",
                self.tr("Start Filling"),
                enabled=False,
            )
            brushSizeSlider = slider(
                self.tr("Set brush size"),
                lambda val: self.updateBrushSize(val),
                minValue=Brush.MIN_SIZE,
                maxValue=Brush.MAX_SIZE,
                defaultValue=Brush.DEFAULT_SIZE,
                enabled=False,
            )
            brushSizeTextBox = textBox(
                lambda val: self.updateBrushSize(val),
                minValue=Brush.MIN_SIZE,
                maxValue=Brush.MAX_SIZE,
                defaultValue=Brush.DEFAULT_SIZE,
                step=1,
                enabled=False
            )
            editMode = action(
                self.tr("Edit Polygons"),
                self.setEditMode,
                shortcuts["edit_polygon"],
                "edit",
                self.tr("Move and edit the selected polygons"),
                enabled=False,
            )
            delete = action(
                self.tr("Delete Polygons"),
                self.deleteSelectedShape,
                shortcuts["delete_polygon"],
                "cancel",
                self.tr("Delete the selected polygons"),
                enabled=False,
            )
            duplicate = action(
                self.tr("Duplicate Polygons"),
                self.duplicateSelectedShape,
                shortcuts["duplicate_polygon"],
                "copy",
                self.tr("Create a duplicate of the selected polygons"),
                enabled=False,
            )
            copy = action(
                self.tr("Copy Polygons"),
                self.copySelectedShape,
                shortcuts["copy_polygon"],
                "copy_clipboard",
                self.tr("Copy selected polygons to clipboard"),
                enabled=False,
            )
            paste = action(
                self.tr("Paste Polygons"),
                self.pasteSelectedShape,
                shortcuts["paste_polygon"],
                "paste",
                self.tr("Paste copied polygons"),
                enabled=False,
            )
            undoLastPoint = action(
                self.tr("Undo last point"),
                self.canvas.undoLastPoint,
                shortcuts["undo_last_point"],
                "undo",
                self.tr("Undo last drawn point"),
                enabled=False,
            )
            removePoint = action(
                text="Remove Selected Point",
                slot=self.removeSelectedPoint,
                shortcut=shortcuts["remove_selected_point"],
                icon="edit",
                tip="Remove selected point from polygon",
                enabled=False,
            )

            undo = action(
                self.tr("Undo"),
                self.undoAction,
                shortcuts["undo"],
                "undo",
                self.tr("Undo last add and edit of shape / undo last action"),
                enabled=False,
            )

            hideAll = action(
                self.tr("&Hide\nPolygons"),
                functools.partial(self.togglePolygons, False),
                icon="eye",
                tip=self.tr("Hide all polygons"),
                enabled=False,
            )
            showAll = action(
                self.tr("&Show\nPolygons"),
                functools.partial(self.togglePolygons, True),
                icon="eye",
                tip=self.tr("Show all polygons"),
                enabled=False,
            )

            # Zooms
            zoom = QtWidgets.QWidgetAction(self)
            zoomBoxLayout = QtWidgets.QVBoxLayout()
            zoomBoxLayout.addWidget(self.zoomWidget)
            zoomLabel = QtWidgets.QLabel("Zoom")
            zoomLabel.setAlignment(Qt.AlignCenter)
            zoomLabel.setFont(QtGui.QFont(None, 10))
            zoomBoxLayout.addWidget(zoomLabel)
            zoom.setDefaultWidget(QtWidgets.QWidget())
            zoom.defaultWidget().setLayout(zoomBoxLayout)
            self.zoomWidget.setWhatsThis(
                str(
                    self.tr(
                        "Zoom in or out of the image. Also accessible with "
                        "{} and {} from the canvas."
                    )
                ).format(
                    utils.fmtShortcut(
                        "{},{}".format(shortcuts["zoom_in"], shortcuts["zoom_out"])
                    ),
                    utils.fmtShortcut(self.tr("Ctrl+Wheel")),
                )
            )
            self.zoomWidget.setEnabled(False)

            zoomIn = action(
                self.tr("Zoom &In"),
                functools.partial(self.addZoom, 1.1),
                shortcuts["zoom_in"],
                "zoom-in",
                self.tr("Increase zoom level"),
                enabled=False,
            )
            zoomOut = action(
                self.tr("&Zoom Out"),
                functools.partial(self.addZoom, 0.9),
                shortcuts["zoom_out"],
                "zoom-out",
                self.tr("Decrease zoom level"),
                enabled=False,
            )
            zoomOrg = action(
                self.tr("&Original size"),
                functools.partial(self.setZoom, 100),
                shortcuts["zoom_to_original"],
                "zoom",
                self.tr("Zoom to original size"),
                enabled=False,
            )
            keepPrevScale = action(
                self.tr("&Keep Previous Scale"),
                self.enableKeepPrevScale,
                tip=self.tr("Keep previous zoom scale"),
                checkable=True,
                checked=self._config["keep_prev_scale"],
                enabled=True,
            )
            fitWindow = action(
                self.tr("&Fit Window"),
                self.setFitWindow,
                shortcuts["fit_window"],
                "fit-window",
                self.tr("Zoom follows window size"),
                checkable=True,
                enabled=False,
            )
            fitWidth = action(
                self.tr("Fit &Width"),
                self.setFitWidth,
                shortcuts["fit_width"],
                "fit-width",
                self.tr("Zoom follows window width"),
                checkable=True,
                enabled=False,
            )
            brightnessContrast = action(
                "&Brightness Contrast",
                self.brightnessContrast,
                None,
                "color",
                "Adjust brightness and contrast",
                enabled=False,
            )
            # Group zoom controls into a list for easier toggling.
            zoomActions = (
                self.zoomWidget,
                zoomIn,
                zoomOut,
                zoomOrg,
                fitWindow,
                fitWidth,
            )
            self.zoomMode = self.FIT_WINDOW
            fitWindow.setChecked(Qt.Checked)
            self.scalers = {
                self.FIT_WINDOW: self.scaleFitWindow,
                self.FIT_WIDTH: self.scaleFitWidth,
                # Set to one to scale to 100% when loading files.
                self.MANUAL_ZOOM: lambda: 1,
            }

            edit = action(
                self.tr("&Edit Label"),
                self.editLabel,
                shortcuts["edit_label"],
                "edit",
                self.tr("Modify the label of the selected polygon"),
                enabled=False,
            )

            fill_drawing = action(
                self.tr("Fill Drawing Polygon"),
                self.canvas.setFillDrawing,
                None,
                "color",
                self.tr("Fill polygon while drawing"),
                checkable=True,
                enabled=True,
            )
            if self._config["canvas"]["fill_drawing"]:
                fill_drawing.trigger()
            
            # Label list context menu.
            labelMenu = QtWidgets.QMenu()
            utils.addActions(labelMenu, (edit, delete))
            self.labelList.setContextMenuPolicy(Qt.CustomContextMenu)
            self.labelList.customContextMenuRequested.connect(
                self.popLabelListMenu
            )

            # Store actions for further handling.
            self.actions = utils.struct(
                saveAuto=saveAuto,
                saveWithImageData=saveWithImageData,
                changeOutputDir=changeOutputDir,
                save=save,
                saveAs=saveAs,
                open=open_,
                close=close,
                deleteFile=deleteFile,
                toggleKeepPrevMode=toggle_keep_prev_mode,
                delete=delete,
                edit=edit,
                duplicate=duplicate,
                copy=copy,
                paste=paste,
                undoLastPoint=undoLastPoint,
                undo=undo,
                removePoint=removePoint,
                brushMode=brushMode,
                brushDrawMode=brushDrawMode,
                brushEraseMode=brushEraseMode,
                brushFillMode=brushFillMode,
                brushSizeSlider=brushSizeSlider,
                brushSizeTextBox=brushSizeTextBox,
                createMode=createMode,
                editMode=editMode,
                createRectangleMode=createRectangleMode,
                createCircleMode=createCircleMode,
                createLineMode=createLineMode,
                createPointMode=createPointMode,
                createLineStripMode=createLineStripMode,
                createAiPolygonMode=createAiPolygonMode,
                zoom=zoom,
                zoomIn=zoomIn,
                zoomOut=zoomOut,
                zoomOrg=zoomOrg,
                keepPrevScale=keepPrevScale,
                fitWindow=fitWindow,
                fitWidth=fitWidth,
                brightnessContrast=brightnessContrast,
                zoomActions=zoomActions,
                openNextImg=openNextImg,
                openPrevImg=openPrevImg,
                fileMenuActions=(open_, opendir, save, saveAs, close, quit),
                tool=(),
                # XXX: need to add some actions here to activate the shortcut
                editMenu=(
                    edit,
                    duplicate,
                    delete,
                    None,
                    undo,
                    undoLastPoint,
                    None,
                    removePoint,
                    None,
                    toggle_keep_prev_mode,
                ),
                # menu shown at right click IN CANVAS RANGE
                menu=(
                    createMode,
                    createRectangleMode,
                    createCircleMode,
                    createLineMode,
                    createPointMode,
                    createLineStripMode,
                    createAiPolygonMode,
                    editMode,
                    edit,
                    duplicate,
                    copy,
                    paste,
                    delete,
                    undo,
                    undoLastPoint,
                    removePoint,
                ),
                # When on open image, the following will be enabled in UI
                onLoadActive=(
                    close,
                    createMode,
                    createRectangleMode,
                    createCircleMode,
                    createLineMode,
                    createPointMode,
                    createLineStripMode,
                    createAiPolygonMode,
                    editMode,
                    brightnessContrast,
                    brushMode
                ),
                onShapesPresent=(saveAs, hideAll, showAll),
            )

            selectAiModel = initAIModel(self)

            self.actions.tool = (
                open_,
                opendir,
                openNextImg,
                openPrevImg,
                save,
                deleteFile,
                None,
                brushMode,
                brushDrawMode,
                brushEraseMode,
                brushFillMode,
                brushSizeSlider,
                brushSizeTextBox,
                None,
                createMode,
                editMode,
                duplicate,
                copy,
                paste,
                delete,
                None,
                undo,
                brightnessContrast,
                zoom,
                fitWidth,
                None,
                selectAiModel,
            )

        def initLabelWidget(self):
            # Main widgets and related state.
            self.labelDialog = LabelDialog(
                parent=self,
                labels=self._config["labels"],
                sort_labels=self._config["sort_labels"],
                show_text_field=self._config["show_label_text_field"],
                completion=self._config["label_completion"],
                fit_to_content=self._config["fit_to_content"],
                flags=self._config["label_flags"],
            )

            self.labelList = LabelListWidget()
            self.lastOpenDir = None

            ##self.labelList.itemSelectionChanged.connect(self.labelSelectionChanged)
            self.labelList.itemDoubleClicked.connect(self.editLabel)
            ##self.labelList.itemChanged.connect(self.labelItemChanged)
            ##self.labelList.itemDropped.connect(self.labelOrderChanged)

            self.uniqLabelList = UniqueLabelQListWidget()
            self.uniqLabelList.setToolTip(
                self.tr(
                    "Select label to start annotating for it. "
                    "Press 'Esc' to deselect."
                )
            )
            if self._config["labels"]:
                for label in self._config["labels"]:
                    item = self.uniqLabelList.createItemFromLabel(label)
                    self.uniqLabelList.addItem(item)
                    rgb = self._get_rgb_by_label(label)
                    self.uniqLabelList.setItemLabel(item, label, rgb)

        def initCanvas(self):
            self.canvas = Canvas(
                epsilon=self._config["epsilon"],
                double_click=self._config["canvas"]["double_click"],
                num_backups=self._config["canvas"]["num_backups"],
                crosshair=self._config["canvas"]["crosshair"],
            )
            self.canvas.zoomRequest.connect(self.zoomRequest)

            self.filename = "C:/AOI/上蓋標記檔/白色上蓋標記檔/13_1_1_8000.jpg"
            self.imageData = LabelFile.load_image_file(self.filename)
            self.image = QtGui.QImage.fromData(self.imageData)
            self.canvas.loadPixmap(QtGui.QPixmap.fromImage(self.image))

            self.canvas.newShape.connect(self.newShape)
            self.canvas.newBrush.connect(self.newBrush)
            self.canvas.brushMoved.connect(self.setDirty)
            self.canvas.shapeMoved.connect(self.setDirty)
            self.canvas.selectionChanged.connect(self.shapeSelectionChanged)
            self.canvas.drawingPolygon.connect(self.toggleDrawingSensitive)

            self.canvas.createBrushClass.connect(self.createBrushClass)
            self.canvas.toggleOverviewBrush.connect(self.toggleBrushMode)

        def initWidgets(self):
            def toolbar(title, actions=None):
                toolbar = ToolBar(title)
                toolbar.setObjectName("%sToolBar" % title)
                toolbar.setOrientation(Qt.Horizontal)
                toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

                if actions:
                    utils.addActions(toolbar, actions)
                return toolbar

            self.layout = QtWidgets.QHBoxLayout(self)
            self.layout.setContentsMargins(0, 0, 0, 0)
            self.layout.setSpacing(1)
            self.setLayout(self.layout)

            # Left widget
            leftWidget = QtWidgets.QWidget()
            leftWidget.layout = QtWidgets.QVBoxLayout(leftWidget)
            leftWidget.layout.setContentsMargins(0, 0, 0, 0)
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
            middleWidget.layout.setContentsMargins(0, 0, 0, 0)
            middleWidget.setLayout(middleWidget.layout)

            self.tools = toolbar("Tools", self.actions.tool)
            middleWidget.layout.addWidget(self.tools)

            self.canvasArea = QtWidgets.QScrollArea()
            self.canvasArea.setWidget(self.canvas)
            self.canvasArea.setWidgetResizable(True)

            self.scrollBars = {
                Qt.Vertical: self.canvasArea.verticalScrollBar(),
                Qt.Horizontal: self.canvasArea.horizontalScrollBar(),
            }
            self.canvas.scrollRequest.connect(self.scrollRequest)

            middleWidget.layout.addWidget(self.canvasArea)

            # Right widget
            rightWidget = QtWidgets.QScrollArea()
            rightWidget.layout = QtWidgets.QVBoxLayout(rightWidget)
            rightWidget.layout.setContentsMargins(0, 0, 0, 0)
            rightWidget.setLayout(rightWidget.layout)

            rightWidget.layout.addWidget(self.labelList)
            rightWidget.layout.addWidget(self.uniqLabelList)

            self.layout.addWidget(leftWidget)
            self.layout.addWidget(middleWidget)
            self.layout.addWidget(rightWidget)

        def initState(self, filename):
            # Whether we need to save or not.
            self.dirty = False
            self._noSelectionSlot = False
            self._copied_shapes = None
            
            self.zoom_level = 100
            self.fit_window = False
            self.zoom_values = {}
            self.brightnessContrast_values = {}
            self.scroll_values = {
                Qt.Horizontal: {},
                Qt.Vertical: {},
            }

            ##
            if False and filename is not None and osp.isdir(filename):
                self.importDirImages(filename, load=False)
            elif False:
                self.filename = filename

        self.zoomWidget = ZoomWidget()
        self.setAcceptDrops(True)
        self.zoomWidget.valueChanged.connect(self.paintCanvas)

        initCanvas(self)

        initLabelWidget(self)

        initActions(self)

        initWidgets(self)

        initState(self, filename)

        self.actions.createMode.setEnabled(True)

    #region CANVAS ACTION

    def toggleDrawMode(self, edit=True, createMode="polygon"):
        self.canvas.setEditing(edit)
        self.canvas.createMode = createMode
        self.toggleBrushMode(False)

        if edit:
            self.actions.createMode.setEnabled(True)
            self.actions.createRectangleMode.setEnabled(True)
            self.actions.createCircleMode.setEnabled(True)
            self.actions.createLineMode.setEnabled(True)
            self.actions.createPointMode.setEnabled(True)
            self.actions.createLineStripMode.setEnabled(True)
            self.actions.createAiPolygonMode.setEnabled(True)
            self._selectAiModelComboBox.setEnabled(False)
        else:
            if createMode == "polygon":
                self.actions.createMode.setEnabled(False)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)
                self.actions.createAiPolygonMode.setEnabled(True)
                self.actions.brushMode.setEnabled(True)
                self._selectAiModelComboBox.setEnabled(False)
            elif createMode == "rectangle":
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(False)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)
                self.actions.createAiPolygonMode.setEnabled(True)
                self._selectAiModelComboBox.setEnabled(False)
            elif createMode == "line":
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(False)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)
                self.actions.createAiPolygonMode.setEnabled(True)
                self._selectAiModelComboBox.setEnabled(False)
            elif createMode == "point":
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(False)
                self.actions.createLineStripMode.setEnabled(True)
                self.actions.createAiPolygonMode.setEnabled(True)
                self._selectAiModelComboBox.setEnabled(False)
            elif createMode == "circle":
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(False)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)
                self.actions.createAiPolygonMode.setEnabled(True)
                self._selectAiModelComboBox.setEnabled(False)
            elif createMode == "linestrip":
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(False)
                self.actions.createAiPolygonMode.setEnabled(True)
                self._selectAiModelComboBox.setEnabled(False)
            elif createMode == "ai_polygon":
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)
                self.actions.createAiPolygonMode.setEnabled(False)
                self.canvas.initializeAiModel(
                    name=self._selectAiModelComboBox.currentText()
                )
                self._selectAiModelComboBox.setEnabled(True)
            else:
                raise ValueError("Unsupported createMode: %s" % createMode)
        self.actions.editMode.setEnabled(not edit)

    def setEditMode(self):
        self.toggleDrawMode(True)

    def toggleDrawingSensitive(self, drawing=True):
        """Toggle drawing sensitive.

        In the middle of drawing, toggling between modes should be disabled.
        """
        self.actions.brushMode.setEnabled(not drawing)
        self.actions.editMode.setEnabled(not drawing)
        self.actions.undoLastPoint.setEnabled(drawing)
        self.actions.undo.setEnabled(not drawing)
        self.actions.delete.setEnabled(not drawing)

    def removeSelectedPoint(self):
        self.canvas.removeSelectedPoint()
        self.canvas.update()
        if not self.canvas.hShape.points:
            self.canvas.deleteShape(self.canvas.hShape)
            self.remLabels([self.canvas.hShape])
            if self.noShapes():
                for action in self.actions.onShapesPresent:
                    action.setEnabled(False)
        self.setDirty()
    
    def undoAction(self):
        if self.canvas.brushing():
            self.canvas.undoBrushStroke()
            self.actions.undo.setEnabled(self.canvas.isBrushUndoable)
        else:
            self.undoShapeEdit()

    def undoShapeEdit(self):
        logger.info("Undo shape edit")
        self.canvas.restoreShape()
        self.labelList.clear()
        self.loadShapes(self.canvas.shapes)
        self.actions.undo.setEnabled(self.canvas.isShapeRestorable)
    
    def togglePolygons(self, value):
        for item in self.labelList:
            item.setCheckState(Qt.Checked if value else Qt.Unchecked)

    def shapeSelectionChanged(self, selected_shapes):
        self._noSelectionSlot = True
        for shape in self.canvas.selectedShapes:
            shape.selected = False
        self.labelList.clearSelection()
        self.canvas.selectedShapes = selected_shapes
        for shape in self.canvas.selectedShapes:
            shape.selected = True
            item = self.labelList.findItemByShape(shape)
            self.labelList.selectItem(item)
            self.labelList.scrollToItem(item)
        self._noSelectionSlot = False
        n_selected = len(selected_shapes)
        self.actions.delete.setEnabled(n_selected)
        self.actions.duplicate.setEnabled(n_selected)
        self.actions.copy.setEnabled(n_selected)
        self.actions.edit.setEnabled(n_selected == 1)

    #endregion CANVAS ACTION

    #region BRUSH

    def createBrushClass(self):
        self.canvas.currentBrush = Brush()
        self.canvas.currentBrush.initBrushCanvas(self.image.width(), self.image.height())

    def toggleBrushMode(self, brush=True, brushMode="none"):
        if brushMode == "none":
            self.canvas.setToBrush(brush)
        else:
            self.canvas.setToBrushCreate(brush)
            
        self.canvas.brushMode = brushMode
        # self.canvas.prevBrushMask = self.canvas.brush.brushMask.copy()

        if brush:
            logger.info("Brush mode: " + brushMode + " activated!")

            self.actions.createMode.setEnabled(True)
            self.actions.createRectangleMode.setEnabled(True)
            self.actions.createCircleMode.setEnabled(True)
            self.actions.createLineMode.setEnabled(True)
            self.actions.createPointMode.setEnabled(True)
            self.actions.createLineStripMode.setEnabled(True)
            self.actions.createAiPolygonMode.setEnabled(True)
            self.actions.editMode.setEnabled(True)
            self._selectAiModelComboBox.setEnabled(False)
            self.actions.brushMode.setEnabled(False)
            self.actions.brushSizeSlider.setEnabled(True)
            self.actions.brushSizeTextBox.setEnabled(True)
            self.actions.undo.setEnabled(self.canvas.isBrushUndoable)

            self.actions.brushDrawMode.setEnabled(brushMode != "draw")
            self.actions.brushEraseMode.setEnabled(brushMode != "erase")
            self.actions.brushFillMode.setEnabled(brushMode != "fill")

            if brushMode is not "none" and not self.canvas.currentBrush:
                self.createBrushClass()
        else:
            logger.info("Brush mode deactivated!")

            self.actions.brushMode.setEnabled(True)
            self.actions.brushDrawMode.setEnabled(False)
            self.actions.brushEraseMode.setEnabled(False)
            self.actions.brushFillMode.setEnabled(False)
            self.actions.brushSizeSlider.setEnabled(False)
            self.actions.brushSizeTextBox.setEnabled(False)
            self.actions.undo.setEnabled(self.canvas.isShapeRestorable)
        # init canvas
        self.canvas.repaint()

    def updateBrushSize(self, value):
        if type(self.actions) is utils.struct:
            self.actions.brushSizeSlider.setValue(value)
            self.actions.brushSizeTextBox.setValue(value)
        if type(self.canvas.currentBrush) is Brush:
            self.canvas.currentBrush.setSize(value)
    
    def newBrush(self):
        """Pop-up and give focus to the label editor.

        position MUST be in global coordinates.
        """
        items = self.uniqLabelList.selectedItems()
        text = None
        if items:
            text = items[0].data(Qt.UserRole)
        flags = {}
        group_id = None
        description = ""
        if self._config["display_label_popup"] or not text:
            previous_text = self.labelDialog.edit.text()
            text, flags, group_id, description = self.labelDialog.popUp(text)
            if not text:
                self.labelDialog.edit.setText(previous_text)

        if text and not self.validateLabel(text):
            self.errorMessage(
                self.tr("Invalid label"),
                self.tr("Invalid label '{}' with validation type '{}'").format(
                    text, self._config["validate_label"]
                ),
            )
            text = ""
        if text:
            self.labelList.clearSelection()
            brush = self.canvas.setLastLabelForBrush(text, flags)
            brush.group_id = group_id
            brush.description = description
            self.addLabelFromBrush(brush)
            logger.info("tes")
            for i in range(len(self.canvas.brushes)):
                logger.info(str(self.canvas.brushes[i].pen_color.red()))
                logger.info(str(self.canvas.brushes[i].pen_color.green()))
                logger.info(str(self.canvas.brushes[i].pen_color.blue()))

            # self.actions.editMode.setEnabled(True)
            # self.actions.undoLastPoint.setEnabled(False)
            # self.actions.undo.setEnabled(True)
            # self.setDirty()
            pass
        else:
            # self.canvas.undoLastLine()
            # self.canvas.shapesBackups.pop()
            pass
    
    def loadBrushMask(self):
        data = QtCore.QByteArray.fromBase64(self.labelFile.b64brushMask)
        self.canvas.currentBrush.brushMask.loadFromData(data, "PNG")
        self.canvas.update()

    #endregion BRUSH

    #region SHAPE

    def newShape(self):
        """Pop-up and give focus to the label editor.

        position MUST be in global coordinates.
        """
        items = self.uniqLabelList.selectedItems()
        text = None
        if items:
            text = items[0].data(Qt.UserRole)
        flags = {}
        group_id = None
        description = ""
        if self._config["display_label_popup"] or not text:
            previous_text = self.labelDialog.edit.text()
            text, flags, group_id, description = self.labelDialog.popUp(text)
            if not text:
                self.labelDialog.edit.setText(previous_text)

        if text and not self.validateLabel(text):
            self.errorMessage(
                self.tr("Invalid label"),
                self.tr("Invalid label '{}' with validation type '{}'").format(
                    text, self._config["validate_label"]
                ),
            )
            text = ""
        if text:
            self.labelList.clearSelection()
            shape = self.canvas.setLastLabel(text, flags)
            shape.group_id = group_id
            shape.description = description
            self.addLabel(shape)
            self.actions.editMode.setEnabled(True)
            self.actions.undoLastPoint.setEnabled(False)
            self.actions.undo.setEnabled(True)
            self.setDirty()
        else:
            self.canvas.undoLastLine()
            self.canvas.shapesBackups.pop()

    def duplicateSelectedShape(self):
        added_shapes = self.canvas.duplicateSelectedShapes()
        self.labelList.clearSelection()
        for shape in added_shapes:
            self.addLabel(shape)
        self.setDirty()

    def pasteSelectedShape(self):
        self.loadShapes(self._copied_shapes, replace=False)
        self.setDirty()

    def copySelectedShape(self):
        self._copied_shapes = [s.copy() for s in self.canvas.selectedShapes]
        self.actions.paste.setEnabled(len(self._copied_shapes) > 0)

    def deleteSelectedShape(self):
        yes, no = QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No
        msg = self.tr(
            "You are about to permanently delete {} polygons, "
            "proceed anyway?"
        ).format(len(self.canvas.selectedShapes))
        if yes == QtWidgets.QMessageBox.warning(
            self, self.tr("Attention"), msg, yes | no, yes
        ):
            self.remLabels(self.canvas.deleteSelected())
            self.setDirty()
            if self.noShapes():
                for action in self.actions.onShapesPresent:
                    action.setEnabled(False)

    def copyShape(self):
        self.canvas.endMove(copy=True)
        for shape in self.canvas.selectedShapes:
            self.addLabel(shape)
        self.labelList.clearSelection()
        self.setDirty()

    def moveShape(self):
        self.canvas.endMove(copy=False)
        self.setDirty()

    #endregion SHAPE

    #region LABEL

    def addLabel(self, shape):
        if shape.group_id is None:
            text = shape.label
        else:
            text = "{} ({})".format(shape.label, shape.group_id)

        label_list_item = LabelListWidgetItem(text, shape)
        self.labelList.addItem(label_list_item)
        if self.uniqLabelList.findItemByLabel(shape.label) is None:
            item = self.uniqLabelList.createItemFromLabel(shape.label)
            self.uniqLabelList.addItem(item)
            rgb = self._get_rgb_by_label(shape.label)
            self.uniqLabelList.setItemLabel(item, shape.label, rgb)
        self.labelDialog.addLabelHistory(shape.label)
        for action in self.actions.onShapesPresent:
            action.setEnabled(True)

        self._update_shape_color(shape)
        label_list_item.setText(
            '{} <font color="#{:02x}{:02x}{:02x}">●</font>'.format(
                html.escape(text), *shape.fill_color.getRgb()[:3]
            )
        )

    def addLabelFromBrush(self, brush):
        if brush.group_id is None:
            text = brush.label
        else:
            text = "{} ({})".format(brush.label, brush.group_id)

        label_list_item = LabelListWidgetItem(text, brush)
        self.labelList.addItem(label_list_item)
        if self.uniqLabelList.findItemByLabel(brush.label) is None:
            item = self.uniqLabelList.createItemFromLabel(brush.label)
            self.uniqLabelList.addItem(item)
            rgb = self._get_rgb_by_label(brush.label)
            self.uniqLabelList.setItemLabel(item, brush.label, rgb)
        self.labelDialog.addLabelHistory(brush.label)
        for action in self.actions.onShapesPresent:
            action.setEnabled(True)

        self._update_brush_color(brush)
        label_list_item.setText(
            '{} <font color="#{:02x}{:02x}{:02x}">●</font>'.format(
                html.escape(text), *brush.pen_color.getRgb()[:3]
            )
        )

    def validateLabel(self, label):
        # no validation
        if self._config["validate_label"] is None:
            return True

        for i in range(self.uniqLabelList.count()):
            label_i = self.uniqLabelList.item(i).data(Qt.UserRole)
            if self._config["validate_label"] in ["exact"]:
                if label_i == label:
                    return True
        return False

    def editLabel(self, item=None):
        if item and not isinstance(item, LabelListWidgetItem):
            raise TypeError("item must be LabelListWidgetItem type")

        if not self.canvas.editing():
            return
        if not item:
            item = self.currentItem()
        if item is None:
            return
        shape = item.shape()
        if shape is None:
            return
        text, flags, group_id, description = self.labelDialog.popUp(
            text=shape.label,
            flags=shape.flags,
            group_id=shape.group_id,
            description=shape.description,
        )
        if text is None:
            return
        if not self.validateLabel(text):
            self.errorMessage(
                self.tr("Invalid label"),
                self.tr("Invalid label '{}' with validation type '{}'").format(
                    text, self._config["validate_label"]
                ),
            )
            return
        shape.label = text
        shape.flags = flags
        shape.group_id = group_id
        shape.description = description

        self._update_shape_color(shape)
        if shape.group_id is None:
            item.setText(
                '{} <font color="#{:02x}{:02x}{:02x}">●</font>'.format(
                    html.escape(shape.label), *shape.fill_color.getRgb()[:3]
                )
            )
        else:
            item.setText("{} ({})".format(shape.label, shape.group_id))
        self.setDirty()
        if self.uniqLabelList.findItemByLabel(shape.label) is None:
            item = self.uniqLabelList.createItemFromLabel(shape.label)
            self.uniqLabelList.addItem(item)
            rgb = self._get_rgb_by_label(shape.label)
            self.uniqLabelList.setItemLabel(item, shape.label, rgb)

    def loadLabels(self, shapes):
        s = []
        for shape in shapes:
            label = shape["label"]
            points = shape["points"]
            shape_type = shape["shape_type"]
            flags = shape["flags"]
            description = shape.get("description", "")
            group_id = shape["group_id"]
            other_data = shape["other_data"]

            if not points:
                # skip point-empty shape
                continue

            shape = Shape(
                label=label,
                shape_type=shape_type,
                group_id=group_id,
                description=description,
            )
            for x, y in points:
                shape.addPoint(QtCore.QPointF(x, y))
            shape.close()

            default_flags = {}
            if self._config["label_flags"]:
                for pattern, keys in self._config["label_flags"].items():
                    if re.match(pattern, label):
                        for key in keys:
                            default_flags[key] = False
            shape.flags = default_flags
            shape.flags.update(flags)
            shape.other_data = other_data

            s.append(shape)
        self.loadShapes(s)

    def remLabels(self, shapes):
        for shape in shapes:
            item = self.labelList.findItemByShape(shape)
            self.labelList.removeItem(item)
    
    def popLabelListMenu(self, point):
        self.menus.labelList.exec_(self.labelList.mapToGlobal(point))

    #endregion LABEL

    def paintCanvas(self):
        assert not self.image.isNull(), "cannot paint null image"
        self.canvas.scale = 0.01 * self.zoomWidget.value()
        self.canvas.adjustSize()
        self.canvas.update()

    #region SCROOL ZOOM BRIGHTNESS CONTRAST

    def scrollRequest(self, delta, orientation):
        units = -delta * 0.1  # natural scroll
        bar = self.scrollBars[orientation]
        value = bar.value() + bar.singleStep() * units
        self.setScroll(orientation, value)

    def setScroll(self, orientation, value):
        self.scrollBars[orientation].setValue(int(value))
        self.scroll_values[orientation][self.filename] = value
    
    def setZoom(self, value):
        self.actions.fitWidth.setChecked(False)
        self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.MANUAL_ZOOM
        self.zoomWidget.setValue(value)
        self.zoom_values[self.filename] = (self.zoomMode, value)

    def addZoom(self, increment=1.1):
        zoom_value = self.zoomWidget.value() * increment
        if increment > 1:
            zoom_value = math.ceil(zoom_value)
        else:
            zoom_value = math.floor(zoom_value)
        self.setZoom(zoom_value)

    def zoomRequest(self, delta, pos):
        canvas_width_old = self.canvas.width()
        units = 1.1
        if delta < 0:
            units = 0.9
        self.addZoom(units)

        canvas_width_new = self.canvas.width()
        if canvas_width_old != canvas_width_new:
            canvas_scale_factor = canvas_width_new / canvas_width_old

            x_shift = round(pos.x() * canvas_scale_factor) - pos.x()
            y_shift = round(pos.y() * canvas_scale_factor) - pos.y()

            self.setScroll(
                Qt.Horizontal,
                self.scrollBars[Qt.Horizontal].value() + x_shift,
            )
            self.setScroll(
                Qt.Vertical,
                self.scrollBars[Qt.Vertical].value() + y_shift,
            )
    
    def adjustScale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoomMode]()
        value = int(100 * value)
        self.zoomWidget.setValue(value)
        self.zoom_values[self.filename] = (self.zoomMode, value)

    def scaleFitWindow(self):
        """Figure out the size of the pixmap to fit the main widget."""
        e = 2.0  # So that no scrollbars are generated.
        w1 = self.canvasArea.width() - e
        h1 = self.canvasArea.height() - e
        a1 = w1 / h1
        # Calculate a new scale value based on the pixmap's aspect ratio.
        w2 = self.canvas.pixmap.width() - 0.0
        h2 = self.canvas.pixmap.height() - 0.0
        a2 = w2 / h2
        return w1 / w2 if a2 >= a1 else h1 / h2

    def scaleFitWidth(self):
        # The epsilon does not seem to work too well here.
        w = self.canvasArea.width() - 2.0
        return w / self.canvas.pixmap.width()
    
    def setFitWindow(self, value=True):
        if value:
            self.actions.fitWidth.setChecked(False)
        self.zoomMode = self.FIT_WINDOW if value else self.MANUAL_ZOOM
        self.adjustScale()

    def setFitWidth(self, value=True):
        if value:
            self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.FIT_WIDTH if value else self.MANUAL_ZOOM
        self.adjustScale()

    def enableKeepPrevScale(self, enabled):
        self._config["keep_prev_scale"] = enabled
        self.actions.keepPrevScale.setChecked(enabled)

    def onNewBrightnessContrast(self, qimage):
        self.canvas.loadPixmap(
            QtGui.QPixmap.fromImage(qimage), clear_shapes=False
        )

    def brightnessContrast(self, value):
        dialog = BrightnessContrastDialog(
            utils.img_data_to_pil(self.imageData),
            self.onNewBrightnessContrast,
            parent=self,
        )
        brightness, contrast = self.brightnessContrast_values.get(
            self.filename, (None, None)
        )
        if brightness is not None:
            dialog.slider_brightness.setValue(brightness)
        if contrast is not None:
            dialog.slider_contrast.setValue(contrast)
        dialog.exec_()

        brightness = dialog.slider_brightness.value()
        contrast = dialog.slider_contrast.value()
        self.brightnessContrast_values[self.filename] = (brightness, contrast)

    #endregion SCROOL ZOOM BRIGHTNESS CONTRAST
    
    #region OTHERS

    def _update_brush_color(self, brush):
        r, g, b = self._get_rgb_by_label(brush.label)
        brush.pen_color = QtGui.QColor(r, g, b)
        mask = brush.brushMaskFinal.createMaskFromColor(DEFAULT_PEN_COLOR, Qt.MaskOutColor)

        p = QtGui.QPainter(brush.brushMaskFinal)
        p.setPen(QtGui.QColor(r, g, b))
        p.drawPixmap(brush.brushMaskFinal.rect(), mask, mask.rect())
        p.end()


    def _update_shape_color(self, shape):
        r, g, b = self._get_rgb_by_label(shape.label)
        shape.line_color = QtGui.QColor(r, g, b)
        shape.vertex_fill_color = QtGui.QColor(r, g, b)
        shape.hvertex_fill_color = QtGui.QColor(255, 255, 255)
        shape.fill_color = QtGui.QColor(r, g, b, 128)
        shape.select_line_color = QtGui.QColor(255, 255, 255)
        shape.select_fill_color = QtGui.QColor(r, g, b, 155)

    def _get_rgb_by_label(self, label):
        if self._config["shape_color"] == "auto":
            item = self.uniqLabelList.findItemByLabel(label)
            if item is None:
                item = self.uniqLabelList.createItemFromLabel(label)
                self.uniqLabelList.addItem(item)
                rgb = self._get_rgb_by_label(label)
                self.uniqLabelList.setItemLabel(item, label, rgb)
            label_id = self.uniqLabelList.indexFromItem(item).row() + 1
            label_id += self._config["shift_auto_shape_color"]
            return LABEL_COLORMAP[label_id % len(LABEL_COLORMAP)]
        elif (
            self._config["shape_color"] == "manual"
            and self._config["label_colors"]
            and label in self._config["label_colors"]
        ):
            return self._config["label_colors"][label]
        elif self._config["default_shape_color"]:
            return self._config["default_shape_color"]
        return (0, 255, 0)

    #endregion OTHERS

    def setDirty(self):
        pass

    def placeholder(self):
        pass