import cv2
import mediapipe as mp
from mediapipe.python.solutions.face_mesh_connections import FACEMESH_TESSELATION
import numpy as np
# import time # Not needed for static images, so we can comment it out

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

mp_drawing = mp.solutions.drawing_utils
drawing_specs = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)

# --- START MODIFIED SECTION FOR STATIC IMAGE INPUT ---

# 1. REMOVED: Webcam initialization (cap = cv2.VideoCapture...)
# 2. REMOVED: Webcam error check (if not cap.isOpened(): ...)
# 3. REMOVED: Webcam status print (print("Webcam opened successfully...") )

# NEW: Define the path to your image file
# IMPORTANT: Replace 'path/to/your/image.jpg' with the actual path to your image.
# Use forward slashes (/) or double backslashes (\\) for Windows paths.
image_path = "C:/Users/aruns/Downloads/crop photo1_hcrop.jpg" # <--- CHANGE THIS PATH!

# NEW: Load the image
image = cv2.imread(image_path)

# NEW: Check if the image was loaded successfully
if image is None:
    print(f"Error: Could not load image from '{image_path}'. Please check the path and file existence.")
    exit() # Exit the script if the image can't be loaded
print(f"Image '{image_path}' loaded successfully. Displaying result. Press any key to exit.")

# --- END MODIFIED SECTION FOR STATIC IMAGE INPUT ---

# 4. REMOVED: The `while cap.isOpened():` loop. The code now runs once for the loaded image.

# 5. REMOVED: Frame reading (success, image = cap.read() )
#    The 'image' variable is now the one loaded from the file.

# 6. REMOVED: Frame read success check (if not success: ...)

# 7. REMOVED: Start timer for FPS calculation (start = time.time()) - FPS is not relevant for static images.

# Flip the image horizontally (common for selfie-view)
# For a static photo, you might or might not want this, depending on the photo's orientation.
# If your photo looks mirrored, uncomment this line. Otherwise, keep it as is.
# image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) # Process the image without flipping for typical photos

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
        cv2.putText(image, f"Pitch (x): {x:.2f}", (500, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(image, f"Yaw (y): {y:.2f}", (500, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(image, f"Roll (z): {z:.2f}", (500, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Draw all face mesh landmarks
        mp_drawing.draw_landmarks(
            image=image,
            landmark_list=face_landmarks,
            connections=FACEMESH_TESSELATION, # Or mp_face_mesh.FACEMESH_TESSELATION
            landmark_drawing_spec=drawing_specs,
            connection_drawing_spec=drawing_specs
        )
else: # NEW: If no face is detected in the image
    cv2.putText(image, "No face detected", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)

# 8. REMOVED: FPS calculation related lines (end = time.time(), totalTime, fps...)

# --- START MODIFIED SECTION FOR STATIC IMAGE DISPLAY ---
cv2.imshow('Head Pose Estimation for Image', image) # Changed window title
# NEW: Wait indefinitely for a key press (0ms) to keep the window open
if cv2.waitKey(0) & 0xFF == 27: # Still include ESC check if desired, but any key works for 0ms
    pass # No break needed, as it's a single image.
# --- END MODIFIED SECTION FOR STATIC IMAGE DISPLAY ---

# 9. REMOVED: cap.release()
cv2.destroyAllWindows() # Close all OpenCV windows
print("Program finished. Window closed.")
# 10. REMOVED: "Webcam released" print