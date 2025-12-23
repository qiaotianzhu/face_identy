import cv2 as cv
import face_recognition
from face_recognition import face_locations, face_encodings
import numpy as np

image=cv.imread("1.jpg")
image2=cv.imread("face.jpg")
#获取人脸位置
image = cv.cvtColor(image, cv.COLOR_RGBA2RGB)
face_locations1=face_recognition.face_locations(image)
print(face_locations)
#获取人脸特征码
face_encodings1=face_recognition.face_encodings(image)[0]
face_encodings2=face_recognition.face_encodings(image2)[0]
#计算欧几里得距离
distance1=np.linalg.norm(face_encodings1-face_encodings2)
print(distance1)
