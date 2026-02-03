"""Детектор со следами движения"""

import cv2
import numpy as np
import time
from typing import List, Tuple, Dict
from collections import deque
from .base import ObjectDetector
from .motion import MotionDetector
from models.detection import DetectionResult
from models.config import GlobalConfig, TrailsConfig
from models.enums import ObjectCategory
from utils.logger import logger


class TrailsDetector(ObjectDetector):
    """Детектор со следами движения"""

    def __init__(self, config: GlobalConfig):
        super().__init__(config)
        cfg = config.trails
        self.config_obj: TrailsConfig = cfg
        self.trail_history: Dict[int, deque] = {}
        self.trail_colors: Dict[int, Tuple[int, int, int]] = {}
        self.color_index = 0
        self.trail_colors_list = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (255, 0, 255), (0, 255, 255),
            (255, 128, 0), (128, 255, 0), (0, 128, 255)
        ]

    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        # Используем детектор движения как базовый
        detector = MotionDetector(self.config)
        results = detector.detect(frame)

        # Обновляем историю следов
        current_time = time.time()

        for result in results:
            obj_id = result.id

            if obj_id not in self.trail_history:
                self.trail_history[obj_id] = deque(maxlen=self.config_obj.trail_length)
                self.trail_colors[obj_id] = self.trail_colors_list[
                    self.color_index % len(self.trail_colors_list)
                    ]
                self.color_index += 1

            # Добавляем текущую позицию
            self.trail_history[obj_id].append({
                'center': result.center,
                'time': current_time,
                'bbox': result.bbox
            })

        # Удаляем старые треки
        to_remove = []
        for obj_id, trail in self.trail_history.items():
            if trail and current_time - trail[-1]['time'] > 10.0:  # 10 секунд без движения
                to_remove.append(obj_id)

        for obj_id in to_remove:
            del self.trail_history[obj_id]
            if obj_id in self.trail_colors:
                del self.trail_colors[obj_id]

        return results

    def _get_config(self):
        return self.config_obj