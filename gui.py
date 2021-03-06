import cv2
import multiprocessing

from face_detection import *
from face_swap import TrackingMethods
from video import *
import face_detection
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QWidget, QPushButton, QDialog, QFileDialog
from PyQt5.QtCore import QSize, QPoint, QTimer, QRect, Qt
from PyQt5.QtGui import QImage, QPainter, QPixmap


class MainWindow(QMainWindow):
    BUTTON_Y_POS = 30
    TEXT_BOX_HEIGHT = 24
    VIDEO_REFRESH_RATE = 30
    VIDEO_WIDTH = 580
    VIDEO_HEIGHT = 435
    VIDEO_BOX_X = 420
    VIDEO_BOX_Y = 15
    MESSAGE_BOX_Y_OFFSET = 60

    def __init__(self):
        self.face_detector = face_detection.FaceDetector(face_detection.DetectionMethods.HAAR)

        QMainWindow.__init__(self)
        self.setObjectName("Face Swaping Application")
        self.resize(1024, 700)
        self._central_widget = QtWidgets.QWidget(self)
        self._central_widget.setObjectName("_central_widget")
        self._selected_icon = None
        self._click_x = 0
        self._click_y = 0
        self.mouse_x = 0
        self.mouse_y = 0
        self._file_path = ""
        self._detection = False
        self._current_method = DetectionMethods.HAAR
        self._current_track_method = TrackingMethods.DLIB

        # video widget
        self._video = QtWidgets.QLabel(self._central_widget)
        self._video.setGeometry(QtCore.QRect(self.VIDEO_BOX_X, self.VIDEO_BOX_Y, self.VIDEO_WIDTH, self.VIDEO_HEIGHT))
        self._video.setObjectName("video")
        self._capturing = Capture(self._video, self)

        # video frame rate
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.show_frame)
        self._timer.start(1000 / self.VIDEO_REFRESH_RATE)

        # choose file button
        self._choose_file_button = QtWidgets.QPushButton(self._central_widget)
        self._choose_file_button.setGeometry(QtCore.QRect(30, self.BUTTON_Y_POS, 151, 31))
        self._choose_file_button.setObjectName("Input_File")
        self._choose_file_button.clicked.connect(self.get_file)

        # start button
        self._start_button = QtWidgets.QPushButton(self._central_widget)
        self._start_button.setGeometry(QtCore.QRect(240, self.BUTTON_Y_POS, 151, 31))
        self._start_button.setObjectName("_push_button_2")
        self._start_button.clicked.connect(self.start_event)
        self._start_button.setCheckable(True)

        # trackers remove button
        self._trackers_button = QtWidgets.QPushButton(self._central_widget)
        self._trackers_button.setGeometry(QtCore.QRect(20, 352 + self.MESSAGE_BOX_Y_OFFSET , 151, 20))
        self._trackers_button.setObjectName("Remove_Trackers")
        self._trackers_button.clicked.connect(self.remove_trackers)

        # file input path (text box)
        self._input_box = QtWidgets.QTextEdit(self._central_widget)
        self._input_box.setGeometry(QtCore.QRect(20, 100, 381, self.TEXT_BOX_HEIGHT))
        self._input_box.setObjectName("Input File")

        # input file label
        self._input_label = QtWidgets.QLabel(self._central_widget)
        self._input_label.setGeometry(QtCore.QRect(20, 70, 381, self.TEXT_BOX_HEIGHT))
        self._input_label.setObjectName("_input_label")
        self._input_label.setText("Input file path:")

        # text label "Choose a method"
        self._method_label = QtWidgets.QLabel(self._central_widget)
        self._method_label.setGeometry(QtCore.QRect(20, 130, 381, self.TEXT_BOX_HEIGHT))
        self._method_label.setObjectName("_method_label")
        self._method_label.setText("Choose a method of face detection:")

        # choose detection method
        self._method_box = QtWidgets.QComboBox(self._central_widget)
        self._method_box.setGeometry(QtCore.QRect(20, 160, 381, self.TEXT_BOX_HEIGHT))
        self._method_box.setObjectName("_detection_method_box")
        self._method_box.addItems(["Haar cascade", "Lbp cascade", "HOG method(dlib)", "CNN method(dlib)"])
        self._method_box.currentIndexChanged.connect(self.methods_change)

        # text label "Choose a tracking method"
        self._track_method_label = QtWidgets.QLabel(self._central_widget)
        self._track_method_label.setGeometry(QtCore.QRect(20, 190, 381, self.TEXT_BOX_HEIGHT))
        self._track_method_label.setObjectName("_method_label")
        self._track_method_label.setText("Choose a method of face tracking:")

        # choose tracking method
        self._track_method_box = QtWidgets.QComboBox(self._central_widget)
        self._track_method_box.setGeometry(QtCore.QRect(20, 220, 381, self.TEXT_BOX_HEIGHT))
        self._track_method_box.setObjectName("_tracking_method_box")
        self._track_method_box.addItems(["Dlib: Correlation Tracker",
                                         "OpenCV: BOOSTING",
                                         "OpenCV: MIL",
                                         "OpenCV: KCF",
                                         "OpenCV: TLD",
                                         "OpenCV: MEDIANFLOW",
                                         "OpenCV: GOTURN"])
        # Disable GOTURN method since there is a bug in OpenCV
        self._track_method_box.model().item(6).setEnabled(False)
        self._track_method_box.currentIndexChanged.connect(self.track_method_change)

        # infos about FR
        self._text_browser = QtWidgets.QTextBrowser(self._central_widget)
        self._text_browser.setGeometry(QtCore.QRect(20, 220 + self.MESSAGE_BOX_Y_OFFSET, 381, 121))
        self._text_browser.setObjectName("_text_browser")
        self._text_browser.setText("Information about face detection")

        # label infos about process of FD
        self._info_label = QtWidgets.QLabel(self._central_widget)
        self._info_label.setGeometry(QtCore.QRect(20, 190 + self.MESSAGE_BOX_Y_OFFSET, 381, self.TEXT_BOX_HEIGHT))
        self._info_label.setObjectName("_info_label")
        self._info_label.setText("Information about face detection:")

        # on/off face swap checkbox
        self._check_box = QtWidgets.QCheckBox(self._central_widget)
        self._check_box.setGeometry(QtCore.QRect(280, 350 + self.MESSAGE_BOX_Y_OFFSET, 150, self.TEXT_BOX_HEIGHT))
        self._check_box.setObjectName("_check_box")
        self._check_box.stateChanged.connect(lambda: self.check_box_event(self._check_box))

        # Face icons
        pic_face = QPixmap("./bach.jpg")  # default icon
        pic_face = pic_face.scaled(FaceIcon.ICON_SIZE, FaceIcon.ICON_SIZE)

        self._face_slot = []
        for i in range(0, 14):
            if i < 7:
                self._face_slot.append(FaceIcon(self, self._central_widget, 53 + i * 134, 470, pic_face, i, "bach.jpg"))
            else:
                self._face_slot.append(FaceIcon(self, self._central_widget, 53 + (i - 7) * 134, 585, pic_face, i,
                                                "bach.jpg"))

        # rest ~~~~~
        self.setCentralWidget(self._central_widget)
        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def track_method_change(self):
        self._current_track_method = self._track_method_box.currentIndex()

    def get_track_method(self):
        return self._current_track_method

    def send_info(self, info):
        self._text_browser.setText(self._method_box.currentText() + ":\n" + info)

    def methods_change(self):
        self._method_name = self._method_box.currentText()
        if self._method_name == "Haar cascade":
            self._current_method = DetectionMethods.HAAR
        elif self._method_name == "Lbp cascade":
            self._current_method = DetectionMethods.LBP
        elif self._method_name == "HOG method(dlib)":
            self._current_method = DetectionMethods.DLIB
        else:
            self._current_method = DetectionMethods.CNN
        self._capturing.change_method(self._current_method)

    def remove_trackers(self):
        del self._capturing.get_trackers()[:]

    def show_frame(self):
        self._capturing.capture()

    def check_box_event(self, check_box):
        if check_box.isChecked():
            self._capturing._face_swap_on = False
            print("Face swapping turned off")
        else:
            self._capturing._face_swap_on = True
            print("Face swapping turned on")

    def mouseMoveEvent(self, event):
        self.mouse_x = event.x()
        self.mouse_y = event.y()
        if self._selected_icon is not None:
            self._selected_icon.set_pos(event.x() - self._click_x, event.y() - self._click_y)

    def mouseReleaseEvent(self, event):
        if self._selected_icon is not None:
            self._selected_icon.reset_pos()

    def icon_release_event(self):
        if self._selected_icon is not None:
            if self._selected_icon.get_face_region() is not None:
                source_img = cv2.imread(self._selected_icon.get_file_name())
                self._capturing.set_tracker(source_img, self._selected_icon.get_face_region(),
                                            self.mouse_x - self.VIDEO_BOX_X, self.mouse_y - self.VIDEO_BOX_Y)
                self._selected_icon.reset_pos()

    def closeEvent(self, event):
        self._capturing.kill_process()
        event.accept()

    def delete_selected_icon(self):
        self._selected_icon = None

    def get_file(self):
        self._file_path = QFileDialog.getOpenFileName(self, 'Choose file', 'c:\\',
                                                      "Image files (*.jpg *.gif *.png *.mp4)")
        self._input_box.setText(self._file_path[0])

    def set_selected_icon(self, selected_icon, x, y):
        self._click_x = x
        self._click_y = y
        self._selected_icon = selected_icon

    def start_event(self):
        if self._input_box.toPlainText() != "":
            self._capturing.change_video_source(self._input_box.toPlainText())
        else:
            self._capturing.set_camera_source()
        self._detection = not self._detection
        self._start_button.setChecked(self._detection)

    def turn_off_detection(self):
        self._detection = False
        self._start_button.setChecked(self._detection)

    def is_detection(self):
        return self._detection

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "Face Swapping Application"))
        self._choose_file_button.setText(_translate("MainWindow", "Choose input File"))
        self._check_box.setText(_translate("MainWindow", "Turn off face swapping"))
        self._start_button.setText(_translate("MainWindow", "Start/Stop"))
        self._trackers_button.setText(_translate("MainWindow", "Remove all trackers"))


class FaceIcon(QLabel):
    ICON_SIZE = 110

    def __init__(self, parent, central_widget, pos_x, pos_y, image, number, file_name):
        QLabel.__init__(self, central_widget)
        self._parent = parent
        self.setGeometry(QRect(pos_x, pos_y, self.ICON_SIZE, self.ICON_SIZE))
        self._original_pos = pos_x, pos_y
        self.setObjectName("_face_slot_" + str(number))
        self.setPixmap(image)
        self.mousePressEvent = self.press_method
        self.mouseReleaseEvent = self.release_method
        self._file_name = file_name
        self._face_region = None
        self.detect_face_on_icon()

    def detect_face_on_icon(self):
        img = cv2.imread(self._file_name)
        if img is None:
            self._parent.send_info("Loading failed")
            self._face_region = None
            return False
        face_region, _ = self._parent.face_detector._detect_faces(face_detection.FaceDetector.HAAR_CASCADE, img)
        if not face_region:
            self._face_region = None
            return False
        else:
            self._face_region = face_region[0]
            return True

    def press_method(self, event):
        if event.button() == Qt.LeftButton:
            self._parent.set_selected_icon(self, event.x(), event.x())
        else:
            file_name = QFileDialog.getOpenFileName(self, 'Open file', 'c:\\', "Image files (*.jpg *.gif *.png *.mp4)")
            if file_name[0] != "":
                # Safe icon properties in case of failure in finding a face on an icon
                tmp_face_region = self._face_region
                tmp_file_name = self._file_name
                self._file_name = file_name[0]
                # no face found or wrong file
                if not self.detect_face_on_icon():
                    # Restore icon properties
                    self._file_name = tmp_file_name
                    self._face_region = tmp_face_region
                    return

                face_icon = QPixmap(file_name[0])
                self.setPixmap(face_icon.scaled(self.ICON_SIZE, self.ICON_SIZE))

    def release_method(self, event):
        self._parent.icon_release_event()
        self._parent.delete_selected_icon()
        self.reset_pos()

    def set_pos(self, x, y):
        self.setGeometry(x, y, self.ICON_SIZE, self.ICON_SIZE)

    def reset_pos(self):
        self.set_pos(self._original_pos[0], self._original_pos[1])

    def get_face_region(self):
        return self._face_region

    def get_file_name(self):
        return self._file_name

