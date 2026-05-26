# Passport Pro AI Studio

This folder contains the desktop GUI application for preparing passport-style photos.

Files
- `main.py` — Tkinter GUI app: browse images, remove background, auto-crop for passport, enhance quality, live webcam compliance and snapshot.

Requirements
- Python 3.10+ (use the project `venv`)
- Install dependencies (from repo root):

```powershell
pip install -r requirements.txt
```

Run

```powershell
python main.py
```

Notes
- The app uses MediaPipe, OpenCV, Pillow and rembg. Camera access requires OS permissions.
