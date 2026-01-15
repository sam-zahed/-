# Vision Module

## Overview
- Endpoint: POST /vision/detect -> accepts image file, returns detections
- Endpoint: POST /vision/estimate_ttc -> query params distance_m, relative_speed_m_s

## Replacing the DummyDetector with YOLOv8 (example)
1. Install ultralytics:
   ```bash
   pip install ultralytics
   ```
2. In `app/vision/model.py` replace DummyDetector with real loading:
   ```py
   from ultralytics import YOLO
   model = YOLO('yolov8n.pt')
   def detect(image_bytes):
       # convert bytes to numpy array via cv2.imdecode and run model
       ...
   ```

## Notes on TTC
- You need either depth estimate or stereo/monocular depth model to compute real distances.
- Alternatively use bounding-box size heuristics + calibration.
