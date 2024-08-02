"""
Used to handle capturing live video feed from a camera or video file.
"""

import cv2

# Returns the video feed from camera specified by CAMERA_INDEX (Built-in Webcam, USB Webcam, etc.)
def start_video_feed(CAMERA_INDEX):
    return cv2.VideoCapture(CAMERA_INDEX)

# Returns the video capture of a local video file
def start_video_file(file_path):
    return cv2.VideoCapture(file_path)

# Returns the video feed from a Camera connected to through an IP Address
# (When running on lab computers, connects to cameras connected through Ethernet)
def start_ip_camera(ip_address, username, password):
    # Correctly format the RTSP URL
    rtsp_url = f'rtsp://{username}:{password}@{ip_address}/1'
    return cv2.VideoCapture(rtsp_url)