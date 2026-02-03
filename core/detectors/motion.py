"""Детектор движения"""

import cv2
import numpy as np
import time
from typing import List, Tuple
from collections import deque
from .base import ObjectDetector
from models.detection import DetectionResult
from models.config import GlobalConfig, MotionConfig
from models.enums import ObjectCategory
from utils.logger import logger


class MotionDetector(ObjectDetector):
    """Детектор движения"""

    def __init__(self, config: GlobalConfig):
        super().__init__(config)
        cfg = config.motion
        self.config_obj: MotionConfig = cfg
        self._frame_buffer = deque(maxlen=cfg.temporal_buffer_size)
        self._last_positions: Dict[int, Tuple[float, float]] = {}
        self._last_times: Dict[int, float] = {}

    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        cfg = self.config_obj

        # Подготовка кадра
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        self._frame_buffer.append(gray)

        if len(self._frame_buffer) < 2:
            return []

        # Вычисление разности кадров
        diff = cv2.absdiff(self._frame_buffer[-2], self._frame_buffer[-1])

        # Применение чувствительности к минимальному изменению пикселя
        min_pixel_change = self._apply_sensitivity(cfg.min_pixel_change, 1, 50)
        _, motion_mask = cv2.threshold(diff, int(min_pixel_change), 255, cv2.THRESH_BINARY)

        # Улучшение маски
        kernel = np.ones((5, 5), np.uint8)
        motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_CLOSE, kernel)

        # Детекция контуров движения
        contours, _ = cv2.findContours(motion_mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        results = []
        current_time = time.time()

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 50:  # Минимальная площадь
                continue

            x, y, w, h = cv2.boundingRect(contour)
            center_x = x + w // 2
            center_y = y + h // 2

            # Расчет скорости
            velocity, direction = self._calculate_motion(
                center_x, center_y, current_time
            )

            category = self._classify_object(w, h, area, velocity)
            confidence = 0.7 if velocity > cfg.velocity_threshold else 0.3

            result = DetectionResult(
                bbox=(x, y, w, h),
                center=(center_x, center_y),
                area=area,
                contour=contour,
                category=category,
                confidence=confidence,
                velocity=velocity,
                direction=direction
            )
            results.append(result)

            # Обновление истории
            self._last_positions[result.id] = (center_x, center_y)
            self._last_times[result.id] = current_time

        return results

    def _calculate_motion(self, x: int, y: int, timestamp: float) -> Tuple[float, float]:
        """Расчет скорости и направления"""
        # Простая реализация
        return 0.0, 0.0

    def _get_config(self):
        return self.config_obj