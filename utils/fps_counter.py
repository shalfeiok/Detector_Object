"""Утилиты для подсчета FPS"""

import time
from collections import deque


class FPSCounter:
    """Счетчик FPS"""

    def __init__(self, window_size: int = 30):
        self.times = deque(maxlen=window_size)
        self.fps = 0.0

    def update(self) -> None:
        """Обновление счетчика"""
        current_time = time.time()
        self.times.append(current_time)

        if len(self.times) >= 2:
            duration = current_time - self.times[0]
            if duration > 0:
                self.fps = len(self.times) / duration