from PyQt5 import QtCore, QtGui, QtWidgets, Qt
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import os
import time
import sys
import logging
import cv2
import imageio.v2 as imageio
import numpy as np
import tkinter as tk

logging.basicConfig(filename="log.log", encoding="utf-8", format="%(asctime)s - %(levelname)s : %(message)s", datefmt="%Y-%m-%d %H:%M:%S %p", level=10)

def GetScreenCenter():
    root = tk.Tk()
    return root.winfo_screenwidth()//2,root.winfo_screenheight()//2

def read_bgrimage(filename):
    image = imageio.imread(filename)
    return cv2.cvtColor(np.array(image[:,:,:3]), cv2.COLOR_RGB2BGR)

def sort_contours(cnts, tolerance=20):
    bounding_boxes = [cv2.boundingRect(c) for c in cnts]
    cnts, bounding_boxes = zip(*sorted(zip(cnts, bounding_boxes), key=lambda b: (int(b[1][1] / tolerance) * tolerance, b[1][0])))
    return cnts

def open_debug(original, gray, thresh):
    center_x, center_y = GetScreenCenter()
    cv2.namedWindow('thresh', cv2.WINDOW_NORMAL)
    cv2.imshow('thresh', thresh)
    cv2.moveWindow('thresh', center_x, center_y)
    cv2.namedWindow('contours', cv2.WINDOW_NORMAL)
    cv2.imshow('contours', original)
    cv2.moveWindow('contours', center_x, center_y)
    cv2.namedWindow('gray', cv2.WINDOW_NORMAL)
    cv2.imshow('gray', gray)
    cv2.moveWindow('gray', center_x, center_y)
    # cv2.namedWindow('close', cv2.WINDOW_NORMAL)
    # cv2.imshow('close', close)
    # cv2.moveWindow('close', center_x, center_y)
    # cv2.namedWindow('dilate', cv2.WINDOW_NORMAL)
    # cv2.imshow('dilate', dilate)
    # cv2.moveWindow('dilate', center_x, center_y)
    cv2.waitKey()
    cv2.destroyAllWindows()

def sheet_slice(filename, bar_cur, interval, MainWindow):
    dirpath, ext = os.path.splitext(filename)
    image = read_bgrimage(filename)

    original = image.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    gradX = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
    gradY = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=0, dy=1, ksize=-1)
    gradient = cv2.subtract(gradX, gradY)
    gradient = cv2.convertScaleAbs(gradient)

    cv2.imshow('gradient', gradient)

    # blurred = cv2.blur(gradient, (9, 9))

    # thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 5, 2)
    thresh = cv2.threshold(gradient, 0, 255, cv2.THRESH_BINARY)[1]

    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
    close = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
    # close = cv2.erode(close, kernel, iterations=1)
    # dilate = cv2.dilate(close, kernel, iterations=1)

    cv2.imshow('close', close)

    cnts, _ = cv2.findContours(close, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filtered_cnts = [c for c in cnts if cv2.contourArea(c) > 100]
    count = len(filtered_cnts)
    MainWindow.append_text("<font color='green'>开始处理 {}，需要切分成 {} 个单元</font>".format(filename, count))
    logging.info("开始处理 {}，需要切分成 {} 个单元".format(filename, count))
    if count > 0:
        ii = interval // count
        output = sort_contours(filtered_cnts)
        max_width = 0
        max_height = 0
        for c in output:
            x,y,w,h = cv2.boundingRect(c)
            if w > max_width:
                max_width = w
            if h > max_height:
                max_height = h

        MainWindow.append_text("导出精灵的统一尺寸：宽 {}，高 {}".format(max_width, max_height))
        logging.info("导出精灵的统一尺寸：宽 {}，高 {}".format(max_width, max_height))

        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
            logging.info("创建文件夹 {}".format(dirpath))
            sprite_number = 1
            for c in output:
                x,y,w,h = cv2.boundingRect(c)
                ROI = image[y:y+h, x:x+w]
                bg = np.zeros((max_height, max_width, 4), np.uint8)
                x_offset = (max_width - w) // 2
                y_offset = (max_height - h) // 2
                bg[y_offset:y_offset+h, x_offset:x_offset+w, :3] = ROI
                bg[y_offset:y_offset+h, x_offset:x_offset+w, 3] = (gray[y:y+h, x:x+w] > 0).astype(np.uint8) * 255
                cv2.imwrite('{}/sprite_{}.png'.format(dirpath, sprite_number), bg)
                MainWindow.append_text("导出第 {} 张精灵".format(sprite_number))
                logging.info("导出第 {} 张精灵 {}/sprite_{}.png".format(sprite_number, dirpath, sprite_number))
                sprite_number += 1
                bar_cur = bar_cur + ii
                MainWindow.process_update(bar_cur)

        cv2.drawContours(original, output, -1, (0,.0, 255), 3, lineType=cv2.LINE_AA)

    open_debug(original, gray, thresh)


class Ui_MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(Ui_MainWindow,self).__init__()
        self.setupUi(self)
        self.retranslateUi(self)
        self.done = 1

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setFixedSize(500, 300)
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.retranslateUi(MainWindow)

        self.pushButton = QtWidgets.QPushButton(self.centralWidget)
        self.pushButton.setGeometry(QtCore.QRect(210, 10, 85, 30))
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setText("打开")
        MainWindow.setCentralWidget(self.centralWidget)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.pushButton.clicked.connect(self.openfile)

        self.progressBar = QtWidgets.QProgressBar(MainWindow)
        self.progressBar.setGeometry(QtCore.QRect(20, 50, 450, 30))
        self.progressBar.setStyleSheet("QProgressBar {border: 2px solid grey; border-radius: 5px; background-color: #FFFFFF; text-align:center; font-size:20px}")
        self.progressBar.setRange(0, 100)
        self.process_update(0)

        self.browser = QTextBrowser(MainWindow)
        self.browser.setPlainText("")
        self.browser.setGeometry(QtCore.QRect(20, 80, 450, 200))

    def append_text(self, text):
        self.browser.append(text)

    def process_update(self, i):
        self.progressBar.setValue(i)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "选择需要切分的 sprite sheet"))

    def openfile(self):
        if self.done == 1:
            self.done = 0
            files, _ = QFileDialog.getOpenFileNames(self, '选择文件', '', 'Images (*.tga *.png *.jpg *.bpm *.dib *.jpeg *.jpe *.jp2 *.webp *.tif *.tiff)')
            p_num = len(files)
            logging.info("选择了文件 {}".format(files))
            if p_num > 0:
                interval = 100 // p_num
                cur = 0
                self.process_update(cur)
                self.browser.setPlainText("")
                for file in files:
                    sheet_slice(file, cur, interval, self)
                    cur = cur + interval
                    self.process_update(cur)
                self.process_update(100)
            self.done = 1

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
