import cv2
import multiprocessing
from face_detection import *
from gui import *
import face_swap as fs
from PyQt5 import QtGui


class Capture:
    def __init__(self, video_elem, gui):
        self._video_elem = video_elem
        self._capturing = False
        self._gui = gui
        self._c = cv2.VideoCapture(0)
        self._detector = FaceDetector(DetectionMethods.HAAR)
        self._process = None
        self._queue = multiprocessing.Queue()
        self._img_queue = multiprocessing.Queue()
        self._positions = []
        self._time = 0
        self._video = self._c
        self._cv_img = None
        self._source_img = None
        self._source_face_area = None
        # Points where you drop an Icon
        self._swapping_point_x = 0
        self._swapping_point_y = 0
        self._try_swapping = False
        # List of all active trackers
        self._trackers = []
        self._face_swap_on = True

    def capture(self):
        if self._gui.is_detection():
            ret, frame = self._video.read()
            if ret:
                self._cv_img = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
                                          (self._gui.VIDEO_WIDTH, self._gui.VIDEO_HEIGHT))

                if not self._queue.empty():
                    self._positions, time = self._queue.get()
                    if self._positions:
                        # If we put the icon somewhere in the film - we check whether this location is a face
                        # and if so set the tracker
                        if self._try_swapping:
                            self.icon_drag_handler()
                        self._try_swapping = False

                        information = "Detected %d face(s)\n" % len(self._positions)
                    else:
                        information = "No faces\n"
                    information += "Detection time: %+2.2f seconds\n" % time
                    self._gui.send_info(information)
                    self._img_queue.put(self._cv_img)

                elif self._process is None:
                    self._img_queue.put(self._cv_img)
                    self._process = multiprocessing.Process(target=self._detector.detect,
                                                            args=(self._queue, self._img_queue))
                    self._process.start()

                # If face swap is turned on
                if self._face_swap_on:
                    for tracker in self._trackers:
                        if tracker.is_tracking:
                            self._cv_img = tracker.track_and_swap_faces(self._cv_img)

                self.show_frame()

            else:
                self._gui.turn_off_detection()

    def show_frame(self):
        for face in self._positions:
            cv2.rectangle(self._cv_img, (int(face.x), int(face.y)), (int(face.x + face.w), int(face.y + face.h)),
                          (0, 255, 0), 1)
        qimg = QtGui.QImage(self._cv_img.data, self._cv_img.shape[1], self._cv_img.shape[0], QtGui.QImage.Format_RGB888)
        qpm = QtGui.QPixmap.fromImage(qimg)
        self._video_elem.setPixmap(qpm)

    def change_method(self, method):
        self._img_queue.put(method)

    def change_video_source(self, source):
        self._video = cv2.VideoCapture(source)

    def set_camera_source(self):
        self._video = self._c

    def kill_process(self):
        if self._process is not None:
            self._process.terminate()
            self._process = None

    def get_trackers(self):
        return self._trackers

    def set_trackers(self, list_of_trackers):
        self._trackers = list_of_trackers

    def set_tracker(self, source_img, source_face_area, point_x, point_y):
        self._source_face_area = source_face_area
        self._source_img = source_img
        self._swapping_point_x = point_x
        self._swapping_point_y = point_y
        self._try_swapping = True

    def icon_drag_handler(self):
        # this variable indicates if we hit a face with the icon
        is_point_a_face = False
        face_position = None
        for position in self._positions:
            if (position.x <= self._swapping_point_x <= position.x + position.w
                    and position.y <= self._swapping_point_y <= position.y + position.h):
                is_point_a_face = True
                face_position = position
                break
        # If we have hit the face with the icon we initialize the tracker
        if is_point_a_face:
            track_method = self._gui.get_track_method()
            if track_method == TrackingMethods.DLIB:
                tracker = fs.Tracker()
            else:
                tracker = fs.TrackerOpenCV(track_method)
            tracker.init_tracker(self._cv_img, face_position,
                                 self._source_img,
                                 self._source_face_area)
            self._trackers.append(tracker)
            print("Tracker initialized")

        else:
            print("Cannot find a face is this location")
