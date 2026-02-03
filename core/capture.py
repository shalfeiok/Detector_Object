"""Модуль захвата экрана/окон"""

import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import threading
import time
from typing import Optional, Tuple, List
from collections import deque
from models.config import CaptureConfig, GlobalConfig
from models.enums import CaptureSource
from utils.fps_counter import FPSCounter
from utils.logger import logger


class FrameBuffer:
    """Буфер для хранения и управления кадрами"""

    def __init__(self, max_size: int = 10):
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.RLock()
        self._current_frame = None

    def push(self, frame: np.ndarray) -> None:
        """Добавление кадра в буфер"""
        with self.lock:
            self.buffer.append(frame)
            self._current_frame = frame

    def pop(self) -> Optional[np.ndarray]:
        """Извлечение кадра из буфера"""
        with self.lock:
            return self.buffer.pop() if self.buffer else None

    def get_latest(self) -> Optional[np.ndarray]:
        """Получение последнего кадра"""
        with self.lock:
            return self._current_frame

    def clear(self) -> None:
        """Очистка буфера"""
        with self.lock:
            self.buffer.clear()
            self._current_frame = None

    @property
    def size(self) -> int:
        """Текущий размер буфера"""
        with self.lock:
            return len(self.buffer)


class WindowManager:
    """Менеджер окон для захвата"""

    @staticmethod
    def list_windows() -> List[str]:
        """Получение списка доступных окон"""
        try:
            windows = gw.getAllTitles()
            return [title for title in windows if title.strip()]
        except:
            return []

    @staticmethod
    def get_active_window() -> Optional[gw.Window]:
        """Получение активного окна"""
        try:
            return gw.getActiveWindow()
        except:
            return None

    @staticmethod
    def get_window_by_title(title: str) -> Optional[gw.Window]:
        """Получение окна по заголовку"""
        try:
            windows = gw.getWindowsWithTitle(title)
            return windows[0] if windows else None
        except:
            return None


class WindowCapture:
    """Захват окна или экрана"""

    def __init__(self, config: GlobalConfig):
        self.config = config
        self.buffer = FrameBuffer(config.capture.buffer_size)
        self._is_active = False
        self._stop_event = threading.Event()
        self._capture_thread = None
        self._fps_counter = FPSCounter()
        self._current_window = None

    def start(self) -> None:
        """Запуск захвата"""
        if self._is_active:
            return

        self._is_active = True
        self._stop_event.clear()
        self._capture_thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name="WindowCaptureThread"
        )
        self._capture_thread.start()
        logger.info("Window capture started")

    def stop(self) -> None:
        """Остановка захвата"""
        self._is_active = False
        self._stop_event.set()

        if self._capture_thread:
            self._capture_thread.join(timeout=2)

        self.buffer.clear()
        logger.info("Window capture stopped")

    def _capture_loop(self) -> None:
        """Основной цикл захвата"""
        while not self._stop_event.is_set() and self._is_active:
            try:
                frame = self._capture_frame()
                if frame is not None:
                    self.buffer.push(frame)
                    self._fps_counter.update()

            except Exception as e:
                logger.error(f"Capture error: {e}")
                time.sleep(0.1)

    def _capture_frame(self) -> Optional[np.ndarray]:
        """Захват одного кадра"""
        try:
            cfg = self.config.capture

            if cfg.source == CaptureSource.FULL_SCREEN:
                return self._capture_full_screen()
            elif cfg.source == CaptureSource.ACTIVE_WINDOW:
                return self._capture_active_window()
            elif cfg.source == CaptureSource.WINDOW_BY_TITLE:
                return self._capture_window_by_title(cfg.window_title)
            elif cfg.source == CaptureSource.REGION and cfg.region:
                return self._capture_region(cfg.region)
            else:
                return self._capture_full_screen()

        except Exception as e:
            logger.error(f"Frame capture failed: {e}")
            return None

    def _capture_full_screen(self) -> np.ndarray:
        """Захват всего экрана"""
        screenshot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    def _capture_active_window(self) -> Optional[np.ndarray]:
        """Захват активного окна"""
        window = WindowManager.get_active_window()
        if not window:
            return self._capture_full_screen()

        return self._capture_window(window)

    def _capture_window_by_title(self, title: str) -> Optional[np.ndarray]:
        """Захват окна по заголовку"""
        window = WindowManager.get_window_by_title(title)
        if not window:
            logger.warning(f"Window with title '{title}' not found")
            return None

        return self._capture_window(window)

    def _capture_region(self, region: Tuple[int, int, int, int]) -> np.ndarray:
        """Захват области экрана"""
        x, y, width, height = region
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    def _capture_window(self, window: gw.Window) -> np.ndarray:
        """Захват конкретного окна"""
        try:
            # Активируем окно для захвата
            if window != self._current_window:
                self._current_window = window
                logger.info(f"Capturing window: {window.title}")

            # Получаем координаты окна
            left, top, width, height = window.left, window.top, window.width, window.height

            # Захватываем область окна
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"Window capture failed: {e}")
            return self._capture_full_screen()

    def get_frame(self) -> Optional[np.ndarray]:
        """Получение кадра"""
        return self.buffer.get_latest()

    @property
    def fps(self) -> float:
        """Текущий FPS"""
        return self._fps_counter.fps

    @property
    def is_active(self) -> bool:
        """Статус активности"""
        return self._is_active