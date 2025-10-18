import time
import cv2
import os

def save_frame(frame, prefix="detect", out_dir="captures"):
    os.makedirs(out_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    path = os.path.join(out_dir, f"{prefix}_{ts}.jpg")
    cv2.imwrite(path, frame)
    return path
