"""
This file is used as the main file to test the object detection on a local video file.

This GUI allows user to upload a video file and performs object detection on it
in the same way it uses a live camera, with the same summary of results.
(Currently supports mp4, avi, mov file types)

To use, run this file directly.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from main import process_video
import threading
import sys

class VideoFileApp:
    
    # Initialization of the GUI interface
    def __init__(self, root):
        self.root = root
        self.root.title("Video File Object Detection")
        
        self.video_path = None
        self.object_types = ['person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck', 'bird', 'cat', 'dog']
        self.object_vars = {}
        
        self.create_widgets()

    # Handles creation of the GUI interface
    def create_widgets(self):
        
        # File selection
        self.file_frame = ttk.Frame(self.root)
        self.file_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(self.file_frame, textvariable=self.file_path_var, width=50)
        self.file_entry.grid(row=0, column=0, padx=5)

        self.browse_button = ttk.Button(self.file_frame, text="Browse", command=self.browse_file)
        self.browse_button.grid(row=0, column=1, padx=5)

        # Selection of object types to select
        self.object_frame = ttk.LabelFrame(self.root, text="Object Types to Detect")
        self.object_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.all_objects_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.object_frame, text="All Object Types", variable=self.all_objects_var, command=self.toggle_all_objects).grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        for i, obj_type in enumerate(self.object_types):
            self.object_vars[obj_type] = tk.BooleanVar(value=True)
            ttk.Checkbutton(self.object_frame, text=obj_type.capitalize(), variable=self.object_vars[obj_type], command=self.update_all_objects_state).grid(row=i//3+1, column=i%3, padx=5, pady=2, sticky="w")

        # Export summary checkbox
        self.export_var = tk.BooleanVar(value=False)
        self.export_checkbox = ttk.Checkbutton(self.root, text="Export Summary", variable=self.export_var)
        self.export_checkbox.grid(row=2, column=0, columnspan=2, padx=10, pady=5)

        # Start button
        self.start_button = ttk.Button(self.root, text="Start Detection", command=self.start_detection)
        self.start_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

        # Exit program button
        self.exit_button = ttk.Button(self.root, text="Exit", command=self.exit_program)
        self.exit_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

    # Function called to browse local machine for video file to upload
    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if file_path:
            self.video_path = file_path
            self.file_path_var.set(file_path)

    # Used to toggle object type checkboxes based on if "All Object Types" is selected
    def toggle_all_objects(self):
        state = self.all_objects_var.get()
        for var in self.object_vars.values():
            var.set(state)


    def update_all_objects_state(self):
        if all(var.get() for var in self.object_vars.values()):
            self.all_objects_var.set(True)
        else:
            self.all_objects_var.set(False)

    # Function that starts the program
    def start_detection(self):
        if not self.video_path:
            messagebox.showerror("Error", "Please select a video file.")
            return

        export_summary = self.export_var.get()
        selected_objects = [obj_type for obj_type, var in self.object_vars.items() if var.get()]

        # Run the detection in a separate thread to avoid blocking the GUI
        detection_thread = threading.Thread(target=self.run_detection_and_update_gui, 
                                            args=(self.video_path, export_summary, selected_objects))
        detection_thread.start()
        
    # Calls object detection process from main.py to begin
    def run_detection_and_update_gui(self, video_path, export_summary, selected_objects):
        process_video(video_path, export_summary, selected_objects)
        self.root.after(0, self.update_gui_after_detection)

    # Returns GUI to normal and gives completion notice
    def update_gui_after_detection(self):
        self.start_button.config(state='normal')
        messagebox.showinfo("Detection Completed", "Object detection has finished.")

    # Exits the program and all related windows
    def exit_program(self):
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            self.root.quit()
            sys.exit()



if __name__ == "__main__":
    root = tk.Tk()
    app = VideoFileApp(root)
    root.mainloop()