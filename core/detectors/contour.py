"""Контурный детектор"""

import cv2
import numpy as np
from typing import List
from .base import ObjectDetector
from models.detection import DetectionResult
from models.config import GlobalConfig, ContourConfig
from models.enums import TrackingMethod, ObjectCategory
from utils.logger import logger


class ContourDetector(ObjectDetector):
    """Контурный детектор"""

    def __init__(self, config: GlobalConfig):
        super().__init__(config)
        self.config_obj: ContourConfig = config.contour

    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        cfg = self.config_obj

        # Препроцессинг
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if cfg.blur_size > 0:
            kernel_size = cfg.blur_size if cfg.blur_size % 2 == 1 else cfg.blur_size + 1
            gray = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)

        # Применение чувствительности к порогу
        threshold = self._apply_sensitivity(cfg.threshold, 1, 255)

        # Бинаризация
        _, binary = cv2.threshold(gray, int(threshold), 255, cv2.THRESH_BINARY)

        # Морфологические операции
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        # Детекция контуров
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        results = []
        for contour in contours:
            area = cv2.contourArea(contour)

            # Применение чувствительности к минимальной площади
            min_area = self._apply_sensitivity(cfg.min_area, 1, 1000)

            # Фильтрация по площади
            if not (min_area < area < cfg.max_area):
                continue

            # Ограничивающий прямоугольник
            x, y, w, h = cv2.boundingRect(contour)

            # Фильтрация по соотношению сторон
            if h == 0:
                continue
            aspect_ratio = w / h
            if not (cfg.aspect_ratio_min < aspect_ratio < cfg.aspect_ratio_max):
                continue

            # Фильтрация по сплошности
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            if hull_area == 0:
                continue
            solidity = area / hull_area
            if solidity < cfg.solidity_threshold:
                continue

            # Создание результата
            center_x = x + w // 2
            center_y = y + h // 2

            category = self._classify_object(w, h, area)
            confidence = min(1.0, area / 1000.0)

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