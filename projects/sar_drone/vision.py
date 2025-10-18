import cv2
import numpy as np
from typing import Optional, Tuple

class ColorTargetDetector:
    """
    זיהוי יעד לפי צבע (אדום כברירת מחדל) באמצעות HSV ובלובים.
    """

    def __init__(self,
                 hsv_low_1=(0, 120, 100),   hsv_high_1=(10, 255, 255),
                 hsv_low_2=(170, 120, 100), hsv_high_2=(180, 255, 255),
                 min_area=1200):
        self.hsv_low_1  = np.array(hsv_low_1,  dtype=np.uint8)
        self.hsv_high_1 = np.array(hsv_high_1, dtype=np.uint8)
        self.hsv_low_2  = np.array(hsv_low_2,  dtype=np.uint8)
        self.hsv_high_2 = np.array(hsv_high_2, dtype=np.uint8)
        self.min_area   = min_area

    def detect(self, frame_bgr) -> Optional[Tuple[int,int,int,int]]:
        """
        מחזיר bbox (x,y,w,h) אם נמצא יעד, אחרת None.
        """
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, self.hsv_low_1, self.hsv_high_1)
        mask2 = cv2.inRange(hsv, self.hsv_low_2, self.hsv_high_2)
        mask  = cv2.bitwise_or(mask1, mask2)
        mask  = cv2.medianBlur(mask, 5)

        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts:
            return None
        c = max(cnts, key=cv2.contourArea)
        if cv2.contourArea(c) < self.min_area:
            return None
        x, y, w, h = cv2.boundingRect(c)
        return (x, y, w, h)
