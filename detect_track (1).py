from ultralytics import YOLO
import cv2
import servo_control

TARGET_LABEL = "person"
model = YOLO("yolov8n.pt")
cap   = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam")
    servo_control.cleanup()
    exit()


def rescale_frame(frame, scale: float = 0.9):
    h, w = frame.shape[:2]
    return cv2.resize(frame, (int(w * scale), int(h * scale)),
                      interpolation=cv2.INTER_AREA)


def zoom_frame(img, zoom_factor: float = 2.0):
    h, w = img.shape[:2]
    x1 = int(w / 2 - w / (2 * zoom_factor))
    y1 = int(h / 2 - h / (2 * zoom_factor))
    x2 = int(w / 2 + w / (2 * zoom_factor))
    y2 = int(h / 2 + h / (2 * zoom_factor))
    return cv2.resize(img[y1:y2, x1:x2], (w, h), interpolation=cv2.INTER_LINEAR)


print("Press 'q' to quit")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame")
            break

        frame_h, frame_w = frame.shape[:2]
        results = model(frame)

        best_box  = None
        best_conf = 0.0

        for result in results:
            for box in result.boxes:
                cls   = int(box.cls[0].item())
                label = model.names[cls]
                conf  = box.conf[0].item()

                if label != TARGET_LABEL:
                    continue
                if conf > best_conf:
                    best_conf = conf
                    best_box  = box

        if best_box is not None:
            x1, y1, x2, y2 = best_box.xyxy[0].tolist()
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2

            new_yaw, new_pitch = servo_control.move_servos(cx, cy, frame_w, frame_h)

            print(f"[{TARGET_LABEL}] conf={best_conf:.2f} | "
                  f"box=({x1:.0f},{y1:.0f})->({x2:.0f},{y2:.0f}) | "
                  f"center=({cx:.0f},{cy:.0f}) | "
                  f"servo yaw={new_yaw:.1f}° pitch={new_pitch:.1f}°")

            frame = zoom_frame(frame)

        annotated_frame = results[0].plot()
        cv2.imshow("YOLOv8 Tracking", rescale_frame(annotated_frame))

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    servo_control.cleanup()
