"""
Object Tracker class used by the program to keep track of detected objects, current and previous,
and match detections to their correct unqiue real-life objects.

CLASS INFO:
Each object that is detected throughout the course of the program is assigned an ID, with the first object starting at ID 1.
An object's data and location within the frame are stored in the tracked_objects dictionary with the key being its ID.
For each frame, the program compares the currently detected objects with the data for all previously detected objects to
determine if they are the same real-life object as detected before, or if a "new object" has entered the frame.
A "new object" refers to an object in the frame that gets detected by the program, but does not match the data of any
previously detected object, and therefore is assumed to be a new real-life object in the frame.
"""


"""
Class variables:
        tracked_objects: dictionary of objects detected by the program so far that is is keeping track of
        next_object_id: the next id to be assigned to a new object when it is detected
        iou_threshold: the threshold for determining if two objects are the same from frame to frame
        first_frame_time: stores the time of the first frame processed by the program
        selected_objects: the types of objects to detect selected by the user in the GUI
        missing_threshold: the threshold for determining that an object has permanently left the frame
"""
class ObjectTracker:
    
    """ObjectTracker Initialization"""
    def __init__(self, iou_threshold=0.5, selected_objects=None, missing_threshold=20):
        self.tracked_objects = {}
        self.next_object_id = 1
        self.iou_threshold = iou_threshold
        self.first_frame_time = None
        self.selected_objects = selected_objects or []
        self.missing_threshold = missing_threshold
    
    """    
    Updates the list of detected objects with new detection data
    
    Params:
        detections: list of objects detected and their data in the CURRENT frame
        frame_time: current time of the new frame
    """
    def update(self, detections, frame_time):
        
        # Set the time of the first frame processed after starting the program
        if self.first_frame_time is None:
            self.first_frame_time = frame_time

        matched_ids = set()

        # Iterate through the current detected objects and find matches in previous tracked objects
        for detection in detections:
            bbox = detection['bbox']
            label = detection['label']
            
            if label not in self.selected_objects:
                continue  # Skip over any object types not selected by the user
            
            matched_obj_id = self._find_matching_object(bbox, label)
                
            if matched_obj_id is not None:
                # Update matched object with new current info
                obj_info = self.tracked_objects[matched_obj_id]
                obj_info['bbox'] = bbox
                obj_info['last_seen'] = frame_time
                obj_info['total_time'] = frame_time - obj_info['first_seen']
                obj_info['missing_frames'] = 0  # Reset missing_frames counter
                matched_ids.add(matched_obj_id)
            else:
                # Add new object if no match found
                new_id = self.next_object_id
                self.next_object_id += 1
                self.tracked_objects[new_id] = {
                    'id': new_id,
                    'label': label,
                    'bbox': bbox,
                    'first_seen': frame_time,
                    'last_seen': frame_time,
                    'total_time': 0,
                    'missing_frames': 0,
                    'missing': False
                }
                matched_ids.add(new_id)
        
        # Update missing_frames for previously tracked objects with no current match
        for obj_id, obj_info in self.tracked_objects.items():
            if obj_id not in matched_ids and not obj_info['missing']:
                obj_info['missing_frames'] += 1
                if obj_info['missing_frames'] >= self.missing_threshold:
                    obj_info['missing'] = True
            elif obj_id in matched_ids and obj_info['missing_frames'] > 0:
                obj_info['missing_frames'] = 0  # Reset counter if object reappears
    
    """Finds the matching object in previously tracked objects if one exists"""
    def _find_matching_object(self, bbox, label):
        for obj_id, obj_info in self.tracked_objects.items():
            if not obj_info['missing'] and obj_info['label'] == label and self._iou(bbox, obj_info['bbox']) > self.iou_threshold:
                return obj_id
        return None

    """Creates a summary of the tracked objects"""
    def get_detailed_summary(self):
        summary = {}
        for obj_id, obj_info in self.tracked_objects.items():
            label = obj_info['label']
            if label not in summary:
                summary[label] = []
            summary[label].append({
                'id': obj_info['id'],
                'first_seen': obj_info['first_seen'] - self.first_frame_time,
                'last_seen': obj_info['last_seen'] - self.first_frame_time,
                'total_time': obj_info['total_time'],
                'missing_frames': obj_info['missing_frames'],
                'missing': obj_info['missing']
            })
        return summary

    """Compute Intersection over Union (IoU) between two objects' bounding boxes."""
    def _iou(self, box1, box2):
        x1, y1, x2, y2 = box1
        x1g, y1g, x2g, y2g = box2

        xi1 = max(x1, x1g)
        yi1 = max(y1, y1g)
        xi2 = min(x2, x2g)
        yi2 = min(y2, y2g)
        inter_area = max(xi2 - xi1, 0) * max(yi2 - yi1, 0)
        
        box1_area = (x2 - x1) * (y2 - y1)
        box2_area = (x2g - x1g) * (y2g - y1g)
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0