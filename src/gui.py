"""
This file contains the Graphical User Interface (GUI) for controlling the running of the program.

Running this file directly will give the user an interface to select and input specific
settings for the program, and allow the user to run it with those settings.
"""

import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import configparser
import cv2

from main import main as start_detection

CONFIG_FILE = 'config.ini'

"""Used to update the config file based on settings the user selects"""
def update_config(section, option, value):
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    
    # Add section to the config file if it doesn't exist
    if not config.has_section(section):
        config.add_section(section)
    
    # Set the config setting to what the user chooses
    config.set(section, option, str(value))
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

"""Used to find any cameras connected to the device (webcam, via USB, etc.)"""
def detect_cameras(max_cameras=10):
    index = 0
    available_cameras = []
    while len(available_cameras) < max_cameras:
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            available_cameras.append(index + 1)
            cap.release()
        else:
            break
        index += 1
        if index >= max_cameras:
            break
        
    # Returns all the indexes of exisitng cameras to be displayed on the GUI
    return available_cameras

"""The GUI interface for the user to use to run the program with the settings they desire"""
class App:
    
    # Initialization
    def __init__(self, root):
        self.root = root
        self.root.title("Object Detection")

        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_FILE)
        
        # If changes are made to the possible types of objects to detect, this list must also be changed
        self.object_types = ['person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck', 'bird', 'cat', 'dog']
        self.object_vars = {}
        
        self.create_widgets()

    # Creates all the sections of the GUI
    def create_widgets(self):
        
        # Camera selection
        camera_frame = ttk.LabelFrame(self.root, text="Camera Selection")
        camera_frame.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

        self.camera_type_var = tk.StringVar(value="Webcam")
        self.camera_type_radio_webcam = ttk.Radiobutton(camera_frame, text="Webcam", variable=self.camera_type_var, value="Webcam", command=self.toggle_camera_options)
        self.camera_type_radio_webcam.grid(row=0, column=0, padx=10, pady=5)
        self.camera_type_radio_ip = ttk.Radiobutton(camera_frame, text="IP Camera", variable=self.camera_type_var, value="IP Camera", command=self.toggle_camera_options)
        self.camera_type_radio_ip.grid(row=0, column=1, padx=10, pady=5)

        available_cameras = detect_cameras()
        if not available_cameras:
            messagebox.showerror("Error", "No cameras detected.")
            self.root.quit()
            return

        self.camera_combo = ttk.Combobox(camera_frame)
        self.camera_combo['values'] = [f"Camera {i}" for i in available_cameras]
        self.camera_combo.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.camera_combo.current(0)  # Set the default selection to the first camera

        # IP camera details frame
        self.ip_camera_frame = ttk.Frame(camera_frame)
        self.ip_camera_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.ip_camera_frame.grid_remove()  # Hide initially

        ttk.Label(self.ip_camera_frame, text="IP Address:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.ip_address_var = tk.StringVar(value="10.1.16.114") #Default IP address
        ttk.Entry(self.ip_camera_frame, textvariable=self.ip_address_var).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(self.ip_camera_frame, text="Username:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.username_var = tk.StringVar(value="guest") #Default username
        ttk.Entry(self.ip_camera_frame, textvariable=self.username_var).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(self.ip_camera_frame, text="Password:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.password_var = tk.StringVar()
        ttk.Entry(self.ip_camera_frame, textvariable=self.password_var, show="*").grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Detection settings frame
        detection_frame = ttk.LabelFrame(self.root, text="Detection Settings")
        detection_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

        # Runtime input in hours, minutes, seconds
        ttk.Label(detection_frame, text="Detection Runtime:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        runtime_frame = ttk.Frame(detection_frame)
        runtime_frame.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        self.hours_var = tk.StringVar(value="0")
        self.minutes_var = tk.StringVar(value="0")
        self.seconds_var = tk.StringVar(value="30")

        ttk.Entry(runtime_frame, textvariable=self.hours_var, width=3).pack(side=tk.LEFT)
        ttk.Label(runtime_frame, text="h", width=2).pack(side=tk.LEFT)
        ttk.Entry(runtime_frame, textvariable=self.minutes_var, width=3).pack(side=tk.LEFT)
        ttk.Label(runtime_frame, text="m", width=3).pack(side=tk.LEFT)
        ttk.Entry(runtime_frame, textvariable=self.seconds_var, width=3).pack(side=tk.LEFT)
        ttk.Label(runtime_frame, text="s", width=2).pack(side=tk.LEFT)

        # Object type selection
        self.object_frame = ttk.LabelFrame(self.root, text="Object Types to Detect")
        self.object_frame.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

        self.all_objects_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.object_frame, text="All Object Types", variable=self.all_objects_var, command=self.toggle_all_objects).grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        for i, obj_type in enumerate(self.object_types):
            self.object_vars[obj_type] = tk.BooleanVar(value=True)
            ttk.Checkbutton(self.object_frame, text=obj_type.capitalize(), variable=self.object_vars[obj_type], command=self.update_all_objects_state).grid(row=i//3+1, column=i%3, padx=5, pady=2, sticky="w")

        # Export summary checkbox
        self.export_var = tk.BooleanVar(value=False)
        self.export_checkbox = ttk.Checkbutton(self.root, text="Export Summary", variable=self.export_var)
        self.export_checkbox.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        # Start button
        self.start_button = ttk.Button(self.root, text="Start Detection", command=self.start_detection)
        self.start_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

        # Exit button
        self.exit_button = ttk.Button(self.root, text="Exit", command=self.exit_program)
        self.exit_button.grid(row=4, column=2, columnspan=2, padx=10, pady=10)

    """Toggles the GUI between the selected Webcam view and IP Camera view"""
    def toggle_camera_options(self):
        if self.camera_type_var.get() == "Webcam":
            self.camera_combo.grid()
            self.ip_camera_frame.grid_remove()
        else:
            self.camera_combo.grid_remove()
            self.ip_camera_frame.grid()

    """Toggles all the object types' checkboxes depending on if "All Object Types" is selected"""
    def toggle_all_objects(self):
        state = self.all_objects_var.get()
        for var in self.object_vars.values():
            var.set(state)

    """Updates all object variable"""
    def update_all_objects_state(self):
        if all(var.get() for var in self.object_vars.values()):
            self.all_objects_var.set(True)
        else:
            self.all_objects_var.set(False)

    """Starts the object detection program upon pressening 'Start' button"""
    def start_detection(self):
        camera_type = self.camera_type_var.get()

        # Convert time input to actual integers
        try:
            hours = int(self.hours_var.get())
            minutes = int(self.minutes_var.get())
            seconds = int(self.seconds_var.get())
            total_seconds = hours * 3600 + minutes * 60 + seconds
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for hours, minutes, and seconds.")
            return

        continuous_detection = True  # Default to Continuous Detection
        export_summary = self.export_var.get()
        
        selected_objects = [obj_type for obj_type, var in self.object_vars.items() if var.get()]

        # Updates config file with selected settings
        update_config('Settings', 'continuous_detection', continuous_detection)
        update_config('Settings', 'detection_duration', total_seconds)
        update_config('Settings', 'export_summary', export_summary)
        update_config('Settings', 'selected_objects', ','.join(selected_objects))

        # Sets the detection_args depending on which camera type was selected
        if camera_type == "Webcam":
            camera_index = int(self.camera_combo.get().split()[1]) - 1
            update_config('Settings', 'camera_type', 'Webcam')
            update_config('Settings', 'camera_index', camera_index)
            detection_args = (camera_index, total_seconds, continuous_detection, export_summary, selected_objects)
        else:
            ip_address = self.ip_address_var.get()
            username = self.username_var.get()
            password = self.password_var.get()
            update_config('Settings', 'camera_type', 'IP Camera')
            update_config('Settings', 'ip_address', ip_address)
            update_config('Settings', 'username', username)
            update_config('Settings', 'password', password)
            detection_args = (ip_address, username, password, total_seconds, continuous_detection, export_summary, selected_objects)

        # Run the detection in a separate thread to avoid blocking the GUI
        detection_thread = threading.Thread(target=self.run_detection_and_update_gui, args=detection_args)
        detection_thread.start()
        
    # Start the detection in separate thread
    def run_detection_and_update_gui(self, *args):
        start_detection(*args)
        self.root.after(0, self.update_gui_after_detection)

    # Sets 'Start' button back to normal
    def update_gui_after_detection(self):
        self.start_button.config(state='normal')
        messagebox.showinfo("Detection Completed", "Object detection has finished.")

    # Exits the program with the 'Exit' button
    def exit_program(self):
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            self.root.quit()
            sys.exit()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()