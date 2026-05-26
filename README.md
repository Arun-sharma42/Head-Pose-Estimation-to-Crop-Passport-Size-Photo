# Passport Pro AI Studio

A desktop Tkinter application for preparing passport-style photos with AI-powered camera compliance, background removal, auto passport cropping, image enhancement, and print sheet generation.

## Overview

`main.py` provides a polished GUI experience for:

- browsing and previewing local image folders
- removing photo backgrounds automatically
- auto-cropping images to passport-style aspect ratio
- enhancing image quality with smoothing, contrast correction, and upscaling
- generating a 4x6 print sheet containing 6 copies of a selected image
- live webcam capture with face compliance guidance
- taking snapshots from the webcam and saving them locally

## Features

- `File Explorer` tab for image browsing and preview
- `Live Studio` tab for webcam capture and compliance checking
- background removal using `rembg`
- passport crop using `MediaPipe` face detection
- quality enhancement using `OpenCV` filters
- print sheet creation using `Pillow`
- user-friendly status messages and threaded processing

## Requirements

Install the required Python packages in a virtual environment before running the app.

```powershell
pip install opencv-python pillow mediapipe rembg numpy
```

If you already have a `requirements.txt`, install with:

```powershell
pip install -r requirements.txt
```

## Running the App

Launch the application from the project folder:

```powershell
python main.py
```

## How to Use

1. Open the app with `python main.py`.
2. In `File Explorer`, browse to a folder containing images.
3. Select an image to preview it.
4. Use the quick action buttons to:
   - remove background
   - auto crop to passport size
   - enhance quality
   - generate a print sheet
5. Switch to `Live Studio` to start the webcam, check compliance, and take a snapshot.

## Notes

- If webcam access fails, check camera permissions and privacy settings.
- The app saves processed images using filename suffixes such as `_clean_bg`, `_passport_crop`, `_HD`, and `_print_sheet`.
- Local virtual environments and cache directories should be ignored by Git.

## Files

- `main.py` — main GUI and image-processing application
- `HeadPoseEstimation.py` — standalone head pose estimation script
- `headposeimage.py` — static image head pose testing script
- `project1.py` — alternate image file manager and processing script
- `README.md` — project documentation

## License

No license is included. Add a license file if you plan to share or publish this project.

