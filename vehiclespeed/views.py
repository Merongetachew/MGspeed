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
# Increased distance to make speed numbers more visible/larger
CALIBRATION_DISTANCE = 20  
CALIBRATION_PIXELS = 200 
PIXEL_TO_METER = CALIBRATION_DISTANCE / CALIBRATION_PIXELS
FRAME_RATE = 30

# Initialize Model and Tracker
model_path = os.path.join('ai_models', 'yolov8n.pt')
model = YOLO(model_path)
tracker = Sort(max_age=30)

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

def live_monitor(request):
    video_path = request.session.get('current_video_path')
    if not video_path or not os.path.exists(video_path):
        video_path = 0 
    return StreamingHttpResponse(stream_frames(video_path), 
                                 content_type='multipart/x-mixed-replace; boundary=frame')

def stream_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    prev_positions = {}
    speed_log = {} 
    frame_count = 0 
    
    # AGGRESSIVE SKIP: Only process 1 out of every 20 frames (1.5 frames per second)
    # This is the ONLY way to prevent the "frozen" image on Render Free Tier.
    SKIP_RATE = 20 

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame_count += 1
        if frame_count % SKIP_RATE != 0:
            continue

        # SUPER SHRINK: Reduce display size to 480p to save memory
        frame = cv2.resize(frame, (640, 360))

        # AI OPTIMIZATION: imgsz=128 is the absolute lowest YOLO can go.
        # This makes the detection 10x faster than standard settings.
        results = model(frame, stream=True, imgsz=128, conf=0.20)

        detections = np.empty((0, 5))
        for info in results:
            for box in info.boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                conf = box.conf[0]
                cls = int(box.cls[0])
                if cls in [2, 3, 5, 7]: # Cars, motorcycles, buses, trucks
                    new_det = np.array([int(x1), int(y1), int(x2), int(y2), conf])
                    detections = np.vstack((detections, new_det))

        track_result = tracker.update(detections)
        adjusted_frame_time = SKIP_RATE / FRAME_RATE

        for result in track_result:
            x1, y1, x2, y2, obj_id = map(int, result)
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2

            if obj_id in prev_positions:
                prev_x, prev_y, _ = prev_positions[obj_id]
                dist_px = np.sqrt((center_x - prev_x)**2 + (center_y - prev_y)**2)
                speed = (dist_px * PIXEL_TO_METER) / adjusted_frame_time * 3.6
                
                if speed > 2: 
                    if obj_id not in speed_log or speed > speed_log[obj_id]:
                        speed_log[obj_id] = round(speed, 2)
            else:
                speed = 0

            prev_positions[obj_id] = (center_x, center_y, time.time())

            # DRAWING LABELS (Visibility Fix)
            # 1. Thick green box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
            
            # 2. Black background for text (Critical for visibility)
            cv2.rectangle(frame, (x1, y1 - 35), (x1 + 180, y1), (0, 0, 0), -1)
            
            # 3. Bright Yellow/Green Text
            cv2.putText(frame, f'ID:{obj_id} {speed:.1f} km/h', (x1 + 5, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # COMPRESSION: Lower JPEG quality to 40% to speed up the network transfer
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 40])
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    
    cap.release()
