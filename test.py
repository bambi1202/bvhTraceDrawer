import numpy as np
import math
import scipy.linalg as linalg
import matplotlib as mpl 
from mpl_toolkits.mplot3d import Axes3D 
import matplotlib.pyplot as plt 

#旋转矩阵 欧拉角
def rotate_mat(axis, radian):
    rot_matrix = linalg.expm(np.cross(np.eye(3), axis / linalg.norm(axis) * radian))
    return rot_matrix
# 分别是x,y和z轴,也可以自定义旋转轴
axis_x, axis_y, axis_z = [1,0,0], [0,1,0], [0, 0, 1]
rand_axis = [0,0,1]
#旋转角度
yaw = math.pi/180
#返回旋转矩阵
rot_matrix = rotate_mat(rand_axis, yaw)
# print(rot_matrix)
# 计算点绕着轴运动后的点
x = [-1010,105.43,-244]
x1 = np.dot(rot_matrix,x)
# 旋转后的坐标
print(x1)   
# 计算各轴偏移量
# print([x1[i]-x[i] for i in range(3)])
