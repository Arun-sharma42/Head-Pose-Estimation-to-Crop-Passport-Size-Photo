# Passport Pro AI Studio

A desktop Tkinter application for preparing passport-style photos with AI-powered camera compliance, background removal, auto passport cropping, image enhancement, and print sheet generation.

## Overview

The GUI app is now located in `passport-pro-ai-studio/main.py` and provides a polished experience for:

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
python -m venv venv
& .\venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
```

If you already have a `requirements.txt`, install with:

```powershell
pip install -r requirements.txt
```

## Running the App

Run the GUI app from its folder (activate the venv first):

```powershell
& .\venv\Scripts\Activate.ps1
python passport-pro-ai-studio\main.py
```

Run the head-pose tool (useful for debugging face alignment and cropping):

```powershell
& .\venv\Scripts\Activate.ps1
python head-pose-estimation\HeadPoseEstimation.py
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

- `passport-pro-ai-studio/main.py` — main GUI and image-processing application (moved)
- `head-pose-estimation/HeadPoseEstimation.py` — standalone head pose estimation utility (moved)
- `README.md` — project documentation (this file)

Repository layout:

- `passport-pro-ai-studio/` — GUI app and related helpers
- `head-pose-estimation/` — head-pose estimator and experiments
- `requirements.txt` — Python dependencies

Notes about removed files:

- `main1.py`, `project1.py`, and `headposeimage.py` were removed to reduce duplication and simplify the repository.

## License

No license is included. Add a license file if you plan to share or publish this project.

