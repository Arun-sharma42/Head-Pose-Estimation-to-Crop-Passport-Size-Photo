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
