"""Многоуровневый детектор"""

import cv2
import numpy as np
from typing import List, Tuple
from .base import ObjectDetector
from models.detection import DetectionResult
from models.config import GlobalConfig, MultiScaleConfig
from models.enums import ObjectCategory
from utils.logger import logger


class MultiScaleDetector(ObjectDetector):
    """Многоуровневый детектор"""

    def __init__(self, config: GlobalConfig):
        super().__init__(config)
        self.config_obj: MultiScaleConfig = config.multiscale

    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        cfg = self.config_obj

        objects_all_scales = []

        for scale_idx, scale in enumerate(cfg.scales):
            if scale_idx >= len(cfg.scale_weights):
                break

            weight = cfg.scale_weights[scale_idx]

            # Масштабирование изображения
            if scale != 1.0:
                width = int(frame.shape[1] * scale)
                height = int(frame.shape[0] * scale)
                scaled = cv2.resize(frame, (width, height))
            else:
                scaled = frame

            # Детекция на текущем масштабе (используем адаптивный фон)
            from .adaptive import AdaptiveDetector
            detector = AdaptiveDetector(self.config)
            objects = detector.detect(scaled)

            # Масштабирование координат обратно
            for obj in objects:
                if scale != 1.0:
                    x, y, w, h = obj.bbox
                    obj.bbox = (int(x / scale), int(y / scale), int(w / scale), int(h / scale))
                    cx, cy = obj.center
                    obj.center = (int(cx / scale), int(cy / scale))
                    if obj.contour is not None:
                        obj.contour = (obj.contour / scale).astype(np.int32)

                # Применение веса масштаба
                obj.confidence *= weight

            objects_all_scales.extend(objects)

        # Объединение дубликатов
        return self._merge_objects(objects_all_scales, cfg.merge_threshold)

    def _merge_objects(self, objects: List[DetectionResult], threshold: float) -> List[DetectionResult]:
        """Объединение перекрывающихся объектов"""
        if not objects:
            return []

        # Сортировка по уверенности
        objects.sort(key=lambda x: x.confidence, reverse=True)

        merged = []
        used = [False] * len(objects)

        for i, obj1 in enumerate(objects):
            if used[i]:
                continue

            # Создаем объединенный объект
            merged_obj = obj1
            merge_count = 1

            # Ищем перекрывающиеся объекты
            for j, obj2 in enumerate(objects[i + 1:], i + 1):
                if used[j]:
                    continue

                # Проверка перекрытия
                if self._check_overlap(obj1, obj2) > threshold:
                    # Объединение
                    merged_obj = self._combine_objects(merged_obj, obj2)
                    used[j] = True
                    merge_count += 1

            # Усреднение уверенности
            merged_obj.confidence /= merge_count
            merged.append(merged_obj)
            used[i] = True

        return merged

    def _check_overlap(self, obj1: DetectionResult, obj2: DetectionResult) -> float:
        """Проверка перекрытия двух объектов"""
        x1, y1, w1, h1 = obj1.bbox
        x2, y2, w2, h2 = obj2.bbox

        # Вычисление площади пересечения
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        intersection = (x_right - x_left) * (y_bottom - y_top)
        area1 = w1 * h1
        area2 = w2 * h2

        # Коэффициент перекрытия (IoU)
        union = area1 + area2 - intersection
        return intersection / union if union > 0 else 0.0

    def _combine_objects(self, obj1: DetectionResult, obj2: DetectionResult) -> DetectionResult:
        """Объединение двух объектов"""
        x1, y1, w1, h1 = obj1.bbox
        x2, y2, w2, h2 = obj2.bbox

        # Новый ограничивающий прямоугольник
        x_new = min(x1, x2)
        y_new = min(y1, y2)
        x_end = max(x1 + w1, x2 + w2)
        y_end = max(y1 + h1, y2 + h2)
        w_new = x_end - x_new
        h_new = y_end - y_new

        # Новый центр
        center_x = x_new + w_new // 2
        center_y = y_new + h_new // 2

        # Объединение контуров (пока просто берем первый)
        contour_new = obj1.contour

        # Выбор большего типа
        area1 = w1 * h1
        area2 = w2 * h2
        category = obj1.category if area1 >= area2 else obj2.category

        merged_obj = DetectionResult(
            bbox=(x_new, y_new, w_new, h_new),
            center=(center_x, center_y),
            area=w_new * h_new,
            contour=contour_new,
            category=category,
            confidence=(obj1.confidence + obj2.confidence) / 2
        )

        return merged_obj

    def _get_config(self):
        return self.config_obj