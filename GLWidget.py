# -*- coding: utf-8 -*-

# "BVHPlayerPy" OpenGL drawing component
# Author: T.Shuhei
# Last Modified: 2017/09/28

import numpy as np
import time
import pickle

from numpy.core.numeric import _tensordot_dispatcher
import similaritymeasures

from PyQt5.Qt import *
from OpenGL.GL import *
from OpenGL.GLU import *

# from python_bvh import BVHNode, getNodeRoute
from python_bvh import BVHNode, BVH
from writebvh import editBVH
# from editjoint import jointeditBVH

import glm
import math

class GLWidget(QOpenGLWidget):
    frameChanged = pyqtSignal(int)
    InitframeChanged = pyqtSignal(int)
    hParentWidget = None
    checkerBoardSize = 50
    camDist = 500

    coorObj = None
    floorObj = None

    xyObj = None
    zyObj = None
    zxObj = None

    xy = 0.0
    zy = 0.0
    zx = 0.0

    rotateXZ = 0
    rotateY = 45
    translateX = 0
    translateY = 0
    frameCount = 0
    isPlaying = True
    fastRatio = 1.0
    IntiisPlaying = True
    InitfastRatio = 1.0

    scale = 1.0
    root = None
    motion = None
    frames = None
    frameTime = None
    drawMode = 0    # 0:rotation, 1:position

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hParentWidget = parent
        # self.setMinimumSize(500, 500)
        self.resize(500,500)
        self.lastPos = QPoint()
        self.matrixList0 = []
        self.matrixList1 = []
        self.matrixList2 = []
        self.matrixList3 = []
        self.matrixList4 = []
        self.matrixList5 = []
        self.matrixDict = {
            '0': [],
            '5': [], 
            '9': [],
            '13': [],
            '16': [],
            '20': []
        }

        self.canvas = True
        with open('csv/test_pick.pkl','rb') as file:
            self.pkl_stroke = pickle.load(file)
        

        with open('csv/jointpos_pick.pkl','rb') as file:
            self.jointpos = pickle.load(file)   
        # print(self.jointpos) 
        


    def resetCamera(self):
        self.rotateXZ = 0
        self.rotateY = 45
        self.translateX = 0
        self.translateY = 0
        self.camDist = 500

    def canvasShow(self):
        if self.canvas is True:
            self.canvas = False
        else:
            self.canvas = True

    def setInit(self):
        with open('csv/xy.pkl','rb') as file:
           self.xy = pickle.load(file)
        with open('csv/zy.pkl','rb') as file:
           self.zy = pickle.load(file)
        with open('csv/zx.pkl','rb') as file:
           self.zx = pickle.load(file)
        
        # print(self.xy)
        # print(self.zy)
        # print(self.zx)
        file = 'normalized/143_1_n.bvh'
        editBVH(file, self.xy, self.zy, self.zx)



    def setMotion(self, root:BVHNode, motion, frames:int, frameTime:float):
        self.root = root
        self.motion = motion
        self.frames = frames
        self.frameTime = frameTime
        self.frameCount = 0
        self.isPlaying = True
        self.InitisPlaying = False

    # 06.16
    def setInitMotion(self, Initroot:BVHNode, Initmotion, Initframes:int, InitframeTime:float):
        self.Initroot = Initroot
        self.Initmotion = Initmotion
        # print(len(self.Initmotion))
        self.Initframes = Initframes
        self.InitframeTime = InitframeTime
        self.InitframeCount = 0
        self.InitisPlaying = True

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_CONSTANT_ALPHA)
        glEnable(GL_BLEND)
        glClearColor(0.2, 0.2, 0.2, 0)
        # 06.16
        root, motion, frames, frameTime = BVH.readBVH('bvhdata/143_1.bvh')
        self.setInitMotion(root, motion, frames, frameTime)

        self.floorObj = self.makeFloorObject(0)
        self.coorObj = self.makeCoordinate(10)
        self.start = time.time()

    def updateFrame(self):
        if (self.frames is not None) and (self.frameTime is not None):
            # print('play')
            now = time.time()
            if self.isPlaying:
                self.frameCount += int(1 * self.fastRatio) if abs(self.fastRatio) >= 1.0 else 1
                if self.frameCount >= self.frames:
                    self.frameCount = 0
                elif self.frameCount < 0:
                    self.frameCount = self.frames - 1
                self.frameChanged.emit(self.frameCount)

        # 06.16
        if (self.Initframes is not None) and (self.InitframeTime is not None):
            # print('unplay')
            now = time.time()
            if self.InitisPlaying:
                self.InitframeCount += int(1 * self.InitfastRatio) if abs(self.InitfastRatio) >= 1.0 else 1
                if self.InitframeCount >= self.Initframes:
                    self.InitframeCount = 0
                elif self.InitframeCount < 0:
                    self.InitframeCount = self.Initframes - 1
                self.InitframeChanged.emit(self.InitframeCount)
        self.update()
        self.hParentWidget.infoPanel.updateFrameCount(self.frameCount)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        qs = self.sizeHint()
        gluPerspective(60.0, float(qs.width()) / float(qs.height()), 1.0, 1000.0)
        camPx = self.camDist * np.cos(self.rotateXZ / 180.0)
        camPy = self.camDist * np.tanh(self.rotateY / 180.0)
        camPz = self.camDist * np.sin(self.rotateXZ / 180.0)
        transX = self.translateX * -np.sin(self.rotateXZ / 180.0)
        transZ = self.translateX * np.cos(self.rotateXZ / 180.0)
        gluLookAt(camPx + transX, camPy + self.translateY, camPz + transZ, transX, self.translateY, transZ, 0.0, 1.0, 0.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glCallList(self.floorObj)
        glCallList(self.coorObj)

        # 06.16
        with open('csv/xy.pkl','rb') as file:
           self.xy = pickle.load(file)
        with open('csv/zy.pkl','rb') as file:
           self.zy = pickle.load(file)
        with open('csv/zx.pkl','rb') as file:
           self.zx = pickle.load(file)
        
        if self.canvas is True:
            self.xyObj = self.makexyObj(self.xy)
            self.zyObj = self.makezyObj(self.zy)
            self.zxObj = self.makezxObj(self.zx)
            glCallList(self.xyObj)
            glCallList(self.zyObj)
            glCallList(self.zxObj)

        if  self.InitisPlaying:
            self.drawInitSkeleton()
        

        self.drawSkeleton()
        # zhao
        self.drawTrajectory()
        
        # self.drawTraLine()
        glPopMatrix()
        glFlush()
#        self.update()
        self.updateFrame()

    def drawTraLine(self):
        for i in range(0,23):
            if i == 5 or i == 9 or i == 13 or i == 16 or i == 20:
                for m in self.matrixDict[str(i)]:
                    matrix = m.T
                    # print(matrix)
                    # for a in range(len(matrix)):
                    #     if a > 0 :
                    #         glColor3f(0.000, 1.052, 0.000)
                    #         glBegin(GL_LINES)
                    #         glVertex3f(matrix[a])
                    #         glVertex3f(matrix[a-1])
                    #         glEnd()

    def drawTrajectory(self):
        def _RenderJoint(quadObj):
            if quadObj is None:
                quadObj = GLUQuadric()
            gluQuadricDrawStyle(quadObj, GLU_FILL)
            gluQuadricNormals(quadObj, GLU_SMOOTH)

            if self.drawMode == 0:  # rotation mode
                glColor3f(1.000, 0.271, 0.000)
            else:                   # position mode
                glColor3f(0.000, 1.052, 0.000)

            gluSphere(quadObj, 3.0, 16, 16)            

            if self.drawMode == 0:  # rotation mode
                glColor3f(1.000, 0.549, 0.000)
            else:                   # position mode
                glColor3f(0.000, 1.000, 0.000)

        if (self.root is not None) and (self.motion is not None):
            # for m in self.matrixList:
            #     glPushMatrix()
            #     matrix = m.T
            #     glMultMatrixd((matrix[0, 0], matrix[1, 0], matrix[2, 0], matrix[3, 0], matrix[0, 1], matrix[1, 1], matrix[2, 1], matrix[3, 1],
            #                 matrix[0, 2], matrix[1, 2], matrix[2, 2], matrix[3, 2], matrix[0, 3], matrix[1, 3], matrix[2, 3], matrix[3, 3]))
            #     quadObj = None
            #     _RenderJoint(quadObj)
            #     glPopMatrix()
            for i in range(0,23):
                if i ==0 or i == 5 or i == 9 or i == 13 or i == 16 or i == 20:
                    for m in self.matrixDict[str(i)]:
                        glPushMatrix()
                        matrix = m.T
                        # print(matrix)
                        glMultMatrixd((matrix[0, 0], matrix[1, 0], matrix[2, 0], matrix[3, 0], matrix[0, 1], matrix[1, 1], matrix[2, 1], matrix[3, 1],
                                    matrix[0, 2], matrix[1, 2], matrix[2, 2], matrix[3, 2], matrix[0, 3], matrix[1, 3], matrix[2, 3], matrix[3, 3]))
                        quadObj = None
                        _RenderJoint(quadObj)
                        glPopMatrix()

    def drawSkeleton(self):
        def _RenderBone(quadObj, x0, y0, z0, x1, y1, z1):
            dir = [x1 - x0, y1 - y0, z1 - z0]
            boneLength = np.sqrt(dir[0]**2 + dir[1]**2 + dir[2]**2)

            if quadObj is None:
                quadObj = GLUQuadric()
            gluQuadricDrawStyle(quadObj, GLU_FILL)
            gluQuadricNormals(quadObj, GLU_SMOOTH)

            glPushMatrix()
            glTranslated(x0, y0, z0)

            length = np.sqrt(dir[0]**2 + dir[1]**2 + dir[2]**2)
            if length < 0.0001:
                dir = [0.0, 0.0, 1.0]
                length = 1.0
            dir = [data / length for data in dir]            
            
#            up   = [0.0, 1.0, 0.0]
#            side = [up[1]*dir[2] - up[2]*dir[1], up[2]*dir[0] - up[0]*dir[2], up[0]*dir[1] - up[1]*dir[0]]
            side = [dir[2], 0.0, -dir[0]]
            length = np.sqrt(side[0]**2 + side[1]**2 + side[2]**2)
            if length < 0.0001:
                side = [1.0, 0.0, 0.0]
                length = 1.0
            side = [data / length for data in side]

            up = [dir[1]*side[2] - dir[2]*side[1], dir[2]*side[0] - dir[0]*side[2], dir[0]*side[1] - dir[1]*side[0]]
            glMultMatrixd((side[0], side[1], side[2], 0.0,
                             up[0],   up[1],   up[2], 0.0,
                            dir[0],  dir[1],  dir[2], 0.0,
                               0.0,     0.0,     0.0, 1.0))
            radius = 1.5
            slices = 8
            stack = 1
            gluCylinder(quadObj, radius, radius, boneLength, slices, stack)
            glPopMatrix()

        def _RenderJoint(quadObj):
            if quadObj is None:
                quadObj = GLUQuadric()
            gluQuadricDrawStyle(quadObj, GLU_FILL)
            gluQuadricNormals(quadObj, GLU_SMOOTH)

            if self.drawMode == 0:  # rotation mode
                glColor3f(1.000, 0.271, 0.000)
            else:                   # position mode
                glColor3f(0.000, 1.052, 0.000)

            gluSphere(quadObj, 3.0, 16, 16)            

            if self.drawMode == 0:  # rotation mode
                glColor3f(1.000, 0.549, 0.000)
            else:                   # position mode
                glColor3f(0.000, 1.000, 0.000)

        def _RenderFigure(node:BVHNode):
            quadObj = None
            glPushMatrix()
            if self.drawMode == 0:
                # Translate
                if node.nodeIndex == 0:     # ROOT
                    glTranslatef(self.motion[self.frameCount][0] * self.scale,
                                 self.motion[self.frameCount][1] * self.scale,
                                 self.motion[self.frameCount][2] * self.scale)
                    # glTranslatef(self.zy * self.scale,
                    #              self.zx * self.scale,
                    #              self.xy * self.scale)
                else:   # general node
                    glTranslatef(node.offset[0] * self.scale, node.offset[1] * self.scale, node.offset[2] * self.scale)

                # Rotation
                # 07.13
                for i, channel in enumerate(node.chLabel):
                    if "Xrotation" in channel:
                        glRotatef(self.motion[self.frameCount-1][node.frameIndex + i], 1.0, 0.0, 0.0)
                    elif "Yrotation" in channel:
                        glRotatef(self.motion[self.frameCount-1][node.frameIndex + i], 0.0, 1.0, 0.0)
                    elif "Zrotation" in channel:
                        glRotatef(self.motion[self.frameCount-1][node.frameIndex + i], 0.0, 0.0, 1.0)
                # for i, channel in enumerate(node.chLabel):
                #     if "Xrotation" in channel:
                #         glRotatef(self.motion[self.frameCount][node.frameIndex + i], 1.0, 0.0, 0.0)
                #     elif "Yrotation" in channel:
                #         glRotatef(self.motion[self.frameCount][node.frameIndex + i], 0.0, 1.0, 0.0)
                #     elif "Zrotation" in channel:
                #         glRotatef(self.motion[self.frameCount][node.frameIndex + i], 0.0, 0.0, 1.0)
                

                if (node.nodeIndex == 0 and len(self.matrixList1) < self.frames):
                    currentModelView = np.array(glGetFloatv(GL_MODELVIEW_MATRIX))
                    self.matrixList1.append(currentModelView)
                    self.matrixDict['0'] = self.matrixList1
                    # print(self.matrixDict)
                # elif (node.nodeIndex == 9 and len(self.matrixList2) < self.frames):
                #     currentModelView = np.array(glGetFloatv(GL_MODELVIEW_MATRIX))
                #     self.matrixList2.append(currentModelView)
                #     self.matrixDict['9'] = self.matrixList2
                #     # print(self.matrixDict)
                # elif (node.nodeIndex == 13 and len(self.matrixList3) < self.frames):
                #     currentModelView = np.array(glGetFloatv(GL_MODELVIEW_MATRIX))
                #     self.matrixList3.append(currentModelView)
                #     self.matrixDict['13'] = self.matrixList3
                #     # print(self.matrixDict)
                # elif (node.nodeIndex == 16 and len(self.matrixList4) < self.frames):
                #     currentModelView = np.array(glGetFloatv(GL_MODELVIEW_MATRIX))
                #     self.matrixList4.append(currentModelView)
                #     self.matrixDict['16'] = self.matrixList4
                #     # print(self.matrixDict)
                # elif (node.nodeIndex == 20 and len(self.matrixList5) < self.frames):
                #     currentModelView = np.array(glGetFloatv(GL_MODELVIEW_MATRIX))
                #     self.matrixList5.append(currentModelView)
                #     self.matrixDict['20'] = self.matrixList5
                #     # print(self.matrixDict)            
                # elif (node.nodeIndex == 8 and len(self.matrixList0) < self.frames):
                #     currentModelView = np.array(glGetFloatv(GL_MODELVIEW_MATRIX))
                #     self.matrixList0.append(currentModelView)
                #     self.matrixDict['8'] = self.matrixList0

                # Drawing Links
                if node.fHaveSite:
                    _RenderBone(quadObj, 0.0, 0.0, 0.0, node.site[0] * self.scale, node.site[1] * self.scale, node.site[2] * self.scale)
                for child in node.childNode:
                    _RenderBone(quadObj, 0.0, 0.0, 0.0, child.offset[0] * self.scale, child.offset[1] * self.scale, child.offset[2] * self.scale)
                
                # Drawing Joint Sphere
                _RenderJoint(quadObj)

                # Child drawing
                for child in node.childNode:
                    _RenderFigure(child)
            glPopMatrix()

        # drawSkeleton Main Codes
        if (self.root is not None) and (self.motion is not None):
            if self.drawMode == 0:  # rotation mode
                glColor3f(1.000, 0.549, 0.000)
            else:                   # position mode
                glColor3f(0.000, 1.000, 0.000)
            _RenderFigure(self.root)
        pass



    def makeFloorObject(self, height):
        size = 50
        num = 20
        genList = glGenLists(1)
        glNewList(genList, GL_COMPILE)
        glBegin(GL_QUADS)
        for j in range(-int(num/2), int(num/2)+1):
            glNormal(0.0, 1.0, 0.0)
            for i in range(-int(num/2), int(num/2)+1):
                if (i + j) % 2 == 0:
                    glColor3f(0.4, 0.4, 0.4)
                else:
                    glColor3f(0.2, 0.2, 0.2)
                glVertex3i(i*size, height, j*size)
                glVertex3i(i*size, height, j*size+size)
                glVertex3i(i*size+size, height, j*size+size)
                glVertex3i(i*size+size, height, j*size)
        glEnd()
        glEndList()
        return genList

    def makexyObj(self, z):
        size = 50
        num = 10
        genList = glGenLists(1)
        glNewList(genList, GL_COMPILE)
        glBegin(GL_QUADS)
        for j in range(-int(num/2), int(num/2)+1):
            glNormal(0.0, 1.0, 0.0)
            for i in range(-int(num/2), int(num/2)+1):
                if (i + j) % 2 == 0:
                    glColor3f(0.0, 0.0, 0.4)
                else:
                    glColor3f(0.0, 0.0, 0.4)
                glVertex3i(i*size, j*size, z)
                glVertex3i(i*size, j*size+size, z)
                glVertex3i(i*size+size, j*size+size, z)
                glVertex3i(i*size+size,j*size, z)
        glEnd()
        glEndList()
        return genList

    def makezyObj(self, x):
        size = 50
        num = 10
        genList = glGenLists(1)
        glNewList(genList, GL_COMPILE)
        glBegin(GL_QUADS)
        for j in range(-int(num/2), int(num/2)+1):
            glNormal(0.0, 1.0, 0.0)
            for i in range(-int(num/2), int(num/2)+1):
                if (i + j) % 2 == 0:
                    glColor3f(0.4, 0.0, 0.0)
                else:
                    glColor3f(0.4, 0.0, 0.0)
                glVertex3i(x, i*size, j*size)
                glVertex3i(x, i*size, j*size+size)
                glVertex3i(x, i*size+size, j*size+size)
                glVertex3i(x, i*size+size,j*size)
        glEnd()
        glEndList()
        return genList

    def makezxObj(self, y):
        size = 50
        num = 10
        genList = glGenLists(1)
        glNewList(genList, GL_COMPILE)
        glBegin(GL_QUADS)
        for j in range(-int(num/2), int(num/2)+1):
            glNormal(0.0, 1.0, 0.0)
            for i in range(-int(num/2), int(num/2)+1):
                if (i + j) % 2 == 0:
                    glColor3f(0.0, 0.4, 0.0)
                else:
                    glColor3f(0.0, 0.4, 0.0)
                glVertex3i(i*size, y, j*size)
                glVertex3i(i*size, y, j*size+size)
                glVertex3i(i*size+size, y, j*size+size)
                glVertex3i(i*size+size, y, j*size)
        glEnd()
        glEndList()
        return genList

    def makeCoordinate(self, h):
        len = 100
        genList = glGenLists(1)
        glNewList(genList, GL_COMPILE)
        glLineWidth(3)
        glBegin(GL_LINES)
        
        glColor3f(1.0, 0.0, 0.0)
        glVertex3i(-300, h, -300)
        glVertex3i(len-300, h, -300)

        glColor3f(0.0, 1.0, 0.0)
        glVertex3i(-300, h, -300)
        glVertex3i(-300, h+len, -300)

        glColor3f(0.0, 0.0, 1.0)
        glVertex3i(-300, h, -300)
        glVertex3i(-300, h, len-300)
        glEnd()
        glEndList()
        return genList

    def drawInitSkeleton(self):
        def _RenderBone(quadObj, x0, y0, z0, x1, y1, z1):
            dir = [x1 - x0, y1 - y0, z1 - z0]
            boneLength = np.sqrt(dir[0]**2 + dir[1]**2 + dir[2]**2)

            if quadObj is None:
                quadObj = GLUQuadric()
            gluQuadricDrawStyle(quadObj, GLU_FILL)
            gluQuadricNormals(quadObj, GLU_SMOOTH)

            glPushMatrix()
            glTranslated(x0, y0, z0)

            length = np.sqrt(dir[0]**2 + dir[1]**2 + dir[2]**2)
            if length < 0.0001:
                dir = [0.0, 0.0, 1.0]
                length = 1.0
            dir = [data / length for data in dir]            
            
#            up   = [0.0, 1.0, 0.0]
#            side = [up[1]*dir[2] - up[2]*dir[1], up[2]*dir[0] - up[0]*dir[2], up[0]*dir[1] - up[1]*dir[0]]
            side = [dir[2], 0.0, -dir[0]]
            length = np.sqrt(side[0]**2 + side[1]**2 + side[2]**2)
            if length < 0.0001:
                side = [1.0, 0.0, 0.0]
                length = 1.0
            side = [data / length for data in side]

            up = [dir[1]*side[2] - dir[2]*side[1], dir[2]*side[0] - dir[0]*side[2], dir[0]*side[1] - dir[1]*side[0]]
            glMultMatrixd((side[0], side[1], side[2], 0.0,
                             up[0],   up[1],   up[2], 0.0,
                            dir[0],  dir[1],  dir[2], 0.0,
                               0.0,     0.0,     0.0, 1.0))
            radius = 1.5
            slices = 8
            stack = 1
            gluCylinder(quadObj, radius, radius, boneLength, slices, stack)
            glPopMatrix()

        def _RenderJoint(quadObj):
            if quadObj is None:
                quadObj = GLUQuadric()
            gluQuadricDrawStyle(quadObj, GLU_FILL)
            gluQuadricNormals(quadObj, GLU_SMOOTH)

            if self.drawMode == 0:  # rotation mode
                glColor3f(1.000, 0.271, 0.000)
            else:                   # position mode
                glColor3f(0.000, 1.052, 0.000)

            gluSphere(quadObj, 3.0, 16, 16)            

            if self.drawMode == 0:  # rotation mode
                glColor3f(1.000, 0.549, 0.000)
            else:                   # position mode
                glColor3f(0.000, 1.000, 0.000)

        def _RenderFigure(node:BVHNode):
            quadObj = None
            glPushMatrix()
            if self.drawMode == 0:
                # Translate
                if node.nodeIndex == 0:     # ROOT
                    glTranslatef(self.zy * self.scale,
                                 self.zx * self.scale,
                                 self.xy * self.scale)
                else:   # general node
                    glTranslatef(node.offset[0] * self.scale, node.offset[1] * self.scale, node.offset[2] * self.scale)

                # Rotation
                for i, channel in enumerate(node.chLabel):
                    if "Xrotation" in channel:
                        glRotatef(self.Initmotion[0][node.frameIndex + i], 1.0, 0.0, 0.0)
                    elif "Yrotation" in channel:
                        glRotatef(self.Initmotion[0][node.frameIndex + i], 0.0, 1.0, 0.0)
                    elif "Zrotation" in channel:
                        glRotatef(self.Initmotion[0][node.frameIndex + i], 0.0, 0.0, 1.0)
                
                # Drawing Links
                if node.fHaveSite:
                    _RenderBone(quadObj, 0.0, 0.0, 0.0, node.site[0] * self.scale, node.site[1] * self.scale, node.site[2] * self.scale)
                for child in node.childNode:
                    _RenderBone(quadObj, 0.0, 0.0, 0.0, child.offset[0] * self.scale, child.offset[1] * self.scale, child.offset[2] * self.scale)
                
                # Drawing Joint Sphere
                _RenderJoint(quadObj)

                # Child drawing
                for child in node.childNode:
                    _RenderFigure(child)
            glPopMatrix()

        # drawSkeleton Main Codes
        if (self.Initroot is not None) and (self.Initmotion is not None):
            if self.drawMode == 0:  # rotation mode
                glColor3f(1.000, 0.549, 0.000)
            else:                   # position mode
                glColor3f(0.000, 1.000, 0.000)
            _RenderFigure(self.Initroot)
        pass


    ## Mouse & Key Events
    def mousePressEvent(self, event:QMouseEvent):
        self.lastPos = event.pos()

    def mouseMoveEvent(self, event:QMouseEvent):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()

        if event.buttons() & Qt.LeftButton:
            self.rotateXZ += dx
            self.rotateY  += dy
        if event.buttons() & Qt.RightButton:
            self.translateX += dx
            self.translateY += dy
        self.lastPos = event.pos()
        self.update()

    def wheelEvent(self, event:QWheelEvent):
        angle = event.angleDelta()
        steps = angle.y() / 8.0

        self.camDist -= steps
        if self.camDist < 1:
            self.camDist = 1
        elif self.camDist > 750:
            self.camDist = 750
        self.update()

    def zxSwitch(self):
        with open('csv/teststk_pick.pkl','rb') as file:
            test_stroke = pickle.load(file)
        print(len(test_stroke))
        query_stroke = np.zeros((len(test_stroke),3))
        query_stroke[:,0] = test_stroke[:,0]
        query_stroke[:,1] = test_stroke[:,1]
        for i in range(len(self.pkl_stroke)):
            df = similaritymeasures.frechet_dist(test_stroke, self.pkl_stroke[i])
            print(df)

    def zySwitch(self):
        with open('csv/teststk_pick.pkl','rb') as file:
            test_stroke = pickle.load(file)
        query_stroke = np.zeros((len(test_stroke),3))
        query_stroke[:,1] = test_stroke[:,0]
        query_stroke[:,2] = test_stroke[:,1]
        for i in range(len(self.pkl_stroke)):
            df = similaritymeasures.frechet_dist(test_stroke, self.pkl_stroke[i])
            print(df)

    def xySwitch(self):
        with open('csv/teststk_pick.pkl','rb') as file:
            test_stroke = pickle.load(file)
        query_stroke = np.zeros((len(test_stroke),3))
        query_stroke[:,0] = test_stroke[:,0]
        query_stroke[:,2] = test_stroke[:,1]
        for i in range(len(self.pkl_stroke)):
            df = similaritymeasures.frechet_dist(test_stroke, self.pkl_stroke[i])
            print(df)

    # 07.13
    def zxLocal(self):
        with open('csv/teststk_pick.pkl','rb') as file:
            test_stroke = pickle.load(file)
        # print(len(test_stroke))
        query_stroke = np.zeros((len(test_stroke),3))
        query_stroke[:,0] = test_stroke[:,0]
        query_stroke[:,1] = test_stroke[:,1]
        self.score = []
        for i in range(len(self.jointpos)):
            df = similaritymeasures.frechet_dist(test_stroke, self.jointpos[i])
            # print(df)
            self.score.append(df)
        self.rank = np.argsort(self.score)
        print(self.rank[0])
        # jointeditBVH("testbvh/",self.rank[0])

    def zyLocal(self):
        with open('csv/teststk_pick.pkl','rb') as file:
            test_stroke = pickle.load(file)
        # print(len(test_stroke))
        query_stroke = np.zeros((len(test_stroke),3))
        query_stroke[:,1] = test_stroke[:,0]
        query_stroke[:,2] = test_stroke[:,1]
        self.score = []
        for i in range(len(self.jointpos)):
            df = similaritymeasures.frechet_dist(test_stroke, self.jointpos[i])
            # print(df)
            self.score.append(df)
        self.rank = np.argsort(self.score)
        print(self.rank[0])

    def xyLocal(self):
        with open('csv/teststk_pick.pkl','rb') as file:
            test_stroke = pickle.load(file)
        # print(len(test_stroke))
        query_stroke = np.zeros((len(test_stroke),3))
        query_stroke[:,0] = test_stroke[:,0]
        query_stroke[:,2] = test_stroke[:,1]
        self.score = []
        for i in range(len(self.jointpos)):
            df = similaritymeasures.frechet_dist(test_stroke, self.jointpos[i])
            # print(df)  
            self.score.append(df)
        self.rank = np.argsort(self.score)
        print(self.rank[0])  

#    def keyPressEvent(self, event:QKeyEvent):
#        if event.key() == Qt.Key_Escape:
#            self.parent().quit()
#        elif event.key() == Qt.Key_S:
#            self.isPlaying = not self.isPlaying
#        elif event.key() == Qt.Key_F:
#            self.fastRatio *= 2.0
#        elif event.key() == Qt.Key_D:
#            self.fastRatio /= 2.0
#        elif event.key() == Qt.Key_Right:
#            self.frameCount += 1
#        elif event.key() == Qt.Key_Left:
#            self.frameCount -= 1
#        else:
#            None
#        self.update()