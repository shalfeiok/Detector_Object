"""Рендерер оверлея"""

import cv2
import numpy as np
from typing import List, Tuple
from models.detection import DetectionResult
from models.config import GlobalConfig
from utils.logger import logger


class OverlayRenderer:
    """Рендерер оверлея"""

    def __init__(self, config: GlobalConfig):
        self.config = config
        self._heatmap = None
        self._heatmap_decay = 0.95

    def render(self, frame: np.ndarray,
               detections: List[DetectionResult]) -> np.ndarray:
        """Рендеринг оверлея с детекциями"""
        if frame is None:
            return np.zeros((100, 100, 3), dtype=np.uint8)

        overlay = frame.copy()

        # Инициализация тепловой карты
        if self.config.display.show_heatmap and self._heatmap is None:
            self._heatmap = np.zeros(frame.shape[:2], dtype=np.float32)

        # Отрисовка объектов
        for detection in detections:
            overlay = self._draw_detection(overlay, detection)

        # Наложение тепловой карты
        if self.config.display.show_heatmap:
            overlay = self._apply_heatmap(overlay)

        # Смешивание с оригиналом
        if self.config.display.show_original:
            overlay = cv2.addWeighted(frame, 0.3, overlay, 0.7, 0)

        return overlay

    def _draw_detection(self, overlay: np.ndarray,
                        detection: DetectionResult) -> np.ndarray:
        """Отрисовка одного детекта"""
        color = self.config.colors.get(
            detection.category.value,
            (0, 255, 0)  # Зеленый по умолчанию
        )

        # Ограничивающий прямоугольник
        x, y, w, h = detection.bbox
        cv2.rectangle(overlay, (x, y), (x + w, y + h), color, 2)

        # Центральный маркер
        cx, cy = detection.center
        cv2.circle(overlay, (cx, cy), 5, color, -1)
        cv2.circle(overlay, (cx, cy), 7, (255, 255, 255), 1)

        # Метка
        label = f"{detection.category.value} ({detection.confidence:.1f})"
        if detection.velocity > 0:
            label += f" {detection.velocity:.1f}px/s"

        self._draw_text_with_background(
            overlay, label, (cx + 10, cy - 10), color
        )

        # Контур
        if detection.contour is not None:
            cv2.drawContours(overlay, [detection.contour], -1, color, 1)

        # Обновление тепловой карты
        if self.config.display.show_heatmap:
            self._update_heatmap(cx, cy, overlay.shape)

        return overlay

    def _draw_text_with_background(self, image: np.ndarray, text: str,
                                   position: Tuple[int, int],
                                   text_color: Tuple[int, int, int]) -> None:
        """Рисование текста с фоном"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.5
        thickness = 2

        text_size = cv2.getTextSize(text, font, scale, thickness)[0]
        text_width, text_height = text_size

        x, y = position

        # Фон
        bg_rect = (
            x - 5, y - text_height - 5,
            x + text_width + 10, y + 5
        )
        cv2.rectangle(image,
                      (bg_rect[0], bg_rect[1]),
                      (bg_rect[2], bg_rect[3]),
                      (0, 0, 0), -1)

        # Текст
        cv2.putText(image, text, (x, y),
                    font, scale, text_color, thickness)

    def _update_heatmap(self, x: int, y: int, shape: Tuple[int, int, int]) -> None:
        """Обновление тепловой карты"""
        if self._heatmap is None:
            return

        # Проверяем границы
        if x < 0 or y < 0 or x >= shape[1] or y >= shape[0]:
            return

        # Добавление тепла в точку
        radius = 10
        y_min = max(0, y - radius)
        y_max = min(self._heatmap.shape[0], y + radius)
        x_min = max(0, x - radius)
        x_max = min(self._heatmap.shape[1], x + radius)

        if y_min < y_max and x_min < x_max:
            self._heatmap[y_min:y_max, x_min:x_max] += 1.0

        # Затухание
        self._heatmap *= self._heatmap_decay

    def _apply_heatmap(self, image: np.ndarray) -> np.ndarray:
        """Применение тепловой карты к изображению"""
        if self._heatmap is None:
            return image

        # Нормализация
        heatmap_norm = cv2.normalize(
            self._heatmap, None, 0, 255, cv2.NORM_MINMAX
        ).astype(np.uint8)

        # Цветовая карта
        heatmap_color = cv2.applyColorMap(heatmap_norm, cv2.COLORMAP_JET)

        # Наложение
        return cv2.addWeighted(image, 0.7, heatmap_color, 0.3, 0)