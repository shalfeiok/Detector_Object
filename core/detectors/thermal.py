"""Тепловизионный детектор"""

import cv2
import numpy as np
from typing import List
from .base import ObjectDetector
from models.detection import DetectionResult
from models.config import GlobalConfig, ThermalConfig
from models.enums import ObjectCategory
from utils.logger import logger


class ThermalDetector(ObjectDetector):
    """Детектор с тепловизионной симуляцией"""

    def __init__(self, config: GlobalConfig):
        super().__init__(config)
        self.config_obj: ThermalConfig = config.thermal

    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        cfg = self.config_obj

        # Конвертация в тепловизионную карту
        thermal_frame = self._convert_to_thermal(frame, cfg)

        # Детекция горячих областей
        gray = cv2.cvtColor(thermal_frame, cv2.COLOR_BGR2GRAY)

        # Адаптивный порог для выделения "горячих" зон
        _, hot_mask = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # Выделение холодных зон (если нужно)
        if cfg.highlight_cold:
            _, cold_mask = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
            cold_mask = cv2.bitwise_and(cold_mask, cv2.bitwise_not(hot_mask))

        # Поиск контуров горячих зон
        contours, _ = cv2.findContours(hot_mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        results = []
        for contour in contours:
            area = cv2.contourArea(contour)

            if area < 100:  # Слишком маленькие горячие точки
                continue

            x, y, w, h = cv2.boundingRect(contour)

            # Анализ температуры в области
            roi = gray[y:y + h, x:x + w]
            if roi.size > 0:
                avg_temp = np.mean(roi)

                # Классификация по "температуре"
                if avg_temp < 100:
                    category = ObjectCategory.SMALL  # "Холодные" объекты
                elif avg_temp < 180:
                    category = ObjectCategory.MEDIUM
                else:
                    category = ObjectCategory.LARGE  # "Горячие" объекты
            else:
                category = ObjectCategory.UNKNOWN

            center_x = x + w // 2
            center_y = y + h // 2

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

    def _convert_to_thermal(self, frame: np.ndarray, cfg: ThermalConfig) -> np.ndarray:
        """Конвертация в тепловизионное изображение"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Нормализация
        normalized = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

        # Применение цветовой карты
        if cfg.color_map == "jet":
            thermal = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
        elif cfg.color_map == "hot":
            thermal = cv2.applyColorMap(normalized, cv2.COLORMAP_HOT)
        elif cfg.color_map == "cool":
            thermal = cv2.applyColorMap(normalized, cv2.COLORMAP_COOL)
        elif cfg.color_map == "autumn":
            thermal = cv2.applyColorMap(normalized, cv2.COLORMAP_AUTUMN)
        else:
            thermal = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)

        # Регулировка чувствительности
        sensitivity = self._apply_sensitivity(1.0, 0.5, 2.0)
        if sensitivity != 1.0:
            hsv = cv2.cvtColor(thermal, cv2.COLOR_BGR2HSV)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sensitivity, 0, 255)
            thermal = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        return thermal

    def _get_config(self):
        return self.config_obj