# -*- coding: utf-8 -*-
 
# "BVHPlayerPy" Startup Scripts
# Author: T.Shuhei
# Last Modified: 2017/09/28

import sys
import os
import pickle
from ctypes import windll
from PyQt5.Qt import *

from GLWidget import GLWidget
from InfoWidget import InfoWidget
from ControlWidget import ControlWidget
from SplitWidget import SplitWidget
from python_bvh import BVH

from drawtest import mylable
# from globalWidget import Example


class BVHPlayerPy(QMainWindow):
    def __init__(self, pathCD):
        super().__init__()
        # self.setMaximumSize(800, 500)
        self.resize(1600,600)
        
        self.pathCurrentDir = pathCD
        self.pathMotionFileDir = pathCD.rstrip(os.path.basename(pathCD))

        self.setCentralWidget(self.initComponent())
        menuBar = self.menuBar()
        menuBar.setNativeMenuBar(False)
        # self.setMaximumSize(1600, 900)

        fileMenu = menuBar.addMenu("&File")
        loadAction = QAction("&Open...", self)
        loadAction.triggered.connect(self.loadFile)
        loadAction.setShortcut("Ctrl+l")
        fileMenu.addAction(loadAction)
        playAction = QAction("&Play...",self)
        playAction.triggered.connect(self.playFile)
        playAction.setShortcut("Ctrl+p")
        fileMenu.addAction(playAction)
        quitAction = QAction("&Quit...", self)
        quitAction.triggered.connect(self.quit)
        quitAction.setShortcut("Ctrl+q")
        fileMenu.addAction(quitAction)
        self.setMenuBar(menuBar)
        self.setWindowTitle("BVH Player")

    def initComponent(self):
        self.drawPanel = GLWidget(self)
        self.infoPanel = InfoWidget(self)
        self.controlPanel = ControlWidget(self)
        self.splitterPanel = SplitWidget(self)

        self.globalPanel = mylable(self)

        controlLayout = QVBoxLayout()
        controlLayout.addWidget(self.infoPanel)
        controlLayout.addWidget(self.controlPanel)
        # controlLayout.addWidget(self.globalPanel)
        controlLayout.addWidget(self.splitterPanel)

        subLayout = QVBoxLayout()
        subLayout.addWidget(self.globalPanel)
        

        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.drawPanel)
        
        mainLayout.addLayout(controlLayout)
        mainLayout.addWidget(self.globalPanel)
        
        
        
        mainWidget = QWidget()
        mainWidget.setLayout(mainLayout)
        # mainWidget.setLayout(subLayout)

        return mainWidget

    def quit(self):
        sys.exit()

    def loadFile(self):
        filePath = QFileDialog.getOpenFileName(self, "Choose Motion File...", self.pathMotionFileDir, "Biovision Hierarchy (*.bvh)")
        if filePath[0] == "":
#            print("Error: Motion file is not given")
            pass
        else:
            root, motion, frames, frameTime = BVH.readBVH(filePath[0])
            self.pathMotionFileDir = os.path.dirname(filePath[0])
            self.drawPanel.setMotion(root, motion, frames, frameTime)
            self.infoPanel.initInfo(os.path.basename(filePath[0]), frameTime, frames)
            self.controlPanel.setPlayMode(True)
            self.splitterPanel.setActive()
            self.splitterPanel.initMotionData(os.path.basename(filePath[0]), root, motion, frameTime)

    def playFile(self):
        with open('csv/rank_fln.pkl','rb') as file:
            file_rank=pickle.load(file)
            print(file_rank)
            filePath = 'bvhdata/143_'+str(file_rank[0])+'.bvh'
            root, motion, frames, frameTime = BVH.readBVH(filePath)
            self.pathMotionFileDir = os.path.dirname(filePath)
            self.drawPanel.setMotion(root, motion, frames, frameTime)
            self.infoPanel.initInfo(os.path.basename(filePath), frameTime, frames)
            self.controlPanel.setPlayMode(True)
            self.splitterPanel.setActive()
            self.splitterPanel.initMotionData(os.path.basename(filePath), root, motion, frameTime)

    def keyPressEvent(self, event:QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.quit()
        elif event.key() == Qt.Key_S:
            if self.drawPanel.motion is not None:
                self.drawPanel.isPlaying = not self.drawPanel.isPlaying
                self.controlPanel.setPlayMode(self.drawPanel.isPlaying)
        elif event.key() == Qt.Key_F:
            self.drawPanel.fastRatio *= 2.0
        elif event.key() == Qt.Key_D:
            self.drawPanel.fastRatio /= 2.0
        elif event.key() == Qt.Key_Right:
            if self.drawPanel.frames is not None:
                self.drawPanel.frameCount += 1
                if self.drawPanel.frameCount >= self.drawPanel.frames:
                    self.drawPanel.frameCount = 0
        elif event.key() == Qt.Key_Left:
            if self.drawPanel.frames is not None:
                self.drawPanel.frameCount -= 1
                if self.drawPanel.frameCount < 0:
                    self.drawPanel.frameCount = self.drawPanel.frames - 1
        else:
            pass
        

if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        pathCD = os.path.dirname(sys.executable)
    else:
        pathCD = os.path.dirname(__file__)

    user32 = windll.user32
    user32.SetProcessDPIAware()
    app = QApplication(sys.argv)
    player = BVHPlayerPy(pathCD)
    player.show()
    sys.exit(app.exec_())