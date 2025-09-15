import os
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
import subprocess
import platform
from rembg import remove
from PIL import Image, ImageTk
import io
import threading
import cv2
import numpy as np
import mediapipe as mp

class FileManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python File Manager")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")

        self.selected_file = None
        self.photo = None

        style = ttk.Style()
        style.configure("Treeview", font=('Segoe UI', 10), rowheight=28)
        style.configure("Treeview.Heading", font=('Segoe UI', 11, 'bold'))
        # Configure button-like appearance for the "Open" and "Rename" columns
        style.map("Treeview",
            fieldbackground=[('selected', '#347083')],
            foreground=[('selected', 'white')],
            background=[('selected', '#347083')]
        )
        style.configure("Treeview.Column", font=('Segoe UI', 10, 'underline'), foreground='blue')


        self.path_label = ttk.Label(root, text="Current Directory:", font=("Segoe UI", 10, "bold"))
        self.path_label.pack(pady=5)

        self.path_display = ttk.Entry(root, font=("Segoe UI", 10))
        self.path_display.pack(fill='x', padx=10)
        self.path_display.bind("<Return>", lambda e: self.load_files(self.path_display.get()))

        button_frame = ttk.Frame(root)
        button_frame.pack(pady=5)

        ttk.Button(button_frame, text="Browse", command=self.browse_folder).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Remove Background", command=self.remove_background).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Batch Remove BG", command=self.batch_remove_background).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Enhance Image Quality", command=self.enhance_image_quality).grid(row=0, column=3, padx=5)
        ttk.Button(button_frame, text="Estimate Head Pose", command=self.estimate_head_pose).grid(row=0, column=4, padx=5)
        ttk.Button(button_frame, text="Auto Crop", command=self.auto_crop_to_face_and_shoulders).grid(row=0, column=5, padx=5)


        self.status_label = ttk.Label(root, text="", font=("Segoe UI", 10, "italic"), foreground="green")
        self.status_label.pack(pady=5)

        self.tree_frame = ttk.Frame(root)
        self.tree_frame.pack(fill="both", expand=True)

        self.tree_scroll = ttk.Scrollbar(self.tree_frame)
        self.tree_scroll.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("name", "open_action", "rename_action"), # Added separate columns for actions
            show="headings",
            yscrollcommand=self.tree_scroll.set
        )
        self.tree.heading("name", text="File/Folder Name")
        self.tree.heading("open_action", text="Open") # New "Open" heading
        self.tree.heading("rename_action", text="Rename") # New "Rename" heading
        self.tree.column("name", width=550, anchor='w')
        self.tree.column("open_action", width=70, anchor='center') # Set width for "Open"
        self.tree.column("rename_action", width=70, anchor='center') # Set width for "Rename"
        self.tree.pack(fill="both", expand=True)

        self.tree_scroll.config(command=self.tree.yview)
        # Bind click events to specific columns
        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)

        self.img_label = tk.Label(self.root)
        self.img_label.pack(pady=10)

        self.load_files(os.path.expanduser("~"))

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.load_files(folder_selected)

    def load_files(self, path):
        self.current_path = path
        self.path_display.delete(0, tk.END)
        self.path_display.insert(0, path)
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    # Populate separate columns for Open and Rename actions
                    self.tree.insert("", "end", values=(entry.name, "Open", "Rename"))
        except PermissionError:
            messagebox.showerror("Error", "Permission denied.")

    def on_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        # Get the internal column identifier (e.g., '#1', '#2', '#3')
        col_internal_id = self.tree.identify_column(event.x)

        # Get the actual column name (e.g., 'name', 'open_action', 'rename_action')
        # This is more robust than relying on the internal #N identifiers
        column_name = self.tree.column(col_internal_id, option='id')

        item = self.tree.item(item_id)
        name = item['values'][0]
        full_path = os.path.join(self.current_path, name)
        self.selected_file = full_path # Update selected_file on any click in the row

        if column_name == 'open_action':
            self.open_file(full_path)
        elif column_name == 'rename_action':
            self.rename_file(full_path)


    def open_file(self, path):
        try:
            if os.path.isdir(path):
                self.load_files(path)
            else:
                self.selected_file = path
                if path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    img = Image.open(path)
                    img.thumbnail((300, 300))
                    self.photo = ImageTk.PhotoImage(img)
                    self.img_label.config(image=self.photo)
                else:
                    if platform.system() == "Windows":
                        os.startfile(path)
                    elif platform.system() == "Darwin":
                        subprocess.call(("open", path))
                    else:
                        subprocess.call(("xdg-open", path))
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def rename_file(self, path):
        new_name = simpledialog.askstring("Rename", "Enter new name:", initialvalue=os.path.basename(path))
        if new_name:
            new_path = os.path.join(os.path.dirname(path), new_name)
            try:
                os.rename(path, new_path)
                self.load_files(self.current_path)
            except Exception as e:
                messagebox.showerror("Error", f"Could not rename:\n{e}")

    def remove_background(self):
        if not self.selected_file or not self.selected_file.lower().endswith(('.png', '.jpg', '.jpeg')):
            messagebox.showwarning("No File", "Select a file by clicking on 'Open' or 'Rename' first.")
            return
        try:
            with open(self.selected_file, 'rb') as i:
                result = remove(i.read())

            result_image = Image.open(io.BytesIO(result)).convert("RGBA")
            white_bg = Image.new("RGBA", result_image.size, "WHITE")
            final_image = Image.alpha_composite(white_bg, result_image).convert("RGB")

            output_path = self.selected_file.replace(".", "_bg_removed.", 1)
            final_image.save(output_path)

            self.load_files(self.current_path)
            messagebox.showinfo("Success", f"Background removed.\nSaved as:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove background:\n{e}")

    def batch_remove_background(self):
        image_extensions = ('.png', '.jpg', '.jpeg')
        image_files = [os.path.join(self.current_path, f) for f in os.listdir(self.current_path)
                       if f.lower().endswith(image_extensions) and os.path.isfile(os.path.join(self.current_path, f))]

        if not image_files:
            messagebox.showinfo("No Images", "No image files found in the current directory.")
            return

        def task():
            self.status_label.config(text="Starting batch processing...")
            for index, file in enumerate(image_files, 1):
                try:
                    self.status_label.config(text=f"Processing {index}/{len(image_files)}: {os.path.basename(file)}")
                    with open(file, 'rb') as i:
                        result = remove(i.read())

                    result_image = Image.open(io.BytesIO(result)).convert("RGBA")
                    white_bg = Image.new("RGBA", result_image.size, "WHITE")
                    final_image = Image.alpha_composite(white_bg, result_image).convert("RGB")

                    output_path = file.replace(".", "_bg_removed.", 1)
                    final_image.save(output_path)
                except Exception as e:
                    print(f"Failed for {file}: {e}")

            self.status_label.config(text="Batch background removal completed!")
            self.load_files(self.current_path)

        threading.Thread(target=task).start()

    def enhance_image_quality(self):
        if not self.selected_file or not self.selected_file.lower().endswith(('.png', '.jpg', '.jpeg')):
            messagebox.showerror("Invalid", "Please select an image file first.")
            return

        try:
            img = cv2.imread(self.selected_file)
            if img is None:
                messagebox.showerror("Error", "Could not load image. Check file path or format.")
                return

            denoised_img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)

            gray_img = cv2.cvtColor(denoised_img, cv2.COLOR_BGR2GRAY)
            current_brightness = gray_img.mean()
            target_brightness = 120
            brightness_factor = target_brightness - current_brightness
            brightened_img = cv2.convertScaleAbs(denoised_img, alpha=1.0, beta=brightness_factor)

            hsv_img = cv2.cvtColor(brightened_img, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv_img)
            current_saturation = s.mean()
            target_saturation = 150
            saturation_factor = target_saturation / current_saturation if current_saturation > 0 else 1.0

            saturation_factor = min(max(saturation_factor, 0.8), 1.2)

            s_adjusted = cv2.convertScaleAbs(s, alpha=saturation_factor, beta=0)
            saturated_img = cv2.cvtColor(cv2.merge([h, s_adjusted, v]), cv2.COLOR_HSV2BGR)

            img_yuv = cv2.cvtColor(saturated_img, cv2.COLOR_BGR2YUV)
            enhancer = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            img_yuv[:, :, 0] = enhancer.apply(img_yuv[:, :, 0])
            contrast_enhanced_img = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)

            gray_for_laplacian = cv2.cvtColor(contrast_enhanced_img, cv2.COLOR_BGR2GRAY)
            variance_of_laplacian = cv2.Laplacian(gray_for_laplacian, cv2.CV_64F).var()
            blur_threshold = 100

            sharpened_img = contrast_enhanced_img

            if variance_of_laplacian < blur_threshold:
                sharpen_amount = 0.4
                blurred_for_unsharp = cv2.GaussianBlur(contrast_enhanced_img, (0, 0), sigmaX=3)
                sharpened_img = cv2.addWeighted(contrast_enhanced_img, 1.0 + sharpen_amount, blurred_for_unsharp, -sharpen_amount, 0)
                sharpened_img = np.clip(sharpened_img, 0, 255).astype(np.uint8)

            enhanced = cv2.resize(sharpened_img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

            output_path = self.selected_file.replace(".", "_auto_enhanced.", 1)
            cv2.imwrite(output_path, enhanced)

            self.load_files(self.current_path)
            messagebox.showinfo("Success", f"Image auto-enhanced and saved as:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to auto-enhance image:\n{e}")

    def estimate_head_pose(self):
        if not self.selected_file or not self.selected_file.lower().endswith(('.png', '.jpg', '.jpeg')):
            messagebox.showerror("Invalid File", "Please select an image file (JPG or PNG) first.")
            return

        try:
            image = cv2.imread(self.selected_file)
            img_h, img_w, _ = image.shape
            mp_face_mesh = mp.solutions.face_mesh
            face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, min_detection_confidence=0.5)

            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            result = face_mesh.process(image_rgb)

            if not result.multi_face_landmarks:
                messagebox.showinfo("Result", "No face detected")
                return

            face_landmarks = result.multi_face_landmarks[0]
            face_2d, face_3d = [], []

            for idx, lm in enumerate(face_landmarks.landmark):
                if idx in [33, 263, 1, 61, 291, 199]:
                    x, y = int(lm.x * img_w), int(lm.y * img_h)
                    face_2d.append([x, y])
                    face_3d.append([x, y, lm.z])

            face_2d = np.array(face_2d, dtype=np.float64)
            face_3d = np.array(face_3d, dtype=np.float64)

            focal_length = 1 * img_w
            cam_matrix = np.array([[focal_length, 0, img_w / 2], [0, focal_length, img_h / 2], [0, 0, 1]])
            dist_matrix = np.zeros((4, 1), dtype=np.float64)

            success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)
            rmat, _ = cv2.Rodrigues(rot_vec)
            angles, *_ = cv2.RQDecomp3x3(rmat)
            x, y, z = angles[0] * 360, angles[1] * 360, angles[2] * 360

            if y < -7:
                text = "Looking right"
            elif y > 7:
                text = "Looking left"
            elif x < -7:
                text = "Looking Down"
            elif x > 7:
                text = "Looking Up"
            else:
                text = "Looking Forward"

            if -5 < x < 5 and -5 < y < 5 and -5 < z < 5:
                passport_result = "✅ Suitable for passport photo"
            else:
                passport_result = "❌ Not suitable for passport photo"

            messagebox.showinfo("Head Pose Result",
                                 f"Pitch: {x:.2f}°\nYaw: {y:.2f}°\nRoll: {z:.2f}°\n\n{text}\n{passport_result}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to estimate head pose:\n{e}")

    def auto_crop_to_face_and_shoulders(self):
        if not self.selected_file or not self.selected_file.lower().endswith(('.png', '.jpg', '.jpeg')):
            messagebox.showerror("Invalid File", "Please select an image file (JPG or PNG) first.")
            return

        try:
            img = cv2.imread(self.selected_file)
            img_h, img_w, _ = img.shape

            mp_pose = mp.solutions.pose
            pose = mp_pose.Pose(static_image_mode=True)
            results = pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

            if not results.pose_landmarks:
                messagebox.showinfo("Result", "No pose landmarks detected.")
                return

            landmarks = results.pose_landmarks.landmark

            relevant_landmarks_indices = [
                mp_pose.PoseLandmark.NOSE,
                mp_pose.PoseLandmark.LEFT_EYE,
                mp_pose.PoseLandmark.RIGHT_EYE,
                mp_pose.PoseLandmark.LEFT_EAR,
                mp_pose.PoseLandmark.RIGHT_EAR,
                mp_pose.PoseLandmark.LEFT_SHOULDER,
                mp_pose.PoseLandmark.RIGHT_SHOULDER,
            ]

            x_coords = []
            y_coords = []

            for idx in relevant_landmarks_indices:
                if idx < len(landmarks):
                    lm = landmarks[idx]
                    x_coords.append(lm.x * img_w)
                    y_coords.append(lm.y * img_h)

            if not x_coords or not y_coords:
                messagebox.showinfo("Result", "No relevant pose landmarks detected for cropping.")
                return

            x_min_raw = min(x_coords)
            x_max_raw = max(x_coords)
            y_min_raw = min(y_coords)
            y_max_raw = max(y_coords)

            width_raw = x_max_raw - x_min_raw
            height_raw = y_max_raw - y_min_raw

            x_pad = int(0.3 * width_raw)
            y_pad_top = int(0.6 * height_raw)
            y_pad_bottom = int(0.2 * height_raw)

            x_min = max(0, int(x_min_raw - x_pad))
            x_max = min(img_w, int(x_max_raw + x_pad))
            y_min = max(0, int(y_min_raw - y_pad_top))
            y_max = min(img_h, int(y_max_raw + y_pad_bottom))

            min_crop_width = 100
            min_crop_height = 150
            if (x_max - x_min) < min_crop_width:
                center_x = (x_min + x_max) / 2
                x_min = max(0, int(center_x - min_crop_width / 2))
                x_max = min(img_w, int(center_x + min_crop_width / 2))
            if (y_max - y_min) < min_crop_height:
                center_y = (y_min + y_max) / 2
                y_min = max(0, int(center_y - min_crop_height / 2))
                y_max = min(img_h, int(center_y + min_crop_height / 2))

            cropped_img = img[y_min:y_max, x_min:x_max]

            output_path = self.selected_file.replace(".", "_autocrop.", 1)
            cv2.imwrite(output_path, cropped_img)

            self.load_files(self.current_path)
            messagebox.showinfo("Success", f"Image auto-cropped to face and shoulders.\nSaved as:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to auto-crop image:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = FileManagerApp(root)
    root.mainloop()
