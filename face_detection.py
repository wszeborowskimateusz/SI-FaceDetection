import cv2
import numpy as np
import time
import dlib
from skimage import io


class FaceArea:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self. h = h


"""cv2.CascadeClassifier('cascades/haarcascade_frontalface_default.xml') for Haar Cascade
cv2.CascadeClassifier('cascades/lbpcascade_frontalface.xml') for LBP Cascade
"""


def detect_faces(f_cascade, colored_img, scale_factor=1.2):
    t1 = time.time()
    img_copy = np.copy(colored_img)

    gray = cv2.cvtColor(img_copy, cv2.COLOR_BGR2GRAY)

    faces = f_cascade.detectMultiScale(gray, scaleFactor=scale_factor, minNeighbors=5)
    positions_of_faces = []
    for (x, y, w, h) in faces:

        positions_of_faces.append(FaceArea(x, y, w, h))

    t2 = time.time()
    return positions_of_faces, t2-t1


def detect_faces_dlib(file_name):
    t1 = time.time()
    # Create a HOG face detector using the built-in dlib class
    face_detector = dlib.get_frontal_face_detector()

    # Load the image into an array
    image = io.imread(file_name)

    # Run the HOG face detector on the image data.
    # The result will be the bounding boxes of the faces in our image.
    detected_faces = face_detector(image, 1)

    positions_of_faces = []

    # Loop through each face we found in the image
    for i, face_rect in enumerate(detected_faces):
        positions_of_faces.append(FaceArea(face_rect.left(), face_rect.top(), face_rect.width(), face_rect.height()))

    t2 = time.time()
    return positions_of_faces, t2-t1


#CNN detector
def detect_faces_cnn(file_name):
    t1 = time.time()
    cnn_face_detector = dlib.cnn_face_detection_model_v1("cascades/mmod_human_face_detector.dat")
    img = io.imread(file_name)

    dets = cnn_face_detector(img, 0)

    positions_of_faces = []

    for i, face_rect in enumerate(dets):
        positions_of_faces.append(FaceArea(face_rect.rect.left(), face_rect.rect.top(),
                                           face_rect.rect.width(), face_rect.rect.height()))

    t2 = time.time()
    return positions_of_faces, t2 - t1


