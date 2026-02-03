"""Сбор и расчет статистики"""

import time
from typing import List, Dict
from collections import deque, defaultdict
from models.detection import DetectionResult


class TrackingStatistics:
    """Сбор и расчет статистики"""

    def __init__(self):
        self.total_detections = 0
        self.category_counts = defaultdict(int)
        self.processing_times = deque(maxlen=100)
        self.start_time = time.time()
        self._last_update_time = time.time()
        self._detections_per_second = 0

    def update(self, detections: List[DetectionResult], fps: float) -> Dict:
        """Обновление статистики"""
        current_time = time.time()
        time_diff = current_time - self._last_update_time

        self.total_detections += len(detections)

        # Обновление счетчиков категорий
        for detection in detections:
            self.category_counts[detection.category] += 1

        # Расчет детекций в секунду
        if time_diff >= 1.0:
            self._detections_per_second = len(detections) / time_diff
            self._last_update_time = current_time

        stats = {
            'total': self.total_detections,
            'fps': fps,
            'dps': self._detections_per_second,
            'categories': {
                cat.value: count
                for cat, count in self.category_counts.items()
            },
            'current': len(detections),
            'uptime': current_time - self.start_time
        }

        return stats

    def reset(self):
        """Сброс статистики"""
        self.total_detections = 0
        self.category_counts.clear()
        self.processing_times.clear()
        self.start_time = time.time()
        self._last_update_time = time.time()
        self._detections_per_second = 0