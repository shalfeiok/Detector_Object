"""Детектор с адаптивным фоном"""

import cv2
import numpy as np
from typing import List
from .base import ObjectDetector
from models.detection import DetectionResult
from models.config import GlobalConfig, AdaptiveConfig
from models.enums import ObjectCategory
from utils.logger import logger


class AdaptiveDetector(ObjectDetector):
    """Детектор с адаптивным фоном"""

    def __init__(self, config: GlobalConfig):
        super().__init__(config)
        cfg = config.adaptive
        self.config_obj: AdaptiveConfig = cfg
        self._background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=cfg.history_length,
            varThreshold=cfg.var_threshold,
            detectShadows=cfg.detect_shadows
        )

    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        cfg = self.config_obj

        # Вычитание фона
        fg_mask = self._background_subtractor.apply(
            frame,
            learningRate=cfg.learning_rate
        )

        # Обработка маски
        kernel = np.ones((3, 3), np.uint8)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)

        # Удаление теней
        if cfg.detect_shadows:
            fg_mask[fg_mask == 127] = 0

        # Детекция объектов
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        results = []
        for contour in contours:
            area = cv2.contourArea(contour)

            if area < 100 or area > 10000:
                continue

            x, y, w, h = cv2.boundingRect(contour)

            # Фильтрация по форме
            if min(w, h) == 0:
                continue
            if max(w, h) / min(w, h) > 4:
                continue

            center_x = x + w // 2
            center_y = y + h // 2

            # Проверка границ для безопасного извлечения ROI
            if y < 0 or y + h > frame.shape[0] or x < 0 or x + w > frame.shape[1]:
                continue

            roi = frame[y:y + h, x:x + w]
            if roi.size == 0:
                continue

            category = self._classify_object(w, h, area)
            texture_score = self._analyze_texture(roi)
            confidence = texture_score if texture_score > 0 else 0.5

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

    def _analyze_texture(self, roi: np.ndarray) -> float:
        """Анализ текстуры области"""
        if roi.size == 0:
            return 0.0

        try:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)

            edge_density = np.sum(edges > 0) / edges.size
            return min(edge_density * 3, 1.0)
        except:
            return 0.5

    def _get_config(self):
        return self.config_obj