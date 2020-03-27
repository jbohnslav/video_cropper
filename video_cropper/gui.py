# from mainwindow import Ui_MainWindow
import sys
from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtWidgets import (QMainWindow, QFileDialog, QMessageBox, QInputDialog, QLabel,
                               QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox)
from PySide2.QtCore import Signal, Slot
import os
from typing import Union
import traceback
from .custom_widgets import Toolbar, VideoPlayer
from .crop import crop_video
import warnings

class MainWindow(QMainWindow):
    def __init__(self, debug: bool = False):
        super().__init__()
        self.debug = debug

        self.toolbar = Toolbar(parent=self)
        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.toolbar)

        self.videoPlayer = VideoPlayer(parent=self)
        mainLayout.addWidget(self.videoPlayer)

        # self.setLayout(mainLayout)
        self.setWindowTitle("Video_cropper")

        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)

        # define variables needed in functions
        self.videofile = None

        # hook up all our signals and slots

        self.overlay = self.videoPlayer.videoView._scene
        self.videoPlayer.videoView.initialized.connect(self.overlay.set_enabled)

        self.toolbar.openVideo.clicked.connect(self.open_avi_browser)
        self.overlay.Height.connect(self.toolbar.update_height)
        self.overlay.Width.connect(self.toolbar.update_width)
        self.overlay.X.connect(self.toolbar.update_x)
        self.overlay.Y.connect(self.toolbar.update_y)
        self.toolbar.Width.connect(self.overlay.change_width)
        self.toolbar.Height.connect(self.overlay.change_height)
        self.toolbar.X.connect(self.overlay.change_x)
        self.toolbar.Y.connect(self.overlay.change_y)
        self.toolbar.cropButton.clicked.connect(self.crop_video)

        self.update()
        # self.ui = Ui_MainWindow()
        # self.ui.setupUi(self)
        # self.ui.openVideo.clicked.connect(self.open_avi_browser)

    def open_avi_browser(self):
        options = QFileDialog.Options()
        filestring = 'VideoReader files (*.h5 *.avi *.mp4)'
        filename, _ = QFileDialog.getOpenFileName(self, "Click on video to open", None,
                                                  filestring, options=options)
        if len(filename) == 0 or not os.path.isfile(filename):
            raise ValueError('Could not open file: {}'.format(filename))

        self.initialize_video(filename)

    def initialize_video(self, videofile: Union[str, os.PathLike]):
        if hasattr(self, 'vid'):
            self.vid.close()
            # if hasattr(self.vid, 'cap'):
            #     self.vid.cap.release()

        self.videofile = videofile
        try:
            self.videoPlayer.videoView.initialize_video(videofile)
            # for convenience extract the videoplayer object out of the videoView
            self.vid = self.videoPlayer.videoView.vid
            # for convenience
            self.n_timepoints = len(self.videoPlayer.videoView.vid)

            # get rid of previous info
            self.overlay.clear_rect()
            self.toolbar.clear_text()
        except BaseException as e:
            print('Error initializing video: {}'.format(e))
            tb = traceback.format_exc()
            print(tb)
            return

    def crop_video(self):
        if self.videofile is None:
            return
        if not self.overlay.has_rect:
            return
        options = QFileDialog.Options()
        directory = os.path.dirname(self.videofile)
        default_name, _ = os.path.splitext(os.path.basename(self.videofile))
        default_name += '_cropped'
        filename, _ = QFileDialog.getSaveFileName(self, 'Video to crop', os.path.join(directory, default_name),
                                                  options=options)
        outfile, _ = os.path.splitext(filename) # ignore what user put in
        selected_format = self.toolbar.exportFormat.currentText()
        movie_format = self.toolbar.formats[selected_format]
        x, y, w, h = self.overlay.get_rect_coords()
        x, y, w, h = int(x), int(y), int(w), int(h)
        if movie_format == 'ffmpeg':
            w, h = self.make_even(x, y, w, h)
        crop_video(self.videofile, outfile, x, y, w, h, movie_format=movie_format)

    def make_even(self, x,y,w,h):
        if (w % 2) == 0 and (h % 2) == 0:
            return w, h
        warnings.warn('with ffmpeg, width and height must be even. adjusting...')
        imw, imh = self.overlay.w, self.overlay.h

        max_y = y + h + 1
        if (w % 2) != 0:
            max_x = x + w + 1
            if max_x > imw:
                w = w - 1
            else:
                w = w + 1
            self.overlay.change_width(float(w))
        if (h % 2) != 0:
            if max_y > imh:
                h = h - 1
            else:
                h = h + 1
            self.overlay.change_height(float(h))
        self.update()
        return w, h





def run():
    app = QtWidgets.QApplication(sys.argv)

    # https://www.wenzhaodesign.com/devblog/python-pyside2-simple-dark-theme
    # button from here https://github.com/persepolisdm/persepolis/blob/master/persepolis/gui/palettes.py
    app.setStyle(QtWidgets.QStyleFactory.create("fusion"))

    darktheme = QtGui.QPalette()
    darktheme.setColor(QtGui.QPalette.Window, QtGui.QColor(45, 45, 45))
    darktheme.setColor(QtGui.QPalette.WindowText, QtGui.QColor(222, 222, 222))
    darktheme.setColor(QtGui.QPalette.Button, QtGui.QColor(45, 45, 45))
    darktheme.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(222, 222, 222))
    darktheme.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(222, 222, 222))
    darktheme.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(222, 222, 222))
    darktheme.setColor(QtGui.QPalette.Highlight, QtGui.QColor(45, 45, 45))
    darktheme.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Light, QtGui.QColor(60, 60, 60))
    darktheme.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Shadow, QtGui.QColor(50, 50, 50))
    darktheme.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText,
                       QtGui.QColor(111, 111, 111))
    darktheme.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, QtGui.QColor(122, 118, 113))
    darktheme.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText,
                       QtGui.QColor(122, 118, 113))
    darktheme.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Base, QtGui.QColor(32, 32, 32))
    # darktheme.setColor(QtGui.QPalette.Background, QtGui.QColor(255,0,0))
    # print(dir(QtGui.QPalette))
    # Define the pallet color
    # Then set the pallet color

    app.setPalette(darktheme)
    window = MainWindow()
    window.resize(1024, 768)
    window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    run()