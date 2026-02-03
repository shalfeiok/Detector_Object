"""Основной контроллер приложения"""

import threading
import time
import queue
from typing import Any
from .capture import WindowCapture
from .factory import DetectorFactory
from .renderer import OverlayRenderer
from .statistics import TrackingStatistics
from models.config import GlobalConfig
from models.enums import TrackingMethod
from utils.logger import logger


class TrackingController:
    """Основной контроллер приложения"""

    def __init__(self):
        self.config = GlobalConfig()
        self._is_running = False
        self._thread = None

        # Инициализация компонентов
        self.capture = WindowCapture(self.config)
        self.detector = DetectorFactory.create(
            self.config.method, self.config
        )
        self.renderer = OverlayRenderer(self.config)

        # Очереди для межпоточного обмена
        self._overlay_queue = queue.Queue(maxsize=2)
        self._stats_queue = queue.Queue(maxsize=10)

        # Статистика
        self._stats = TrackingStatistics()

    def start(self) -> None:
        """Запуск отслеживания"""
        if self._is_running:
            return

        self._is_running = True
        self.capture.start()

        self._thread = threading.Thread(
            target=self._tracking_loop,
            daemon=True,
            name="TrackingLoop"
        )
        self._thread.start()

        logger.info("Tracking started")

    def stop(self) -> None:
        """Остановка отслеживания"""
        self._is_running = False
        self.capture.stop()

        if self._thread:
            self._thread.join(timeout=2)

        logger.info("Tracking stopped")

    def switch_method(self, method: TrackingMethod) -> None:
        """Переключение метода детекции"""
        self.config.method = method
        self.detector = DetectorFactory.create(method, self.config)

        logger.info(f"Switched to method: {method.value}")

    def update_config(self, config: GlobalConfig) -> None:
        """Обновление конфигурации"""
        self.config = config
        self.detector = DetectorFactory.create(config.method, config)
        self.renderer = OverlayRenderer(config)

        logger.info("Configuration updated")

    def _tracking_loop(self) -> None:
        """Основной цикл обработки"""
        last_stat_time = time.time()

        while self._is_running:
            try:
                # Получение кадра
                frame = self.capture.get_frame()
                if frame is None:
                    time.sleep(0.01)
                    continue

                # Детекция
                detections = self.detector.process(frame)

                # Рендеринг
                overlay = self.renderer.render(frame, detections)

                # Отправка в UI
                if not self._overlay_queue.full():
                    try:
                        self._overlay_queue.put_nowait(overlay)
                    except queue.Full:
                        pass

                # Обновление статистики
                current_time = time.time()
                if current_time - last_stat_time >= 1.0:
                    stats = self._stats.update(detections, self.capture.fps)
                    if not self._stats_queue.full():
                        try:
                            self._stats_queue.put_nowait(stats)
                        except queue.Full:
                            pass
                    last_stat_time = current_time

                # Задержка для контроля FPS
                time.sleep(self.config.update_interval)

            except Exception as e:
                logger.error(f"Tracking loop error: {e}")
                time.sleep(0.1)

    @property
    def overlay_queue(self) -> queue.Queue:
        """Очередь оверлеев для UI"""
        return self._overlay_queue

    @property
    def stats_queue(self) -> queue.Queue:
        """Очередь статистики для UI"""
        return self._stats_queue

    @property
    def is_running(self) -> bool:
        """Статус работы"""
        return self._is_running