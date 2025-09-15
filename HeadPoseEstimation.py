import cv2
import mediapipe as mp
from mediapipe.python.solutions.face_mesh_connections import FACEMESH_TESSELATION
import numpy as np
import time

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

mp_drawing = mp.solutions.drawing_utils

drawing_specs = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)

# Correct camera index (0 is common, use what worked from check_camera.py)
# and use CAP_DSHOW for stability on Windows
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) # Make sure '0' is the correct index!

# --- ADDED: Check if camera opened successfully immediately ---
if not cap.isOpened():
    print("Error: Could not open webcam. Please check camera connection, privacy settings, and try different camera indices.")
    exit() # Exit the script if camera not opened
print("Webcam opened successfully. Press 'Esc' to exit.")
# --- END ADDED ---

while cap.isOpened():
    success, image = cap.read() # Read a new frame

    # --- ADDED: Check if frame was read successfully ---
    if not success:
        print("Failed to grab frame. Exiting...")
        break # Exit the loop if no frame is read (e.g., camera disconnected)
    # --- END ADDED ---

    start = time.time() # Start timer for FPS calculation

    # Flip the image horizontally (common for selfie-view)
    # Then convert from BGR (OpenCV default) to RGB (MediaPipe expects RGB)
    image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)

    # To improve performance (make image non-writable for MediaPipe)
    image.flags.writeable = False

    # Get the result from face mesh processing
    result = face_mesh.process(image)

    # To allow drawing on the image again
    image.flags.writeable = True

    # Convert the processed image back from RGB to BGR for OpenCV display
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    img_h, img_w, img_c = image.shape
    face_3d = []
    face_2d = []

    if result.multi_face_landmarks:
        for face_landmarks in result.multi_face_landmarks:
            for idx, lm in enumerate(face_landmarks.landmark):
                # Using only specific landmarks for pose estimation (eyes, nose, mouth corners, chin)
                # These indices are commonly used for head pose:
                # 33: left eye outer corner, 263: right eye outer corner, 1: nose tip,
                # 61: left mouth corner, 291: right mouth corner, 199: chin
                if idx in [33, 263, 1, 61, 291, 199]:
                    if idx == 1: # Nose tip
                        nose_2d = (lm.x * img_w, lm.y * img_h)
                        # The Z coordinate here needs a scaling factor to represent depth correctly for PnP
                        # lm.z is relative to the face, scaling by img_w helps keep it consistent
                        nose_3d = (lm.x * img_w, lm.y * img_h, lm.z * img_w)
                    
                    x, y = int(lm.x * img_w), int(lm.y * img_h)

                    # Get the 2D coordinates
                    face_2d.append([x, y])

                    # Get the 3D coordinates (relative to camera plane, lm.z is depth)
                    face_3d.append([x, y, lm.z]) # lm.z is already scaled by MediaPipe


            # Convert to numpy arrays outside the inner loop to collect all points
            face_2d = np.array(face_2d, dtype=np.float64)
            face_3d = np.array(face_3d, dtype=np.float64)

            # Define camera properties
            # Focal length can be approximated as image width for average webcams
            focal_length = 1 * img_w 
            cam_matrix = np.array([
                [focal_length, 0, img_w / 2], # img_w / 2 is cx (principal point x)
                [0, focal_length, img_h / 2], # img_h / 2 is cy (principal point y)
                [0, 0, 1]
            ], dtype=np.float64)
            
            # Assuming no lens distortion
            dist_matrix = np.zeros((4, 1), dtype=np.float64)

            # Solve for rotation and translation vectors
            success_pnp, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)

            # Convert rotation vector to rotation matrix
            rmat, jac = cv2.Rodrigues(rot_vec)
            
            # Get angles (Euler angles)
            angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)

            # Get the yaw, pitch, and roll in degrees
            # Euler angles can have issues with gimbal lock. Be aware.
            x = angles[0] * 360 # Pitch
            y = angles[1] * 360 # Yaw
            z = angles[2] * 360 # Roll

            # Determine head orientation
            if y < -10:
                text = "Looking Left"
            elif y > 10:
                text = "Looking Right"
            elif x < -10:
                text = "Looking Down"
            elif x > 10:
                text = "Looking Up"
            else:
                text = "Looking Forward"

            # Project nose tip for drawing the direction line
            # You need nose_3d to be a proper 3D point array (1,3) or (3,1)
            # nose_3d was defined earlier as a tuple, convert it for projectPoints
            nose_3d_point_for_proj = np.array([nose_3d[0], nose_3d[1], nose_3d[2]]).reshape(3,1)

            nose_3d_projection, jacobian = cv2.projectPoints(nose_3d_point_for_proj, rot_vec, trans_vec, cam_matrix, dist_matrix)

            p1 = (int(nose_2d[0]), int(nose_2d[1]))
            p2 = (int(nose_3d_projection[0][0][0]), int(nose_3d_projection[0][0][1])) # Projecting a point along the nose direction

            cv2.line(image, p1, p2, (255, 0, 0), 3) # Blue line for direction

            # Add text on the image
            cv2.putText(image, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)
            cv2.putText(image, f"x: {x:.2f}", (500, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(image, f"y: {y:.2f}", (500, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(image, f"z: {z:.2f}", (500, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # Draw all face mesh landmarks
            mp_drawing.draw_landmarks(
                image=image,
                landmark_list=face_landmarks,
                connections=FACEMESH_TESSELATION, # Or mp_face_mesh.FACEMESH_TESSELATION
                landmark_drawing_spec=drawing_specs,
                connection_drawing_spec=drawing_specs
            )
        
    end = time.time()
    totalTime = end - start
    
    fps = 1 / totalTime
    print("FPS: ", fps)
    
    cv2.putText(image, f'FPS: {int(fps)}', (20, 450), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2)
    
    cv2.imshow('Head Pose Estimation', image)

    # --- FIX HERE: Change waitKey time to a small value (e.g., 5ms) ---
    if cv2.waitKey(5) & 0xFF == 27: # Wait 5ms, check for 'Esc' key (ASCII 27)
        break

# Release resources when loop ends
cap.release()
cv2.destroyAllWindows()
print("Program finished. Webcam released.")