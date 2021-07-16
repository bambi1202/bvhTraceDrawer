# -*- coding: utf-8 -*-

# "BVHPlayerPy" OpenGL drawing component
# Author: T.Shuhei
# Last Modified: 2017/09/28

import numpy as np
import time

from PyQt5.Qt import *
from OpenGL.GL import *
from OpenGL.GLU import *

from python_bvh import BVHNode, getNodeRoute

import glm
from pyrr import Matrix44, Vector3, vector
import math

class LocalGLWidget(QOpenGLWidget):
    frameChanged = pyqtSignal(int)
    hParentWidget = None
    checkerBoardSize = 50
    camDist = 500
    floorObj = None
    rotateXZ = 0
    rotateY = 180
    translateX = 0
    translateY = 0
    frameCount = 0
    isPlaying = True
    fastRatio = 1.0
    scale = 1.0
    root = None
    motion = None
    frames = None
    frameTime = None
    drawMode = 0    # 0:rotation, 1:position
    currentProject = None
    trajectoryFlag = False
    screenCoords = {'x': [], 'y': []}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hParentWidget = parent
        self.setMinimumSize(500, 500)
        self.lastPos = QPoint()
        self.matrixList = []
        self.matrixDict = {
            '0': {
                'data': [],
                'flag': False
            },
            'RightUpLeg': {
                'data': [],
                'flag': False
            },
            'RightHand': {
                'data': [],
                'flag': False
            }
        }

    def resetCamera(self):
        self.rotateXZ = 0
        self.rotateY = 90
        self.translateX = 0
        self.translateY = 0
        self.camDist = 500

    def setMotion(self, root:BVHNode, motion, frames:int, frameTime:float):
        self.root = root
        print(root.getNodeI(5).nodeName)
        self.motion = motion
        self.frames = frames
        self.frameTime = frameTime
        self.frameCount = 0
        self.isPlaying = True

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_CONSTANT_ALPHA)
        glEnable(GL_BLEND)
        glClearColor(0.2, 0.2, 0.2, 0)
        self.floorObj = self.makeFloorObject(0)
        self.start = time.time()

    def updateFrame(self):
        if (self.frames is not None) and (self.frameTime is not None):
            now = time.time()
            if self.isPlaying:
                self.frameCount += int(1 * self.fastRatio) if abs(self.fastRatio) >= 1.0 else 1
                if self.frameCount >= self.frames:
                    self.frameCount = 0
                elif self.frameCount < 0:
                    self.frameCount = self.frames - 1
                self.frameChanged.emit(self.frameCount)
        self.update()
        self.hParentWidget.infoPanel.updateFrameCount(self.frameCount)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        qs = self.sizeHint()
        gluPerspective(60.0, float(qs.width()) / float(qs.height()), 1.0, 1000.0)
        if self.matrixDict['0']['flag'] and self.matrixDict['RightUpLeg']['flag']:
            root_matrix = self.matrixDict['0']['data'][self.frameCount]
            rightupleg_matrix = self.matrixDict['RightUpLeg']['data'][self.frameCount]
            root_matrix44 = Matrix44(root_matrix)
            rightupleg_matrix44 = Matrix44(rightupleg_matrix)
            origin = Vector3([0., 0., 0.])
            root_coord = root_matrix44 * origin
            rightupleg_coord = rightupleg_matrix44 * origin
            norm_vec = vector.normalise(root_coord - rightupleg_coord)
            eye = root_coord - norm_vec * 200
            center = root_coord
            gluLookAt(eye.x, eye.y, eye.z, center.x, center.y, center.z, 0, 1, 0)
            self.currentProject = np.array(glGetFloatv(GL_PROJECTION_MATRIX))
            self.trajectoryFlag = True
        else:
            camPx = self.camDist * np.cos(self.rotateXZ / 180.0)
            camPy = self.camDist * np.tanh(self.rotateY / 180.0)
            camPz = self.camDist * np.sin(self.rotateXZ / 180.0)
            transX = self.translateX * -np.sin(self.rotateXZ / 180.0)
            transZ = self.translateX * np.cos(self.rotateXZ / 180.0)
            gluLookAt(camPx + transX, camPy + self.translateY, camPz + transZ, transX, self.translateY, transZ, 0.0, 1.0, 0.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glCallList(self.floorObj)
        self.drawSkeleton()
        if self.trajectoryFlag:
            self.drawTrajectory()
        if len(self.screenCoords['x']) == self.frames:
            print(self.frames)
            print(self.screenCoords)
        glPopMatrix()
        glFlush()
#        self.update()
        self.updateFrame()

    def drawTrajectory(self):
        def _RenderJoint(quadObj):
            if quadObj is None:
                quadObj = GLUQuadric()
            glDisable(GL_DEPTH_TEST)
            gluQuadricDrawStyle(quadObj, GLU_FILL)
            gluQuadricNormals(quadObj, GLU_SMOOTH)

            if self.drawMode == 0:  # rotation mode
                glColor3f(0.89, 0.75, 0.75)
                
            else:                   # position mode
                glColor3f(0.000, 1.052, 0.000)

            gluSphere(quadObj, 1.0, 16, 16)            

            if self.drawMode == 0:  # rotation mode
                glColor3f(1.000, 0.271, 0.000)
            else:                   # position mode
                glColor3f(0.000, 1.000, 0.000)
            glEnable(GL_DEPTH_TEST)

        if (self.root is not None) and (self.motion is not None):
            if len(self.screenCoords['x']) < self.frames:
                m = self.matrixDict['RightHand']['data'][self.frameCount]
                glPushMatrix()
                matrix = m.T
                currentModelView = np.array(glGetFloatv(GL_MODELVIEW_MATRIX))
                modelview = glm.mat4(currentModelView.T)
                original = glm.mat4(matrix) * glm.vec4(0, 0, 0, 1)
                viewport = glm.vec4(0.0, 0.0, 500.0, 500.0)
                projection = glm.mat4(self.currentProject.T)
                # print(modelview, original, viewport, projection)
                coords = glm.project(glm.vec3(original), modelview, projection, viewport)
                # print(coords.x, coords.y)
                
                assert len(self.screenCoords['x']) == len(self.screenCoords['y'])
                # assert self.frameCount == len(self.screenCoords['x'])
                self.screenCoords['x'].append(coords.x)
                self.screenCoords['y'].append(coords.y)
                glPopMatrix()

            # glMultMatrixd((matrix[0, 0], matrix[1, 0], matrix[2, 0], matrix[3, 0], matrix[0, 1], matrix[1, 1], matrix[2, 1], matrix[3, 1],
            #             matrix[0, 2], matrix[1, 2], matrix[2, 2], matrix[3, 2], matrix[0, 3], matrix[1, 3], matrix[2, 3], matrix[3, 3]))
            # quadObj = None
            # _RenderJoint(quadObj)
            

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
                else:   # general node
                    glTranslatef(node.offset[0] * self.scale, node.offset[1] * self.scale, node.offset[2] * self.scale)

                # Rotation
                for i, channel in enumerate(node.chLabel):
                    if "Xrotation" in channel:
                        glRotatef(self.motion[self.frameCount][node.frameIndex + i], 1.0, 0.0, 0.0)
                    elif "Yrotation" in channel:
                        glRotatef(self.motion[self.frameCount][node.frameIndex + i], 0.0, 1.0, 0.0)
                    elif "Zrotation" in channel:
                        glRotatef(self.motion[self.frameCount][node.frameIndex + i], 0.0, 0.0, 1.0)

                if node.nodeIndex == 0:
                    if len(self.matrixDict['0']['data']) < self.frames:
                        currentModelView = np.array(glGetFloatv(GL_MODELVIEW_MATRIX))
                        self.matrixDict['0']['data'].append(currentModelView)
                    else:
                        self.matrixDict['0']['flag'] = True

                if node.nodeName == 'RightUpLeg':
                    if len(self.matrixDict['RightUpLeg']['data']) < self.frames:
                        currentModelView = np.array(glGetFloatv(GL_MODELVIEW_MATRIX))
                        self.matrixDict['RightUpLeg']['data'].append(currentModelView)
                    else:
                        self.matrixDict['RightUpLeg']['flag'] = True

                if node.nodeName == 'RightHand':
                    if len(self.matrixDict['RightHand']['data']) < self.frames:
                        currentModelView = np.array(glGetFloatv(GL_MODELVIEW_MATRIX))
                        self.matrixDict['RightHand']['data'].append(currentModelView)
                    else:
                        self.matrixDict['RightHand']['flag'] = True
                
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