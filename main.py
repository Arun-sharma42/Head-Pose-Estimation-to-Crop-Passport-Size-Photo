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
import math

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

        self.path_label = ttk.Label(root, text="Current Directory:", font=("Segoe UI", 10, "bold"))
        self.path_label.pack(pady=5)

        self.path_display = ttk.Entry(root, font=("Segoe UI", 10))
        self.path_display.pack(fill='x', padx=10)
        self.path_display.bind("<Return>", lambda e: self.load_files(self.path_display.get()))

        button_frame = ttk.Frame(root)
        button_frame.pack(pady=5)

        browse_btn = ttk.Button(button_frame, text="Browse", command=self.browse_folder)
        browse_btn.grid(row=0, column=0, padx=5)

        bg_remove_btn = ttk.Button(button_frame, text="Remove Background", command=self.remove_background)
        bg_remove_btn.grid(row=0, column=1, padx=5)

        batch_bg_remove_btn = ttk.Button(button_frame, text="Batch Remove BG", command=self.batch_remove_background)
        batch_bg_remove_btn.grid(row=0, column=2, padx=5)

        enhance_btn = ttk.Button(button_frame, text="Enhance Image Quality", command=self.enhance_image_quality)
        enhance_btn.grid(row=0, column=3, padx=5)

        tilt_btn = ttk.Button(button_frame, text="Fix Tilted Image", command=self.fix_tilted_image)
        tilt_btn.grid(row=0, column=4, padx=5)

        self.status_label = ttk.Label(root, text="", font=("Segoe UI", 10, "italic"), foreground="green")
        self.status_label.pack(pady=5)

        self.tree_frame = ttk.Frame(root)
        self.tree_frame.pack(fill="both", expand=True)

        self.tree_scroll = ttk.Scrollbar(self.tree_frame)
        self.tree_scroll.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("name", "actions"),
            show="headings",
            yscrollcommand=self.tree_scroll.set
        )
        self.tree.heading("name", text="File/Folder Name")
        self.tree.heading("actions", text="Actions")
        self.tree.column("name", width=550, anchor='w')
        self.tree.column("actions", width=100, anchor='center')
        self.tree.pack(fill="both", expand=True)

        self.tree_scroll.config(command=self.tree.yview)
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
                    self.tree.insert("", "end", values=(entry.name, "Open | Rename"))
        except PermissionError:
            messagebox.showerror("Error", "Permission denied.")

    def on_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        col = self.tree.identify_column(event.x)
        if col != '#2':
            return

        item = self.tree.item(item_id)
        name = item['values'][0]
        action_x = event.x - self.tree.column("#1", width=None)

        full_path = os.path.join(self.current_path, name)
        self.selected_file = full_path

        if action_x < 90:
            self.open_file(full_path)
        else:
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
        if not self.selected_file:
            messagebox.showwarning("No File", "Select a file by clicking on 'Open' or 'Rename' first.")
            return

        if not self.selected_file.lower().endswith((".png", ".jpg", ".jpeg")):
            messagebox.showerror("Invalid File", "Please select an image file (JPG or PNG).")
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
            img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)

            enhancer = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            img_yuv[:, :, 0] = enhancer.apply(img_yuv[:, :, 0])
            img_enhancer = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)

            sharpen_kernel = np.array([
                [-1, -1, -1],
                [-1, 9, -1],
                [-1, -1, -1]
            ])
            sharpened = cv2.filter2D(img_enhancer, -1, sharpen_kernel)
            enhanced = cv2.resize(sharpened, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

            output_path = self.selected_file.replace(".", "_enhanced.", 1)
            cv2.imwrite(output_path, enhanced)

            self.load_files(self.current_path)
            messagebox.showinfo("Success", f"Image enhanced and saved as:\n{output_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to enhance image:\n{e}")

    def fix_tilted_image(self):
        try:
            image = cv2.imread(self.selected_file)
            h, w = image.shape[:2]
            mp_pose = mp.solutions.pose
            pose = mp_pose.Pose(static_image_mode=True)
            result = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

            if not result.pose_landmarks:
                messagebox.showinfo("Pose Not Found", "No person detected in image.")
                return

            landmarks = result.pose_landmarks.landmark
            src_pts = np.float32([
                [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x * w, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y * h],
                [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x * w, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * h],
                [landmarks[mp_pose.PoseLandmark.NOSE].x * w, landmarks[mp_pose.PoseLandmark.NOSE].y * h]
            ])
            avg_y = (src_pts[0][1] + src_pts[1][1]) / 2
            dst_pts = np.float32([
                [w * 0.3, avg_y],
                [w * 0.7, avg_y],
                [w * 0.5, h * 0.3]
            ])
            matrix = cv2.getAffineTransform(src_pts, dst_pts)
            warped = cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_LINEAR)

            output_path = self.selected_file.replace(".", "_tilt_fixed.", 1)
            cv2.imwrite(output_path, warped)

            self.load_files(self.current_path)
            messagebox.showinfo("Success", f"Tilted posture fixed and saved as:\n{output_path}")

        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = FileManagerApp(root)
    root.mainloop()
