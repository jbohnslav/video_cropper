from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtWidgets import (QGroupBox, QFormLayout, QLabel, QLineEdit, QVBoxLayout, QWidget, QMainWindow)
from PySide2.QtCore import Qt, Signal, Slot, QPoint
from PySide2.QtGui import QPainter, QBrush, QPen, QPixmap
from typing import Union, Tuple
import os

from .file_io import VideoReader
import numpy as np


def numpy_to_qpixmap(image: np.ndarray) -> QtGui.QPixmap:
    if image.dtype == np.float:
        image = float_to_uint8(image)
    H, W, C = int(image.shape[0]), int(image.shape[1]), int(image.shape[2])
    if C == 4:
        format = QtGui.QImage.Format_RGBA8888
    elif C == 3:
        format = QtGui.QImage.Format_RGB888
    else:
        raise ValueError('Aberrant number of channels: {}'.format(C))
    qpixmap = QtGui.QPixmap(QtGui.QImage(image, W,
                                         H, image.strides[0],
                                         format))
    # print(type(qpixmap))
    return (qpixmap)


def float_to_uint8(image: np.ndarray) -> np.ndarray:
    if image.dtype == np.float:
        image = (image * 255).clip(min=0, max=255).astype(np.uint8)
    # print(image)
    return (image)


def initializer(nframes: int):
    print('initialized with {}'.format(nframes))


class VideoFrame(QtWidgets.QGraphicsView):
    frameNum = Signal(int)
    initialized = Signal(int)

    def __init__(self, videoFile: Union[str, os.PathLike] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.videoView = QtWidgets.QGraphicsView()
        # self._scene = QtWidgets.QGraphicsScene(self)
        self._scene = CroppingOverlay(parent=self)
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._photo)

        # self.videoView.setScene(self._scene)
        self.setScene(self._scene)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(640, 480))
        # self.setObjectName("videoView")

        if videoFile is not None:
            self.initialize_video(videoFile)
            self.update()
        self.setStyleSheet("background:transparent;")

        # print(self.palette())

    def initialize_video(self, videofile: Union[str, os.PathLike]):
        if hasattr(self, 'vid'):
            self.vid.close()
            # if hasattr(self.vid, 'cap'):
            #     self.vid.cap.release()
        self.videofile = videofile
        self.vid = VideoReader(videofile)
        # self.frame = next(self.vid)
        self.initialized.emit(len(self.vid))
        # there was a bug where sometimes subsequent videos with the same frame would not update the image
        self.update_frame(0, force_update=True)

    def update_frame(self, value, force_update: bool=False):
        # print('updating')
        # print('update to: {}'.format(value))
        # print(self.current_fnum)
        # previous_frame = self.current_fnum
        if not hasattr(self, 'vid'):
            return
        value = int(value)
        if hasattr(self, 'current_fnum'):
            if self.current_fnum == value and not force_update:
                # print('already there')
                return
        if value < 0:
            # warnings.warn('Desired frame less than 0: {}'.format(value))
            value = 0
        if value >= self.vid.nframes:
            # warnings.warn('Desired frame beyond maximum: {}'.format(self.vid.nframes))
            value = self.vid.nframes - 1

        self.frame = self.vid[value]

        # the frame in the videoreader is the position of the reader. If you've read frame 0, the current reader
        # position is 1. This makes cv2.CAP_PROP_POS_FRAMES match vid.fnum. However, we want to keep track of our
        # currently displayed image, which is fnum - 1
        self.current_fnum = self.vid.fnum - 1
        # print('new fnum: {}'.format(self.current_fnum))
        self.show_image(self.frame)
        self.frameNum.emit(self.current_fnum)

    def fitInView(self, scale=True):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self._scene.setSceneRect(rect)
            # if self.hasPhoto():
            unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
            self.scale(1 / unity.width(), 1 / unity.height())
            viewrect = self.viewport().rect()
            scenerect = self.transform().mapRect(rect)
            factor = min(viewrect.width() / scenerect.width(),
                         viewrect.height() / scenerect.height())
            # print(factor, viewrect, scenerect)
            self.scale(factor, factor)
            self._zoom = 0

    def adjust_aspect_ratio(self):
        if not hasattr(self, 'vid'):
            raise ValueError('Trying to set GraphicsView aspect ratio before video loaded.')
        if not hasattr(self.vid, 'width'):
            self.vid.width, self.vid.height = self.frame.shape[1], self.frame.shape[0]
        video_aspect = self.vid.width / self.vid.height
        H, W = self.height(), self.width()
        new_width = video_aspect * H
        if new_width < W:
            self.setFixedWidth(new_width)
        new_height = W / self.vid.width * self.vid.height
        if new_height < H:
            self.setFixedHeight(new_height)

    def show_image(self, array):
        qpixmap = numpy_to_qpixmap(array)
        # THIS LINE CHANGES THE SCENE WIDTH AND HEIGHT
        self._photo.setPixmap(qpixmap)

        self.fitInView()
        self.update()
        # self.show()

    def resizeEvent(self, event):
        if hasattr(self, 'vid'):
            self.fitInView()


class ScrollbarWithText(QtWidgets.QWidget):
    position = Signal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.horizontalWidget = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.horizontalWidget.sizePolicy().hasHeightForWidth())
        self.horizontalWidget.setSizePolicy(sizePolicy)
        self.horizontalWidget.setMaximumSize(QtCore.QSize(16777215, 25))
        self.horizontalWidget.setObjectName("horizontalWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalWidget)
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        self.horizontalLayout.setObjectName("horizontalLayout")

        self.horizontalScrollBar = QtWidgets.QScrollBar(self.horizontalWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.horizontalScrollBar.sizePolicy().hasHeightForWidth())
        self.horizontalScrollBar.setSizePolicy(sizePolicy)
        self.horizontalScrollBar.setMaximumSize(QtCore.QSize(16777215, 25))
        self.horizontalScrollBar.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalScrollBar.setObjectName("horizontalScrollBar")
        self.horizontalLayout.addWidget(self.horizontalScrollBar)
        self.plainTextEdit = QtWidgets.QPlainTextEdit(self.horizontalWidget)
        self.plainTextEdit.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plainTextEdit.sizePolicy().hasHeightForWidth())
        self.plainTextEdit.setSizePolicy(sizePolicy)
        self.plainTextEdit.setMaximumSize(QtCore.QSize(100, 25))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.plainTextEdit.setFont(font)
        self.plainTextEdit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.plainTextEdit.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.horizontalLayout.addWidget(self.plainTextEdit)
        self.setLayout(self.horizontalLayout)
        # self.ui.plainTextEdit.textChanged.connect
        self.plainTextEdit.textChanged.connect(self.text_change)
        self.horizontalScrollBar.sliderMoved.connect(self.scrollbar_change)
        self.horizontalScrollBar.valueChanged.connect(self.scrollbar_change)

        self.update()
        # self.show()

    def sizeHint(self):
        return QtCore.QSize(480, 25)

    def text_change(self):
        value = self.plainTextEdit.document().toPlainText()
        value = int(value)
        self.position.emit(value)

    def scrollbar_change(self):
        value = self.horizontalScrollBar.value()
        self.position.emit(value)

    @Slot(int)
    def update_state(self, value: int):
        if self.plainTextEdit.document().toPlainText() != '{}'.format(value):
            self.plainTextEdit.setPlainText('{}'.format(value))

        if self.horizontalScrollBar.value() != value:
            self.horizontalScrollBar.setValue(value)

    @Slot(int)
    def initialize_state(self, value: int):
        # print('nframes: ', value)
        self.horizontalScrollBar.setMaximum(value - 1)
        self.horizontalScrollBar.setMinimum(0)
        # self.horizontalScrollBar.sliderMoved.connect(self.scrollbar_change)
        # self.horizontalScrollBar.valueChanged.connect(self.scrollbar_change)
        self.horizontalScrollBar.setValue(0)
        self.plainTextEdit.setPlainText('{}'.format(0))
        # self.plainTextEdit.textChanged.connect(self.text_change)
        # self.update()


class VideoPlayer(QtWidgets.QWidget):
    # added parent here because python-uic, which turns Qt Creator files into python files, always adds the parent
    # widget. so instead of just saying self.videoPlayer = VideoPlayer(), it does
    # self.videoPlayer = VideoPlayer(self.centralWidget)
    # this just means you are required to pass videoFile as a kwarg
    def __init__(self, parent=None, videoFile: Union[str, os.PathLike] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QVBoxLayout()

        # initialize both widgets and add it to the vertical layout
        self.videoView = VideoFrame(videoFile)
        layout.addWidget(self.videoView)
        self.scrollbartext = ScrollbarWithText()
        layout.addWidget(self.scrollbartext)

        self.setLayout(layout)

        # if you use the scrollbar or the text box, update the video frame
        # self.scrollbartext.horizontalScrollBar.sliderMoved.connect(self.videoView.update_frame)
        # self.scrollbartext.horizontalScrollBar.valueChanged.connect(self.videoView.update_frame)
        # self.scrollbartext.plainTextEdit.textChanged.connect(self.videoView.update_frame)
        self.scrollbartext.position.connect(self.videoView.update_frame)
        self.scrollbartext.position.connect(self.scrollbartext.update_state)

        # if you move the video by any method, update the frame text
        self.videoView.initialized.connect(self.scrollbartext.initialize_state)
        # self.videoView.initialized.connect(initializer)
        self.videoView.frameNum.connect(self.scrollbartext.update_state)

        # I have to do this here because I think emitting a signal doesn't work from within the widget's constructor
        if hasattr(self.videoView, 'vid'):
            self.videoView.initialized.emit(len(self.videoView.vid))

        self.update()


class Toolbar(QtWidgets.QWidget):
    Width = Signal(float)
    Height = Signal(float)
    X = Signal(float)
    Y = Signal(float)

    def __init__(self, parent=None, *args, **kwargs):
        # https://pythonspot.com/pyqt5-form-layout/
        super().__init__(*args, **kwargs)

        self.verticalWidget = QtWidgets.QWidget(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.verticalWidget.setSizePolicy(sizePolicy)
        self.verticalWidget.setMaximumWidth(250)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalWidget)

        self.openVideo = QtWidgets.QPushButton(self.verticalWidget)
        self.openVideo.setMaximumSize(QtCore.QSize(200, 16777215))
        self.openVideo.setObjectName("openVideo")
        self.openVideo.setText('Open Video')

        # self.formGroupBox = QGroupBox('Form Layout')
        self.widget = QtWidgets.QWidget(self.verticalWidget)
        self.widget.setMinimumWidth(125)
        self.widget.setMaximumWidth(250)

        self.widget.setSizePolicy(sizePolicy)
        layout = QFormLayout()
        self.width_edit = QLineEdit()
        self.height_edit = QLineEdit()
        self.x_edit = QLineEdit()
        self.y_edit = QLineEdit()
        layout.addRow(QLabel('X: '), self.x_edit)
        layout.addRow(QLabel('Y: '), self.y_edit)
        layout.addRow(QLabel('Width: '), self.width_edit)
        layout.addRow(QLabel('Height: '), self.height_edit)
        self.widget.setLayout(layout)

        exportWidget = QWidget(self.verticalWidget)
        exportLayout = QFormLayout()
        self.exportFormat = QtWidgets.QComboBox()
        self.formats = {'libx264': 'ffmpeg',
                        'MJPG': 'opencv',
                        'HDF5': 'hdf5',
                        'JPEG folder': 'directory'}
        for fmt in list(self.formats.keys()):
            self.exportFormat.addItem(fmt)
        exportLayout.addRow(QLabel('Format: '), self.exportFormat)
        # self.exportName = QLineEdit()
        # exportLayout.addRow(QLabel('Name: '), self.exportName)
        exportWidget.setSizePolicy(sizePolicy)
        exportWidget.setLayout(exportLayout)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.openVideo)
        mainLayout.addWidget(self.widget)
        mainLayout.addWidget(exportWidget)
        self.cropButton = QtWidgets.QPushButton(text='Crop')
        mainLayout.addWidget(self.cropButton)
        mainLayout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        self.setLayout(mainLayout)
        self.height_edit.returnPressed.connect(self.text_changed)
        self.width_edit.returnPressed.connect(self.text_changed)
        self.x_edit.returnPressed.connect(self.text_changed)
        self.y_edit.returnPressed.connect(self.text_changed)

        self.update()

    @Slot(float)
    def update_height(self, value: float):
        value = int(value)
        current_height = self.height_edit.text()
        if current_height != '{}'.format(value):
            self.height_edit.setText(str(int(value)))

    @Slot(float)
    def update_width(self, value: float):
        value = int(value)
        current_width = self.width_edit.text()
        if current_width != '{}'.format(value):
            self.width_edit.setText(str(int(value)))

    @Slot(float)
    def update_x(self, value: float):
        current_x = self.x_edit.text()
        value = int(value)
        if current_x != '{}'.format(value):
            self.x_edit.setText(str(int(value)))

    @Slot(float)
    def update_y(self, value: float):
        current_y = self.x_edit.text()
        value = int(value)
        if current_y != '{}'.format(value):
            self.y_edit.setText(str(int(value)))

    def text_changed(self):
        x, y, w, h = self.x_edit.text(), self.y_edit.text(), self.width_edit.text(), self.height_edit.text()
        if x != '':
            x = int(x)
            self.X.emit(x)
        if y != '':
            y = int(y)
            self.Y.emit(y)
        if w != '':
            w = int(w)
            self.Width.emit(w)
        if h != '':
            h = int(h)
            self.Height.emit(h)
        # print(x, y, w, h)

    def clear_text(self):
        self.x_edit.setText('')
        self.y_edit.setText('')
        self.width_edit.setText('')
        self.height_edit.setText('')


class CroppingOverlay(QtWidgets.QGraphicsScene):
    # capitalized to not interfere with other variables
    X = Signal(float)
    Y = Signal(float)
    Width = Signal(float)
    Height = Signal(float)

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.border = 10
        self._rect = None
        self._start = None
        self.is_moving = False
        self.is_resizing = False
        self.first = False
        self.w = None
        self.h = None
        self.has_image = False
        self.border_id = None
        self.enabled = False
        self.has_rect = False

    def initialize_rect(self, event):
        if not self.enabled:
            return
        self._rect = QtWidgets.QGraphicsRectItem()
        pen = QPen(Qt.black, 2, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin)
        self._rect.setPen(pen)
        # because of the resizing logic,
        self._rect.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
        self.addItem(self._rect)
        self.first = True

        self._start = event.scenePos()
        r = QtCore.QRectF(self._start, self._start)
        self._rect.setRect(r)
        self.has_rect = True


    def clear_rect(self):
        if self._rect is None:
            return
        self.removeItem(self._rect)
        self._rect = None
        self.has_rect = False


    def mousePressEvent(self, event):
        if not self.has_image:
            return
        # if self.itemAt(event.scenePos(), QtGui.QTransform()) is None:
        if self._rect == None:
            self.initialize_rect(event)
        else:
            is_interior = self.is_click_in_interior(event)
            self.first = False
            if is_interior:
                self.is_moving = True
            else:
                self.border_id = self.get_border_id(event)
                if self.border_id is not None:
                    self.is_resizing = True
        # print(event)

        super().mousePressEvent(event)

    def get_rect_coords(self):
        if self._rect is None:
            return
        rect = self._rect.rect()
        x, y, = rect.topLeft().x(), rect.topLeft().y()
        width, height = rect.width(), rect.height()
        return x, y, width, height

    def is_click_in_interior(self, event):
        if self._rect is None:
            return

        border = self.border

        x, y, width, height = self.get_rect_coords()
        pos = event.scenePos()
        clickx, clicky = pos.x(), pos.y()

        if (clickx < x + width - border and clickx > x + border and
                clicky < y + height - border and clicky > y + border):
            return True
        else:
            return False

    def get_border_id(self, event):
        if self._rect is None:
            return
        border = self.border
        x, y, width, height = self.get_rect_coords()
        pos = event.scenePos()
        clickx, clicky = pos.x(), pos.y()

        border_id = None

        if abs(clickx - x) < border:
            # near the left edge
            if abs(clicky - y) < border:
                border_id = 'top-left'
            elif abs(clicky - (y + height)) < border:
                border_id = 'bottom-left'
            else:
                border_id = 'left'
        elif abs(clickx - (x + width)) < border:
            # near the right edge
            if abs(clicky - y) < border:
                border_id = 'top-right'
            elif abs(clicky - (y + height)) < border:
                border_id = 'bottom-right'
            else:
                border_id = 'right'
        elif abs(clicky - y) < border:
            border_id = 'top'
        elif abs(clicky - (y + height)) < border:
            border_id = 'bottom'

        return border_id

    def emit_rect(self):
        if self._rect is None:
            return
        x, y, w, h = self.get_rect_coords()

        self.X.emit(x)
        self.Y.emit(y)
        self.Width.emit(w)
        self.Height.emit(h)


    def set_rect(self, x, y, w, h):
        if x < 0 or x > self.w:
            return
        if y < 0 or y > self.h:
            return
        if w < 1 or h < 1:
            return
        if not self.is_in_bounds(x, y):
            return
        self._rect.setRect(x, y, w, h)
        self.emit_rect()


    def mouseMoveEvent(self, event):
        if self._rect is None:
            return

        lastx, lasty = event.lastScenePos().x(), event.lastScenePos().y()
        thisx, thisy = event.scenePos().x(), event.scenePos().y()
        dx = thisx - lastx
        dy = thisy - lasty
        x, y, w, h = self.get_rect_coords()
        if self.first:
            r = QtCore.QRectF(self._start, event.scenePos()).normalized()
            self._rect.setRect(r)
            self.emit_rect()
        elif self.is_moving:
            new_x = x + dx
            new_y = y + dy
            self.set_rect(new_x, new_y, w, h)
        elif self.is_resizing:

            if 'left' in self.border_id:
                w = w - dx
                x = x + dx
            if 'top' in self.border_id:
                h = h - dy
                y = y + dy
            if 'bottom' in self.border_id:
                h = h + dy
            if 'right' in self.border_id:
                w = w + dx
            self.set_rect(x, y, w, h)

        super().mouseMoveEvent(event)

    def is_in_bounds(self, new_x, new_y):
        x, y, w, h = self.get_rect_coords()
        image_width, image_height = self.w, self.h
        # print(new_x, w, image_width, image_height)
        if new_x + w < image_width and new_y + h < image_height and new_x >= 0 and new_y >= 0:
            return True
        else:
            return False

    def addItem(self, item):
        # print(item)
        is_image = isinstance(item, QtWidgets.QGraphicsPixmapItem)

        # print(is_image)
        super().addItem(item)
        # self.update()
        if is_image:
            self.has_image = True

    def setSceneRect(self, rect):
        self.w = rect.width()
        self.h = rect.height()
        super().setSceneRect(rect)

    def mouseReleaseEvent(self, event):
        # self._rect = None
        self.is_moving = False
        self.is_resizing = False
        super().mouseReleaseEvent(event)

    @Slot(float)
    def change_width(self, value: float):
        if self._rect is None:
            return
        x, y, w, h = self.get_rect_coords()
        w = int(w)
        value = int(value)
        if w != value:
            # print('changing width in slot from {} to {}. Should happen when text has been changed'.format(w, value))
            self.set_rect(x, y, value, h)

    @Slot(float)
    def change_height(self, value: float):
        if self._rect is None:
            return
        x, y, w, h = self.get_rect_coords()
        h = int(h)
        value = int(value)
        if h != value:
            self.set_rect(x, y, w, value)

    @Slot(float)
    def change_x(self, value: float):
        if self._rect is None:
            return
        x, y, w, h = self.get_rect_coords()
        x = int(x)
        value = int(value)
        if x != value:
            self.set_rect(value, y, w, h)

    @Slot(float)
    def change_y(self, value: float):
        if self._rect is None:
            return
        x, y, w, h = self.get_rect_coords()
        y = int(y)
        value = int(value)
        if y != value:
            self.set_rect(x, value, w, h)

    @Slot(bool)
    def set_enabled(self, value: bool):
        self.enabled = value



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        widget = VideoPlayer(videoFile=r'/home/jb/Downloads/Basler_acA1300-200um__22273960__20200120_113922411.mp4')
        # scene =CroppingOverlay(self)
        # view = QtWidgets.QGraphicsView(scene)
        self.setCentralWidget(widget)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    # testing = VideoPlayer(videoFile=r'/home/jb/Downloads/Basler_acA1300-200um__22273960__20200120_113922411.mp4')
    testing = MainWindow()
    testing.resize(640, 480)
    # volume = VideoPlayer(r'C:\DATA\mouse_reach_processed\M134_20141203_v001.h5')
    # testing = QtWidgets.QMainWindow()
    # testing.initialize(n=6, n_timepoints=15000, debug=True)
    # testing = ShouldRunInference(['M134_20141203_v001',
    #                               'M134_20141203_v002',
    #                               'M134_20141203_v004'],
    #                              [True, True, False])
    # testing = MainWindow()
    # testing.setMaximumHeight(250)
    testing.show()
    app.exec_()
