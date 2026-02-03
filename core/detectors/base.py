"""Базовый класс детектора"""

import cv2
import numpy as np
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional, Callable, Any
from collections import deque, defaultdict
from models.detection import DetectionResult
from models.config import GlobalConfig
from models.enums import ObjectCategory
from utils.logger import logger


class ObjectDetector(ABC):
    """Абстрактный детектор объектов"""

    def __init__(self, config: GlobalConfig):
        self.config = config
        self._tracked_objects: Dict[int, DetectionResult] = {}
        self._next_id = 0
        self._observers = []

    def attach(self, observer: Callable) -> None:
        """Добавление наблюдателя"""
        self._observers.append(observer)

    def detach(self, observer: Callable) -> None:
        """Удаление наблюдателя"""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event: str, data: Any = None) -> None:
        """Уведомление наблюдателей"""
        for observer in self._observers:
            try:
                observer(event, data)
            except Exception as e:
                logger.error(f"Observer error: {e}")

    @abstractmethod
    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        """Обнаружение объектов в кадре"""
        pass

    def process(self, frame: np.ndarray) -> List[DetectionResult]:
        """Обработка кадра и детекция объектов"""
        if frame is None:
            return []

        try:
            results = self.detect(frame)
            self._update_tracking(results)
            self.notify('objects_detected', results)
            return results

        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []

    def _update_tracking(self, new_results: List[DetectionResult]) -> None:
        """Обновление трекинга объектов"""
        current_ids = {r.id for r in new_results}

        # Удаление потерянных объектов
        lost_ids = set(self._tracked_objects.keys()) - current_ids
        for obj_id in lost_ids:
            del self._tracked_objects[obj_id]

        # Обновление существующих и добавление новых
        for result in new_results:
            if result.id not in self._tracked_objects:
                result.id = self._generate_id()
            self._tracked_objects[result.id] = result

    def _generate_id(self) -> int:
        """Генерация уникального ID"""
        self._next_id += 1
        return self._next_id

    def _classify_object(self, width: int, height: int, area: int,
                         velocity: float = 0.0) -> ObjectCategory:
        """Классификация объекта"""
        if area < 100:
            return ObjectCategory.SMALL
        elif area < 500:
            if velocity > 10.0:
                return ObjectCategory.BIRD
            return ObjectCategory.MEDIUM
        elif area < 2000:
            return ObjectCategory.MEDIUM
        else:
            return ObjectCategory.LARGE

    def _apply_sensitivity(self, value: float, min_val: float, max_val: float) -> float:
        """Применение параметра чувствительности к значению"""
        cfg = self._get_config()
        sensitivity = getattr(cfg, 'sensitivity', 1.0)

        # Преобразуем чувствительность (0.1-3.0) в коэффициент (0.5-2.0)
        coeff = 0.5 + (sensitivity - 0.1) * 0.6

        adjusted = value * coeff
        return max(min_val, min(max_val, adjusted))

    def _get_config(self):
        """Получение конфигурации для текущего детектора"""
        raise NotImplementedError