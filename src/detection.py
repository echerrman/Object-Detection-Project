"""
Handles the object detection process of the program

Currently using COCO dataset trained models
SSD Mobilenet V2: less accurate, but faster and less resources required
EfficientDet D5: much higher accuracy, slow and high resource load required
"""

import tensorflow as tf
import cv2

# Load the COCO label map with only the object types relevant to project
COCO_LABELS = {
    1: 'person',
    2: 'bicycle',
    3: 'car',
    4: 'motorcycle',
    6: 'bus',
    8: 'truck',
    16: 'bird',
    17: 'cat',
    18: 'dog'
}

"""Loads TensorFlow model from the hard-coded filepath"""
def load_model():
    model = tf.saved_model.load('models/ssd_mobilenet_v2/saved_model')
    return model

"""Handles object detection processing on a frame and returns detected objects"""
def perform_object_detection(model, frame):
    
    # Resize the frame to the model's expected input size
    input_size = (320, 320)  # Replace with the model's input size if needed
    resized_frame = cv2.resize(frame, input_size)

    # Convert frame to tensor and add a batch dimension
    input_tensor = tf.convert_to_tensor(resized_frame)
    input_tensor = tf.expand_dims(input_tensor, 0)

    # Perform the detection
    detections = model(input_tensor)

    # Post-process detections
    processed_detections = []
    for i in range(detections['detection_boxes'].shape[1]):
        if detections['detection_scores'][0][i].numpy() > 0.5:  # Filter out low confidence detections
            ymin, xmin, ymax, xmax = detections['detection_boxes'][0][i].numpy()
            class_id = int(detections['detection_classes'][0][i].numpy())
            label = COCO_LABELS.get(class_id)
            
            # Only include detections for the specified object types
            if label:
                bbox = {
                    'bbox': (int(xmin * frame.shape[1]), int(ymin * frame.shape[0]), 
                             int(xmax * frame.shape[1]), int(ymax * frame.shape[0])),
                    'label': label
                }
                processed_detections.append(bbox)

    return processed_detections