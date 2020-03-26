from mainwindow import Ui_MainWindow
import sys
from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtWidgets import (QMainWindow, QFileDialog, QMessageBox, QInputDialog, QLabel,
                               QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox)
from PySide2.QtCore import Signal, Slot
import os
from typing import Union
import traceback
from custom_widgets import Toolbar, VideoPlayer

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

        # hook up all our signals and slots
        self.toolbar.openVideo.clicked.connect(self.open_avi_browser)
        self.videoPlayer.videoView._scene.Height.connect(self.toolbar.update_height)
        # self.videoPlayer.videoView._scene.Height.connect(self.toolbar.update_height)
        # self.videoPlayer.videoView._scene.Height.connect(self.toolbar.update_height)
        # self.videoPlayer.videoView._scene.Height.connect(self.toolbar.update_height)

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
        except BaseException as e:
            print('Error initializing video: {}'.format(e))
            tb = traceback.format_exc()
            print(tb)
            return

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