from django.shortcuts import render
import os
import cv2
import numpy as np
import time
from django.http import StreamingHttpResponse
from django.core.files.storage import FileSystemStorage
from .sort import Sort 
from ultralytics import YOLO

# --- Constants ---
CALIBRATION_DISTANCE = 5 
CALIBRATION_PIXELS = 200 
PIXEL_TO_METER = CALIBRATION_DISTANCE / CALIBRATION_PIXELS
FRAME_RATE = 30

# Initialize Model and Tracker
model_path = os.path.join('ai_models', 'yolov8n.pt')
model = YOLO(model_path)
tracker = Sort(max_age=30)

# --- 1. The Main Page View (Handles Upload) ---
def monitor_page(request):
    context = {}
    if request.method == 'POST' and request.FILES.get('video'):
        video_file = request.FILES['video']
        fs = FileSystemStorage()
        filename = fs.save(video_file.name, video_file)
        video_path = fs.path(filename)
        
        request.session['current_video_path'] = video_path
        context['video_uploaded'] = True
        context['video_name'] = video_file.name

    return render(request, 'vehiclespeed/monitor.html', context)

# --- 2. The Stream View ---
def live_monitor(request):
    video_path = request.session.get('current_video_path')
    if not video_path or not os.path.exists(video_path):
        video_path = 0 
    return StreamingHttpResponse(stream_frames(video_path), 
                                 content_type='multipart/x-mixed-replace; boundary=frame')

# --- 3. The Optimized Processing Logic ---
def stream_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    prev_positions = {}
    speed_log = {} 
    frame_count = 0  # Counter to track frames
    
    while True:
        success, frame = cap.read()
        if not success:
            break

        frame_count += 1
        
        # --- NEW OPTIMIZATION: Skip Frames ---
        # Only process every 10th frame to keep the video moving on slow CPUs.
        # If the video is still too slow, change '10' to '15'.
        if frame_count % 10 != 0:
            continue

        # Resize the frame to save RAM
        frame = cv2.resize(frame, (640, 360))

        detections = np.empty((0, 5))
        
        # --- NEW OPTIMIZATION: Lowered conf to 0.25 ---
        # This helps detect vehicles more easily in low-resolution frames.
        results = model(frame, stream=True, imgsz=320, conf=0.25)

        for info in results:
            for box in info.boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                conf = box.conf[0]
                cls = int(box.cls[0])
                # Detecting Cars, Motorcycles, Buses, and Trucks
                if cls in [2, 3, 5, 7] and conf > 0.25: 
                    new_det = np.array([int(x1), int(y1), int(x2), int(y2), conf])
                    detections = np.vstack((detections, new_det))

        track_result = tracker.update(detections)
        
        # Because we skip 10 frames, we adjust the time calculation
        # Time elapsed = (number of frames skipped) / (original frame rate)
        adjusted_frame_time = 10 / FRAME_RATE

        for result in track_result:
            x1, y1, x2, y2, obj_id = map(int, result)
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2

            if obj_id in prev_positions:
                prev_x, prev_y, _ = prev_positions[obj_id]
                dist_px = np.sqrt((center_x - prev_x)**2 + (center_y - prev_y)**2)
                # Use the adjusted time for accurate speed calculation
                speed = (dist_px * PIXEL_TO_METER) / adjusted_frame_time * 3.6
                
                if speed > 0:
                    if obj_id not in speed_log or speed > speed_log[obj_id]:
                        speed_log[obj_id] = round(speed, 2)
            else:
                speed = 0

            prev_positions[obj_id] = (center_x, center_y, time.time())

            # Drawing logic
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f'ID:{obj_id} {speed:.1f}km/h', (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            if obj_id in speed_log:
                cv2.putText(frame, f'MAX:{speed_log[obj_id]}', (x1, y2+20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        # JPEG Quality Reduction (60)
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    
    cap.release()
    cv2.destroyAllWindows()
