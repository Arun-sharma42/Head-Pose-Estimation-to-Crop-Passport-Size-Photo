# import cv2

# print("Checking camera indices...")
# for i in range(5): # Try indices from 0 to 4
#     cap = cv2.VideoCapture(i)
#     if cap.isOpened():
#         print(f"Camera found at index {i}. Testing...")
#         ret, frame = cap.read()
#         if ret:
#             print(f"Successfully read a frame from camera {i}.")
#             cv2.imshow(f"Camera Test {i}", frame)
#             cv2.waitKey(2000) # Show frame for 2 seconds
#             cv2.destroyAllWindows()
#         else:
#             print(f"Could not read a frame from camera {i}.")
#         cap.release()
#     else:
#         print(f"No camera found at index {i}.")
# print("Camera check complete.")