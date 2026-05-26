import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import cv2
import PIL.Image, PIL.ImageTk
import mediapipe as mp
import numpy as np
import threading
from rembg import remove
import io
import time
import math

# --- LOGIC CLASSES ---

class ImageEngine:
    """Handles heavy image processing tasks."""
    
    @staticmethod
    def remove_bg(image_bytes):
        result = remove(image_bytes)
        img = PIL.Image.open(io.BytesIO(result)).convert("RGBA")
        # Add white background
        white_bg = PIL.Image.new("RGBA", img.size, "WHITE")
        final_img = PIL.Image.alpha_composite(white_bg, img).convert("RGB")
        return final_img

    @staticmethod
    def enhance_quality(cv_img):
        # 1. Professional Skin Smoothing (Bilateral Filter preserves edges)
        # This removes noise and skin blemishes without blurring facial features
        smoothed = cv2.bilateralFilter(cv_img, 9, 75, 75)
        
        # 2. Natural Contrast Enhancement (CLAHE with lower limit)
        img_yuv = cv2.cvtColor(smoothed, cv2.COLOR_BGR2YUV)
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        img_yuv[:, :, 0] = clahe.apply(img_yuv[:, :, 0])
        enhanced = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
        
        # 3. Intelligent Detail Enhancement (Replaces harsh sharpening)
        # This makes the eyes and features pop without looking "deep fried"
        final_details = cv2.detailEnhance(enhanced, sigma_s=10, sigma_r=0.15)
        
        # 4. High-Res Upscale
        final = cv2.resize(final_details, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LANCZOS4)
        return final

    @staticmethod
    def auto_crop_passport(cv_img):
        """Uses MediaPipe to find the head and crop for passport 35x45mm ratio."""
        mp_face = mp.solutions.face_detection
        with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
            results = face_detection.process(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
            
            if not results.detections:
                return None, "Face not detected"
            
            # Use the first face found
            detection = results.detections[0]
            bbox = detection.location_data.relative_bounding_box
            h, w, _ = cv_img.shape
            
            # Face center and size
            center_x = (bbox.xmin + bbox.width / 2) * w
            center_y = (bbox.ymin + bbox.height / 2) * h
            face_w = bbox.width * w
            face_h = bbox.height * h
            
            # Passport target ratio (35mm wide, 45mm high -> ~0.77 ratio)
            target_ratio = 35 / 45
            
            # Target Ratio: Head should take up ~70% of height
            crop_h = face_h / 0.70
            crop_w = crop_h * target_ratio
            
            # Calculate corners safely
            # center_y is face center. 
            # We want center at 45% from top to leave ~10% headspace.
            x1 = int(center_x - crop_w / 2)
            y1 = int(center_y - crop_h * 0.45) 
            x2 = int(x1 + crop_w)
            y2 = int(y1 + crop_h)

            # Side-specific padding
            top_pad = max(0, -y1)
            bottom_pad = max(0, y2 - h)
            left_pad = max(0, -x1)
            right_pad = max(0, x2 - w)
            
            if top_pad > 0 or bottom_pad > 0 or left_pad > 0 or right_pad > 0:
                cv_img = cv2.copyMakeBorder(cv_img, top_pad, bottom_pad, left_pad, right_pad, cv2.BORDER_CONSTANT, value=[255, 255, 255])
                x1 += left_pad; x2 += left_pad; y1 += top_pad; y2 += top_pad
            
            cropped = cv_img[y1:y2, x1:x2]
            # Standard passport pixels (e.g., 600dpi for 35x45 is 826x1063)
            # Let's scale to a reasonable 413x531 (lowish res but clear)
            final = cv2.resize(cropped, (413, 531), interpolation=cv2.INTER_LANCZOS4)
            return final, "Success"

    @staticmethod
    def generate_print_sheet(image_path, output_path):
        """Creates a 4x6 inch sheet with 6 photos."""
        try:
            single = PIL.Image.open(image_path)
            # 4x6 at 300 DPI is 1200x1800
            canvas = PIL.Image.new("RGB", (1800, 1200), "WHITE")
            
            # Target size for each photo (~1.37" x 1.77" @ 300dpi is ~413x531)
            single = single.resize((413, 531), PIL.Image.LANCZOS)
            
            positions = [
                (50, 50), (513, 50), (976, 50),
                (50, 631), (513, 631), (976, 631)
            ]
            
            for pos in positions:
                canvas.paste(single, pos)
                
            canvas.save(output_path, "JPEG", quality=95)
            return True
        except Exception as e:
            print(f"Print sheet error: {e}")
            return False

# --- UI COMPONENTS ---

class ModernApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Passport Pro AI Studio")
        self.root.geometry("1100x750")
        self.root.configure(bg="#1e1e1e")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.setup_styles()
        
        # State
        self.current_cv_image = None
        self.camera_active = False
        self.selected_file = None
        self.cap = None
        
        # MediaPipe for real-time compliance
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        
        self.create_layout()
        self.load_directory(os.path.expanduser("~"))

    def setup_styles(self):
        self.style.configure("Treeview", background="#2d2d2d", foreground="white", fieldbackground="#2d2d2d", font=('Segoe UI', 10), rowheight=30)
        self.style.map("Treeview", background=[('selected', '#007acc')])
        self.style.configure("TFrame", background="#1e1e1e")
        self.style.configure("TLabel", background="#1e1e1e", foreground="white", font=("Segoe UI", 10))
        self.style.configure("Sidebar.TFrame", background="#252526")
        self.style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=10)
        self.style.configure("Status.TLabel", font=("Segoe UI", 9, "italic"), foreground="#aaaaaa")

    def create_layout(self):
        # Sidebar
        sidebar = ttk.Frame(self.root, width=250, style="Sidebar.TFrame")
        sidebar.pack(side="left", fill="y")
        
        ttk.Label(sidebar, text="PASSPORT PRO AI", font=("Segoe UI", 16, "bold")).pack(pady=20, padx=10)
        
        # Tabs for Sidebar
        btn_config = {'padx': 10, 'pady': 5, 'fill': 'x'}
        ttk.Button(sidebar, text="📁 File Explorer", command=lambda: self.switch_tab(0)).pack(**btn_config)
        ttk.Button(sidebar, text="📸 Live Studio", command=lambda: self.switch_tab(1)).pack(**btn_config)
        
        ttk.Separator(sidebar, orient="horizontal").pack(pady=20, fill='x', padx=10)
        
        # Quick Actions
        ttk.Label(sidebar, text="QUICK ACTIONS", foreground="#888888").pack(pady=5)
        self.bg_btn = ttk.Button(sidebar, text="Remove Background", command=self.action_remove_bg)
        self.bg_btn.pack(**btn_config)
        
        self.crop_btn = ttk.Button(sidebar, text="Auto Passport Crop", command=self.action_auto_crop)
        self.crop_btn.pack(**btn_config)
        
        self.enhance_btn = ttk.Button(sidebar, text="Enhance Quality", command=self.action_enhance)
        self.enhance_btn.pack(**btn_config)
        
        self.print_btn = ttk.Button(sidebar, text="Generate Print Sheet", command=self.action_print_sheet)
        self.print_btn.pack(**btn_config)
        
        # Main Area
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(side="right", fill="both", expand=True)
        
        # Notebook for views
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill="both", expand=True)
        
        # Tab 1: File Explorer
        self.explorer_frame = ttk.Frame(self.notebook)
        self.setup_explorer(self.explorer_frame)
        self.notebook.add(self.explorer_frame, text="Files")
        
        # Tab 2: Studio
        self.studio_frame = ttk.Frame(self.notebook)
        self.setup_studio(self.studio_frame)
        self.notebook.add(self.studio_frame, text="Studio")
        
        # Status Bar
        self.status_bar = ttk.Label(self.root, text="Ready", style="Status.TLabel")
        self.status_bar.pack(side="bottom", fill="x", padx=10)

    def setup_explorer(self, parent):
        top_bar = ttk.Frame(parent)
        top_bar.pack(fill="x", pady=10, padx=10)
        
        self.path_entry = ttk.Entry(top_bar)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(top_bar, text="Browse", command=self.browse_folder).pack(side="left")
        
        # Tree and Preview
        paned = ttk.PanedWindow(parent, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tree = ttk.Treeview(paned, columns=("name"), show="headings")
        self.tree.heading("name", text="Filename")
        self.tree.column("name", width=250, anchor="w") # Set explicit width
        self.tree.bind("<<TreeviewSelect>>", self.on_file_select)
        paned.add(self.tree, weight=1)
        
        preview_container = ttk.Frame(paned)
        paned.add(preview_container, weight=1)
        
        self.preview_label = tk.Label(preview_container, bg="#1a1a1a")
        self.preview_label.pack(fill="both", expand=True)
        
        ttk.Label(preview_container, text="PREVIEW", font=("Segoe UI", 8, "bold")).pack(side="top")

    def setup_studio(self, parent):
        self.canvas = tk.Label(parent, bg="black")
        self.canvas.pack(fill="both", expand=True, padx=20, pady=20)
        
        controls = ttk.Frame(parent)
        controls.pack(fill="x", pady=10)
        
        self.capture_btn = ttk.Button(controls, text="START CAMERA", command=self.toggle_camera)
        self.capture_btn.pack(side="left", padx=10)
        
        self.snap_btn = ttk.Button(controls, text="📸 TAKE PHOTO", command=self.take_snapshot, state="disabled")
        self.snap_btn.pack(side="left", padx=10)
        
        self.compliance_label = ttk.Label(controls, text="Compliance: Waiting...", foreground="yellow")
        self.compliance_label.pack(side="right", padx=20)

    # --- ACTIONS ---

    def switch_tab(self, index):
        # Improved switching logic
        current = self.notebook.index(self.notebook.select())
        if current == index and index == 0:
            # If already on File Explorer, treat as "Browse" request
            self.browse_folder()
            return

        self.notebook.select(index)
        if index != 1 and self.camera_active:
            self.toggle_camera()

    def browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.load_directory(path)

    def load_directory(self, path):
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, path)
        self.current_path = os.path.abspath(path)
        
        for i in self.tree.get_children(): self.tree.delete(i)
        
        img_count = 0
        try:
            # Support a wider range of formats including Screenshots and WebP
            extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff', '.jfif')
            for item in sorted(os.listdir(path)):
                if item.lower().endswith(extensions):
                    self.tree.insert("", "end", values=(item,))
                    img_count += 1
            
            if img_count == 0:
                self.status_bar.config(text=f"No images found in {os.path.basename(path)}", foreground="orange")
            else:
                self.status_bar.config(text=f"Loaded {img_count} images from {os.path.basename(path)}", foreground="#aaaaaa")
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not load directory: {e}")


    def on_file_select(self, event):
        item = self.tree.selection()
        if not item: return
        filename = self.tree.item(item[0])['values'][0]
        self.selected_file = os.path.join(self.current_path, filename)
        self.show_preview(self.selected_file)

    def show_preview(self, path):
        img = PIL.Image.open(path)
        img.thumbnail((400, 400))
        photo = PIL.ImageTk.PhotoImage(img)
        self.preview_label.config(image=photo)
        self.preview_label.image = photo
        self.status_bar.config(text=f"Selected: {os.path.basename(path)}")

    # --- WEB CAM LOGIC ---

    def toggle_camera(self):
        if not self.camera_active:
            # Try multiple indices and use CAP_DSHOW for Windows
            self.cap = None
            for index in [0, 1, 2]:
                self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
                if self.cap.isOpened():
                    break
            
            if not self.cap or not self.cap.isOpened():
                # Fallback to default if DSHOW fails
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    messagebox.showerror("Error", "Could not access camera. Check privacy settings.")
                    return
            
            self.camera_active = True
            self.capture_btn.config(text="STOP CAMERA")
            self.snap_btn.config(state="normal")
            threading.Thread(target=self.camera_loop, daemon=True).start()
        else:
            self.camera_active = False
            self.capture_btn.config(text="START CAMERA")
            self.snap_btn.config(state="disabled")
            if self.cap: self.cap.release()

    def camera_loop(self):
        while self.camera_active:
            ret, frame = self.cap.read()
            if not ret: 
                time.sleep(0.1)
                continue
            
            frame = cv2.flip(frame, 1)
            display_frame = frame.copy()
            
            # Compliance Check
            compliance_msg, color, compliant = self.check_compliance(frame)
            
            # Draw Passport Overlay
            h, w, _ = frame.shape
            box_h = int(h * 0.7)
            box_w = int(box_h * (35/45))
            x1, y1 = (w - box_w) // 2, (h - box_h) // 2
            cv2.rectangle(display_frame, (x1, y1), (x1+box_w, y1+box_h), (0, 255, 0) if compliant else (0, 0, 255), 2)
            
            # Convert for Tkinter
            img = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img = PIL.Image.fromarray(img)
            img.thumbnail((640, 480))
            photo = PIL.ImageTk.PhotoImage(img)
            
            # Thread-safe UI update
            self.root.after(0, self.update_ui, photo, compliance_msg, color, frame)
            time.sleep(0.01)

    def update_ui(self, photo, msg, color, frame):
        if not self.camera_active: return
        self.canvas.config(image=photo)
        self.canvas.image = photo
        self.compliance_label.config(text=f"Status: {msg}", foreground=color)
        self.current_cv_image = frame


    def check_compliance(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return "No Face Detected", "red", False
        
        # Simple head pose logic
        landmarks = results.multi_face_landmarks[0].landmark
        # Nose tip (1), left eye (33), right eye (263)
        nose = landmarks[1]
        
        # Check if looking forward (yaw)
        # Ratio of nose center vs eye outer corners
        lx, rx = landmarks[33].x, landmarks[263].x
        eye_center = (lx + rx) / 2
        yaw_diff = abs(nose.x - eye_center)
        
        if yaw_diff > 0.05:
            return "Look Straight", "orange", False
            
        return "Compliant", "green", True

    def take_snapshot(self):
        if self.current_cv_image is not None:
            save_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG", "*.jpg")])
            if save_path:
                cv2.imwrite(save_path, self.current_cv_image)
                self.load_directory(os.path.dirname(save_path))
                messagebox.showinfo("Saved", "Photo captured and saved!")

    # --- IMAGE PROCESSING ACTIONS ---

    def action_remove_bg(self):
        if not self.selected_file: return
        self.status_bar.config(text="Processing background removal...")
        self.root.update_idletasks()
        
        def task():
            try:
                with open(self.selected_file, 'rb') as f:
                    final = ImageEngine.remove_bg(f.read())
                
                out = self.selected_file.replace(".", "_clean_bg.", 1)
                final.save(out)
                self.root.after(0, lambda: self.finish_processing(out))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=task).start()

    def action_auto_crop(self):
        if not self.selected_file: return
        self.status_bar.config(text="Auto-cropping to passport size...")
        
        def task():
            img = cv2.imread(self.selected_file)
            cropped, msg = ImageEngine.auto_crop_passport(img)
            if cropped is not None:
                out = self.selected_file.replace(".", "_passport_crop.", 1)
                cv2.imwrite(out, cropped)
                self.root.after(0, lambda: self.finish_processing(out))
            else:
                self.root.after(0, lambda: messagebox.showwarning("Warning", msg))

        threading.Thread(target=task).start()

    def action_enhance(self):
        if not self.selected_file: return
        self.status_bar.config(text="Enhancing image quality...")
        
        def task():
            img = cv2.imread(self.selected_file)
            enhanced = ImageEngine.enhance_quality(img)
            out = self.selected_file.replace(".", "_HD.", 1)
            cv2.imwrite(out, enhanced)
            self.root.after(0, lambda: self.finish_processing(out))

        threading.Thread(target=task).start()

    def action_print_sheet(self):
        if not self.selected_file: return
        out = self.selected_file.replace(".", "_print_sheet.", 1)
        if ImageEngine.generate_print_sheet(self.selected_file, out):
            self.finish_processing(out)
            messagebox.showinfo("Success", f"Print sheet generated!\n{out}")
        else:
            messagebox.showerror("Error", "Failed to generate print sheet")

    def finish_processing(self, new_file):
        self.load_directory(self.current_path)
        self.show_preview(new_file)
        self.status_bar.config(text=f"Process complete: {os.path.basename(new_file)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernApp(root)
    root.mainloop()
