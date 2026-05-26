# Head Pose Estimation

This folder contains the head pose estimation utility that calculates head yaw/pitch/roll from webcam video using MediaPipe Face Mesh.

Files
- `HeadPoseEstimation.py` — live webcam head-pose estimator and visualizer.

Requirements
- Python 3.10+ and the main repo dependencies (MediaPipe, OpenCV, NumPy).

Run

```powershell
python HeadPoseEstimation.py
```

Notes
- The script opens the default webcam (index 0). If the camera does not open, try other indices or check permissions.
