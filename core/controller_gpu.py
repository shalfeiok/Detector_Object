"""Контроллер с поддержкой GPU"""

import threading
import time
import queue
from typing import Optional
from .capture import WindowCapture
from .factory import DetectorFactory
from .renderer_gpu import AsyncRenderer, RendererFactory
from .statistics import TrackingStatistics
from models.config import GlobalConfig
from models.enums import TrackingMethod
from utils.logger import logger
from utils.gpu_check import gpu_manager


class GPUTrackingController:
    """Контроллер с поддержкой GPU"""

    def __init__(self):
        self.config = GlobalConfig()
        self._is_running = False
        self._thread = None

        # Определение оптимального бэкенда
        self._detect_optimal_backend()

        # Инициализация компонентов
        self.capture = WindowCapture(self.config)
        self.detector = DetectorFactory.create(self.config.method, self.config)
        self.renderer = AsyncRenderer(self.config)

        # Очереди для межпоточного обмена
        self._overlay_queue = queue.Queue(maxsize=3)
        self._stats_queue = queue.Queue(maxsize=10)

        # Статистика
        self._stats = TrackingStatistics()
        self._render_stats = {
            'render_time': 0,
            'fps': 0,
            'frame_count': 0,
            'start_time': time.time()
        }

    def _detect_optimal_backend(self):
        """Определение оптимального бэкенда"""
        if not self.config.render.backend:
            optimal = gpu_manager.get_optimal_backend()
            self.config.render.backend = optimal
            logger.info(f"Auto-selected render backend: {optimal.value}")

    def start(self) -> None:
        """Запуск отслеживания"""
        if self._is_running:
            return

        self._is_running = True
        self.capture.start()
        self.renderer.start()

        self._thread = threading.Thread(
            target=self._tracking_loop,
            daemon=True,
            name="GPUTrackingLoop"
        )
        self._thread.start()

        logger.info("GPU tracking started")

    def stop(self) -> None:
        """Остановка отслеживания"""
        self._is_running = False
        self.capture.stop()
        self.renderer.stop()

        if self._thread:
            self._thread.join(timeout=2)

        logger.info("GPU tracking stopped")

    def switch_method(self, method: TrackingMethod) -> None:
        """Переключение метода детекции"""
        self.config.method = method
        self.detector = DetectorFactory.create(method, self.config)

        logger.info(f"Switched to method: {method.value}")

    def switch_backend(self, backend) -> None:
        """Переключение бэкенда рендеринга"""
        self.config.render.backend = backend
        self.renderer.stop()
        self.renderer = AsyncRenderer(self.config)
        self.renderer.start()

        logger.info(f"Switched to render backend: {backend.value}")

    def update_config(self, config: GlobalConfig) -> None:
        """Обновление конфигурации"""
        old_backend = self.config.render.backend
        self.config = config

        # Пересоздаем детектор
        self.detector = DetectorFactory.create(config.method, config)

        # Пересоздаем рендерер если изменился бэкенд
        if old_backend != config.render.backend:
            self.renderer.stop()
            self.renderer = AsyncRenderer(config)
            self.renderer.start()
        else:
            # Обновляем конфигурацию существующего рендерера
            self.renderer.renderer = RendererFactory.create(config)

        logger.info("Configuration updated")

    def _tracking_loop(self) -> None:
        """Основной цикл обработки"""
        last_stat_time = time.time()
        last_render_stat_time = time.time()

        while self._is_running:
            try:
                # Получение кадра
                frame = self.capture.get_frame()
                if frame is None:
                    time.sleep(0.01)
                    continue

                # Детекция
                detections = self.detector.process(frame)

                # Асинхронный рендеринг
                task_id = self.renderer.submit(frame, detections)

                if task_id >= 0:
                    # Получение результата рендеринга
                    result = self.renderer.get_result(timeout=0.01)
                    if result:
                        # Отправка в UI
                        if not self._overlay_queue.full():
                            try:
                                self._overlay_queue.put_nowait(result.overlay)
                            except queue.Full:
                                pass

                        # Статистика рендеринга
                        self._update_render_stats(result.render_time)

                # Обновление статистики
                current_time = time.time()
                if current_time - last_stat_time >= 1.0:
                    stats = self._stats.update(detections, self.capture.fps)
                    stats['render_fps'] = self._render_stats['fps']
                    stats['render_time_ms'] = self._render_stats['render_time'] * 1000

                    # Информация о GPU
                    if gpu_manager.has_gpu:
                        stats['gpu_backend'] = self.config.render.backend.value
                        stats['gpu_device'] = gpu_manager.capabilities.gpu_name

                    if not self._stats_queue.full():
                        try:
                            self._stats_queue.put_nowait(stats)
                        except queue.Full:
                            pass

                    last_stat_time = current_time

                # Обновление статистики рендеринга
                if current_time - last_render_stat_time >= 2.0:
                    self._render_stats['fps'] = self._render_stats['frame_count'] / 2.0
                    self._render_stats['frame_count'] = 0
                    last_render_stat_time = current_time

                # Задержка для контроля FPS
                time.sleep(self.config.update_interval)

            except Exception as e:
                logger.error(f"Tracking loop error: {e}")
                time.sleep(0.1)

    def _update_render_stats(self, render_time: float):
        """Обновление статистики рендеринга"""
        self._render_stats['render_time'] = (
                self._render_stats['render_time'] * 0.9 + render_time * 0.1
        )
        self._render_stats['frame_count'] += 1

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

    def get_gpu_info(self) -> dict:
        """Получение информации о GPU"""
        caps = gpu_manager.get_capabilities()
        return {
            'has_gpu': caps.gpu_available,
            'gpu_name': caps.gpu_name,
            'gpu_memory_gb': caps.gpu_memory / 1024 ** 3 if caps.gpu_memory else 0,
            'cuda_available': caps.cuda_available,
            'opencl_available': caps.opencl_available,
            'available_backends': [b.value for b in caps.backends],
            'current_backend': self.config.render.backend.value
        }