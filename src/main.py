"""
This file contains the main() function of the program which handles the main logic and continual loop
that runs while the program is processing frames.
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow INFO and WARNING messages
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN custom operations warnings

import csv
import time
import datetime
import absl.logging
from queue import Queue
from threading import Thread, Event

import cv2
import configparser
import tensorflow as tf

from capture import start_video_feed, start_ip_camera
from detection import load_model, perform_object_detection
from tracker import ObjectTracker

absl.logging.set_verbosity(absl.logging.ERROR)  # Suppress TensorFlow and absl warnings
tf.debugging.set_log_device_placement(False)  # Disable log device placement

"""Handles exporting the summary statistics to a csv file"""
def export_summary_to_csv(detailed_summary, actual_duration, start_time):
    
    # Create a 'reports' directory if it doesn't exist
    reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
    os.makedirs(reports_dir, exist_ok=True)

    # Generate filename with current date and time
    current_time = datetime.datetime.fromtimestamp(start_time)
    filename = f"Summary_Results_{current_time.strftime('%Y-%m-%d_%H-%M-%S')}.csv"
    
    # Create the full file path
    filepath = os.path.join(reports_dir, filename)
    
    with open(filepath, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        
        # Write header
        csvwriter.writerow(['Object Type', 'Object ID', 'First Seen (s)', 'Last Seen (s)', 'Total Time in Frame (s)'])
        
        # Write data
        for label, objects in detailed_summary.items():
            for obj in objects:
                csvwriter.writerow([
                    label,
                    obj['id'],
                    f"{obj['first_seen']:.2f}",
                    f"{obj['last_seen']:.2f}",
                    f"{obj['total_time']:.2f}"
                ])
        
        # Write total duration
        csvwriter.writerow([])
        csvwriter.writerow(['Total Detection Duration (s)', f"{actual_duration:.2f}"])
    
    print(f"Summary exported to reports directory.")

"""Handles capturing frames from the video feed and storing them in a queue to be processed"""
def capture_frames(video_feed, frame_queue, stop_event):
    frame_count = 0
    while not stop_event.is_set():
        ret, frame = video_feed.read()
        if not ret:
            break
        
        frame_count += 1
        frame_queue.put((frame_count, time.time(), frame))

        # Limit the size of the queue for resource purposes
        if frame_queue.qsize() > 100:
            try:
                frame_queue.get_nowait()
            except Queue.Empty:
                pass
    video_feed.release()

"""
Main loop of the program that handles continually reading in frames of the video feed
and processing them with object detection until the user specified runtime has been reached.

Continuous detection is automatically set to true
(The program will perform object detection continually the entire runtime, not wait for an alarm)
"""
def main(*args):
    
    print("Initializing object detection...")
    model = load_model()
    print("Model loaded successfully.")
    
    # Selecting Webcam provides 5 arguments to the function
    if len(args) == 5:
        camera_index, detection_duration, continuous_detection, export_summary, selected_objects = args
        print(f"Attempting to start video feed from webcam (index: {camera_index})...")
        video_feed = start_video_feed(camera_index)
        
    # Selecting IP Camera provides 7 arguments to the function
    elif len(args) == 7:
        ip_address, username, password, detection_duration, continuous_detection, export_summary, selected_objects = args
        print(f"Attempting to connect to IP camera at {ip_address}...")
        video_feed = start_ip_camera(ip_address, username, password)
    else:
        raise ValueError("Invalid number of arguments")

    if not video_feed.isOpened():
        print("Error: Failed to initialize video feed. Please check your camera connection and settings.")
        return

    print("Video feed initialized successfully.")
    
    # Create a tracker object to store detected objects in
    tracker = ObjectTracker(iou_threshold=0.5, selected_objects=selected_objects)

    # Create the queue for storing incoming video frames
    frame_queue = Queue(maxsize=1000)
    stop_event = Event()

    # Create a separate thread for running capture_frames on, which allows the program to
    # separate loading frames and processing them into different threads for better efficiency
    capture_thread = Thread(target=capture_frames, args=(video_feed, frame_queue, stop_event))
    capture_thread.start()
    
    # Setup needed variables
    start_time = time.time()  # The time when the program begins
    end_time = start_time + detection_duration  # The time when the program should terminate
    last_print_time = start_time  # The time the program last printed remaining runtime
    
    last_catchup_time = start_time  # The time when the program last "caught up" to remain real-time
    catchup_interval = 0.5  # Catch up every ___ seconds
        
    processed_frame_count = 0

    print("\nStarting Detection")
    try:
        # Run until the current time reaches the calculated end time
        while time.time() < end_time:
            current_time = time.time()

            # Check if it's time to catch up
            if current_time - last_catchup_time >= catchup_interval:
                
                # Skip to the most recent frame by emptying the current queue and getting the next frame
                skipped_frames = 0
                while not frame_queue.empty():
                    frame_count, timestamp, frame = frame_queue.get()
                    skipped_frames += 1
                    
                if skipped_frames > 0:
                    last_catchup_time = current_time
            
            # If it is not time to "catch up", process next frame in queue normally
            else:
                if frame_queue.empty():
                    time.sleep(0.01)
                    continue
                frame_count, timestamp, frame = frame_queue.get()
            
            frame_time = timestamp - start_time
            processed_frame_count += 1

            # Perform object detection on the current frame
            detections = perform_object_detection(model, frame)
            
            # Update the tracker's info on tracked objects so far
            tracker.update(detections, frame_time)

            # Draw bounding boxes and labels for detected objects
            for detection in detections:
                bbox = detection['bbox']
                label = detection['label']
                obj_id = tracker._find_matching_object(bbox, label)
                if obj_id is not None:
                    obj_info = tracker.tracked_objects[obj_id]
                    xmin, ymin, xmax, ymax = bbox
                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
                    cv2.putText(frame, f"{label} ({obj_id})", (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

            # Show the live feed / current frame with bounding boxes and labels
            cv2.imshow('Object Detection', frame)
            
            # Every 30 seconds, print how much runtime the program has left along with other info
            if current_time - last_print_time >= 30:
                remaining_time = end_time - current_time
                fps = processed_frame_count / (current_time - start_time)
                print(f"Current time: {frame_time:.2f}, Remaining: {remaining_time:.2f}, FPS: {fps:.2f}")
                last_print_time = current_time
            
            # If the user presses 'q' during runtime, quit the object detection
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Detection stopped by user.")
                break

    except KeyboardInterrupt:
        print("Detection interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
    
    finally:
        
        # Calculates actual runtime duration (processing times slightly alter actual runtime)
        actual_duration = time.time() - start_time
        stop_event.set()
        capture_thread.join()
        cv2.destroyAllWindows()
        
        # Prints summary of the program's results to the console
        print("\nDetailed summary of detected objects:")
        detailed_summary = tracker.get_detailed_summary()
        for label, objects in detailed_summary.items():
            print(f"\n{label}:")
            for obj in objects:
                print(f"  Object ID: {obj['id']}")
                print(f"    First seen: {obj['first_seen']:.2f} seconds")
                print(f"    Last seen: {obj['last_seen']:.2f} seconds")
                print(f"    Total time in frame: {obj['total_time']:.2f} seconds")

        # Exports to csv file if selected by user to do so
        if export_summary:
            export_summary_to_csv(detailed_summary, actual_duration, start_time)
        
        print(f"Detection completed. Total duration: {actual_duration:.2f} seconds")
        print(f"Frames processed: {frame_count}")
        print(f"Average FPS: {frame_count / actual_duration:.2f}")

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    camera_type = config.get('Settings', 'CAMERA_TYPE', fallback='Webcam')
    
    # Get the appropriate config settings from config.ini depending on which type of camera is being used
    if camera_type == 'Webcam':
        main(
            config.getint('Settings', 'CAMERA_INDEX'),
            config.getint('Settings', 'DETECTION_DURATION'),
            config.getboolean('Settings', 'CONTINUOUS_DETECTION'),
            config.getboolean('Settings', 'EXPORT_SUMMARY', fallback=False),
            config.get('Settings', 'SELECTED_OBJECTS', fallback='').split(',')
        )
    else:  # IP Camera
        main(
            config.get('Settings', 'IP_ADDRESS'),
            config.get('Settings', 'USERNAME'),
            config.get('Settings', 'PASSWORD'),
            config.getint('Settings', 'DETECTION_DURATION'),
            config.getboolean('Settings', 'CONTINUOUS_DETECTION'),
            config.getboolean('Settings', 'EXPORT_SUMMARY', fallback=False),
            config.get('Settings', 'SELECTED_OBJECTS', fallback='').split(',')
        )