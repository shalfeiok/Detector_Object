"""Чувствительный детектор движения"""

import cv2
import numpy as np
from typing import List
from collections import deque
from .base import ObjectDetector
from models.detection import DetectionResult
from models.config import GlobalConfig, SensitiveConfig
from models.enums import ObjectCategory
from utils.logger import logger


class SensitiveDetector(ObjectDetector):
    """Чувствительный детектор движения"""

    def __init__(self, config: GlobalConfig):
        super().__init__(config)
        cfg = config.sensitive
        self.config_obj: SensitiveConfig = cfg
        self._frame_buffer = deque(maxlen=cfg.frame_buffer_size)
        self._motion_accumulator = None

    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        cfg = self.config_obj

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Усиление контраста
        if cfg.enhancement_factor > 1.0:
            clahe = cv2.createCLAHE(clipLimit=cfg.enhancement_factor, tileGridSize=(8, 8))
            gray = clahe.apply(gray)

        # Добавление в буфер
        self._frame_buffer.append(gray)

        if len(self._frame_buffer) < 3:
            return []

        # Вычисление разности между кадрами
        diff1 = cv2.absdiff(self._frame_buffer[-1], self._frame_buffer[-2])
        diff2 = cv2.absdiff(self._frame_buffer[-2], self._frame_buffer[-3])

        # Комбинирование разностей
        combined = cv2.bitwise_and(diff1, diff2)

        # Пороговая обработка с низким порогом
        min_pixel_change = self._apply_sensitivity(cfg.min_pixel_change, 1, 20)
        _, thresh = cv2.threshold(combined, int(min_pixel_change), 255, cv2.THRESH_BINARY)

        # Накопление во времени
        if self._motion_accumulator is None:
            self._motion_accumulator = np.zeros_like(thresh, dtype=np.float32)

        self._motion_accumulator = cv2.addWeighted(
            self._motion_accumulator, cfg.noise_reduction,
            thresh.astype(np.float32), 1 - cfg.noise_reduction, 0
        )

        # Применение порога к накопленному движению
        _, accumulated_thresh = cv2.threshold(
            self._motion_accumulator.astype(np.uint8),
            cfg.accumulation_threshold * 50, 255, cv2.THRESH_BINARY
        )

        # Пространственная фильтрация
        if cfg.spatial_filter:
            kernel = np.ones((2, 2), np.uint8)
            accumulated_thresh = cv2.morphologyEx(accumulated_thresh, cv2.MORPH_CLOSE, kernel)

        # Поиск контуров
        contours, _ = cv2.findContours(accumulated_thresh, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        results = []
        for contour in contours:
            area = cv2.contourArea(contour)

            if area < 10:  # Очень маленькие объекты
                continue

            x, y, w, h = cv2.boundingRect(contour)

            # Дополнительная проверка: движение должно быть устойчивым
            if self._motion_accumulator is not None:
                roi_accumulator = self._motion_accumulator[y:y + h, x:x + w]
                if roi_accumulator.size > 0 and roi_accumulator.max() < 100:
                    continue

            center_x = x + w // 2
            center_y = y + h // 2

            category = ObjectCategory.SMALL if area < 50 else ObjectCategory.MEDIUM
            confidence = 0.5

            result = DetectionResult(
                bbox=(x, y, w, h),
                center=(center_x, center_y),
                area=area,
                contour=contour,
                category=category,
                confidence=confidence
            )
            results.append(result)

        return results

    def _get_config(self):
        return self.config_obj