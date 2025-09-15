import cv2
import mediapipe as mp
import numpy as np

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=True)
image = cv2.imread("person.jpg")

h, w = image.shape[:2]
rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
res = pose.process(rgb)

if res.pose_landmarks:
    l_shoulder = res.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
    r_shoulder = res.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
    
    x1, y1 = int(l_shoulder.x * w), int(l_shoulder.y * h)
    x2, y2 = int(r_shoulder.x * w), int(r_shoulder.y * h)
    
    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
    print("Tilt angle:", angle)

    # Rotate to straighten shoulders
    M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h))
    
    cv2.imshow("Straightened", rotated)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
