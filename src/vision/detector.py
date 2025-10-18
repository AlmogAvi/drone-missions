import cv2
import numpy as np

# Try importing YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False


# ============================================================
# 🟢 COLOR DETECTOR (Standard)
# ============================================================
class ColorTargetDetector:
    COLOR_RANGES = {
        "red": ([0, 120, 70], [10, 255, 255]),
        "red2": ([170, 120, 70], [180, 255, 255]),
        "yellow": ([20, 100, 100], [35, 255, 255]),
        "green": ([40, 40, 40], [80, 255, 255]),
        "blue": ([90, 50, 50], [130, 255, 255]),
        "orange": ([10, 100, 100], [25, 255, 255]),
    }

    def __init__(self, min_area=400):
        self.min_area = min_area

    def detect(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        detections = []

        for color, (lower, upper) in self.COLOR_RANGES.items():
            lower = np.array(lower, np.uint8)
            upper = np.array(upper, np.uint8)
            mask = cv2.inRange(hsv, lower, upper)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in contours:
                if cv2.contourArea(c) > self.min_area:
                    x, y, w, h = cv2.boundingRect(c)
                    detections.append({"color": color, "bbox": (x, y, w, h)})

        if not detections:
            return None

        det = max(detections, key=lambda d: d["bbox"][2] * d["bbox"][3])
        x, y, w, h = det["bbox"]
        color = det["color"]
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
        cv2.putText(frame, color, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        return det["bbox"]


# ============================================================
# 🟡 QUIET COLOR DETECTOR (Enhanced)
# ============================================================
class QuietColorDetector:
    """
    Improved color detector that only prints when detection changes.
    Tracks previous detection to reduce console spam.
    """

    COLOR_RANGES = ColorTargetDetector.COLOR_RANGES

    def __init__(self, min_area=400, sensitivity_px=10):
        self.min_area = min_area
        self.prev_bbox = None
        self.prev_color = None
        self.sensitivity_px = sensitivity_px

    def detect(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        detections = []

        for color, (lower, upper) in self.COLOR_RANGES.items():
            lower = np.array(lower, np.uint8)
            upper = np.array(upper, np.uint8)
            mask = cv2.inRange(hsv, lower, upper)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in contours:
                if cv2.contourArea(c) > self.min_area:
                    x, y, w, h = cv2.boundingRect(c)
                    detections.append({"color": color, "bbox": (x, y, w, h)})

        if not detections:
            self._handle_no_detection()
            return None

        det = max(detections, key=lambda d: d["bbox"][2] * d["bbox"][3])
        bbox = det["bbox"]
        color = det["color"]

        # Draw
        x, y, w, h = bbox
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
        cv2.putText(frame, color, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        if self._is_new_detection(color, bbox):
            print(f"[DETECT] New {color} object at {bbox}")
            self.prev_bbox = bbox
            self.prev_color = color

        return bbox

    def _is_new_detection(self, color, bbox):
        """Check if detection changed significantly."""
        if self.prev_bbox is None or color != self.prev_color:
            return True

        px, py, pw, ph = self.prev_bbox
        x, y, w, h = bbox
        dx, dy, dw, dh = abs(x - px), abs(y - py), abs(w - pw), abs(h - ph)
        return (dx + dy + dw + dh) > self.sensitivity_px

    def _handle_no_detection(self):
        if self.prev_bbox is not None:
            print("[DETECT] Lost object")
        self.prev_bbox = None
        self.prev_color = None


# ============================================================
# 🔵 YOLO DETECTOR
# ============================================================
class YOLODetector:
    def __init__(self, model_path="yolov8n.pt", conf=0.4):
        if not YOLO_AVAILABLE:
            raise RuntimeError("Ultralytics YOLO not installed. Run: pip install ultralytics")
        self.model = YOLO(model_path)
        self.conf = conf

    def detect(self, frame):
        results = self.model.predict(frame, conf=self.conf, verbose=False)
        if not results or not results[0].boxes:
            return None
        box = results[0].boxes[0]
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        label = self.model.names[int(box.cls[0])]
        conf = float(box.conf[0])
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        return (x1, y1, x2 - x1, y2 - y1)


# ============================================================
# ⚙️ DETECTOR FACTORY
# ============================================================
def create_detector(mode="color"):
    """
    Returns detector instance by mode:
      - "color"  → basic HSV detection
      - "quiet"  → quiet mode (prints only when changes)
      - "yolo"   → YOLOv8 detector
    """
    if mode == "yolo":
        return YOLODetector()
    elif mode == "quiet":
        return QuietColorDetector()
    return ColorTargetDetector()
