import cv2 as cv
import numpy as np

global ImageData
#全局阈值
def threshold_demo(image):
    """
    *function:threshold_demo
    功能：对图像进行二值化
    ________
    Parameters
    * image: opencv.mat类型
    ————
    Returns
    -------
    * None
    """
    gray = cv.cvtColor(image, cv.COLOR_RGB2GRAY)
    ret, binary = cv.threshold(gray, 30, 90, cv.THRESH_BINARY_INV)
    print("threshold value %s"%ret)
    return binary

#局部阈值
def local_threshold(image):
    """
    *function:local_threshold
    功能：对图像进行二值化 ，采用局部值域
    ________
    Parameters
    * image: opencv.mat类型
    ————
    Returns
    -------
    * None
    """
    gray = cv.cvtColor(image, cv.COLOR_RGB2GRAY)
    binary =  cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C,cv.THRESH_BINARY, 25, 10)


def line(img):
    """
    *function:line
    功能：从头图像中提取一条线
    ________
    Parameters
    * image: opencv.mat类型
    ————
    Returns
    -------
    * None
    """
    binary = threshold_demo(img)
    binImg, contours, hierarchy = cv.findContours(binary, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)  # 得到轮廓信息
    contourList = []
    cx = 0.0
    cy = 0.0

    for contour in contours:
        area = cv.contourArea(contour)
        # print(area)
        if area > 1000:
            contourList.append(contour)
            M = cv.moments(contour)
            print(M)
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            print('cx:%d' % cx)
            print('cy:%d' % cy)
    return [cx,cy]

