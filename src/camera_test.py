"""
Used to test functionality of live video feed, either from a connected webcam or
through connection with IP address, username, and password.

To use, run this file directly.
"""

import cv2
import tkinter as tk
from tkinter import ttk, messagebox

# Function to find all directly connected cameras (webcams, usb cameras, etc.)
def detect_cameras(max_cameras=10):
    index = 0
    available_cameras = []
    while len(available_cameras) < max_cameras:
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            available_cameras.append(index)
            cap.release()
        else:
            break
        index += 1
    return available_cameras

# Tests webcam selected by user (press q to quit)
def test_webcam(camera_index):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        messagebox.showerror("Error", f"Cannot open camera {camera_index}")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            messagebox.showerror("Error", "Can't receive frame (stream end?). Exiting ...")
            break

        cv2.imshow('Camera Test', frame)
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Tests connection to given ip address and its video feed (press q to quit)
def test_ip_camera(ip_address, username, password):
    
    # Correctly format the RTSP URL
    rtsp_url = f'rtsp://{username}:{password}@{ip_address}/1'
    print(f"Attempting to connect to: {rtsp_url}")

    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        messagebox.showerror("Error", f"Failed to open connection to IP camera at {ip_address}")
        return

    frame_count = 0
    while True:
        print(f"Reading frame {frame_count} from IP camera")
        ret, frame = cap.read()
        if not ret:
            print(f"Failed to receive frame {frame_count}")
            if frame_count == 0:
                messagebox.showerror("Error", "Failed to receive any frames from the camera. Please check your connection settings.")
                break
            else:
                messagebox.showwarning("Warning", f"Stream ended after {frame_count} frames.")
                break

        print(f"Showing video frame {frame_count}")
        cv2.imshow("IP Camera Feed", frame)
        frame_count += 1

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("User quit the video feed")
            break
    
    cap.release()
    cv2.destroyAllWindows()

# Build the simple GUI for testing
class CameraTestApp:
    
    # GUI initialization
    def __init__(self, root):
        self.root = root
        self.root.title("Camera Test")
        self.root.geometry("400x300")

        self.create_widgets()

    # Creates widgets for GUI interface
    def create_widgets(self):
        
        # Camera type selection
        self.camera_type_var = tk.StringVar(value="Webcam")
        self.webcam_radio = ttk.Radiobutton(self.root, text="Webcam", variable=self.camera_type_var, value="Webcam", command=self.toggle_camera_options)
        self.webcam_radio.pack(pady=5)
        self.ip_camera_radio = ttk.Radiobutton(self.root, text="IP Camera", variable=self.camera_type_var, value="IP Camera", command=self.toggle_camera_options)
        self.ip_camera_radio.pack(pady=5)

        # Webcam selection
        self.webcam_frame = ttk.Frame(self.root)
        self.webcam_frame.pack(pady=10)
        self.camera_label = ttk.Label(self.webcam_frame, text="Select Camera:")
        self.camera_label.pack(side=tk.LEFT, padx=5)

        available_cameras = detect_cameras()
        if not available_cameras:
            messagebox.showerror("Error", "No webcams detected.")
        
        self.camera_combo = ttk.Combobox(self.webcam_frame)
        self.camera_combo['values'] = [f"Camera {i}" for i in available_cameras]
        self.camera_combo.pack(side=tk.LEFT, padx=5)
        if available_cameras:
            self.camera_combo.current(0)  # Set the default selection to the first camera

        # IP camera details
        self.ip_camera_frame = ttk.Frame(self.root)
        self.ip_camera_frame.pack(pady=10)
        self.ip_camera_frame.pack_forget()  # Initially hidden

        ttk.Label(self.ip_camera_frame, text="IP Address:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.ip_address_var = tk.StringVar(value="10.1.16.114")  # Default IP
        ttk.Entry(self.ip_camera_frame, textvariable=self.ip_address_var).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(self.ip_camera_frame, text="Username:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.username_var = tk.StringVar(value="guest")  # Default username
        ttk.Entry(self.ip_camera_frame, textvariable=self.username_var).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(self.ip_camera_frame, text="Password:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.password_var = tk.StringVar()
        ttk.Entry(self.ip_camera_frame, textvariable=self.password_var, show="*").grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Test button
        self.test_button = ttk.Button(self.root, text="Test Camera", command=self.run_camera_test)
        self.test_button.pack(pady=10)

    # Used to toggle between testing for webcam or ip address camera
    def toggle_camera_options(self):
        if self.camera_type_var.get() == "Webcam":
            self.webcam_frame.pack()
            self.ip_camera_frame.pack_forget()
        else:
            self.webcam_frame.pack_forget()
            self.ip_camera_frame.pack()

    # Starts testing program
    def run_camera_test(self):
        self.root.withdraw()  # Hide the main window
        
        if self.camera_type_var.get() == "Webcam":
            camera_index = int(self.camera_combo.get().split()[1])
            test_webcam(camera_index)
        else:
            ip_address = self.ip_address_var.get()
            username = self.username_var.get()
            password = self.password_var.get()
            test_ip_camera(ip_address, username, password)
        
        self.root.deiconify()  # Show the main window again after the test


if __name__ == "__main__":
    root = tk.Tk()
    app = CameraTestApp(root)
    root.mainloop()