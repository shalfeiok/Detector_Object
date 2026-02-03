"""Виджет отображения видео"""

import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import queue
from .widgets import BaseWidget
from utils.logger import logger


class VideoDisplay(BaseWidget):
    """Виджет отображения видео"""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.canvas = tk.Canvas(self, bg='black')
        self.canvas.pack(fill='both', expand=True)

        self._current_image = None
        self._photo_image = None

        # Запуск обновления
        self._update_display()

    def _update_display(self) -> None:
        """Обновление отображения"""
        try:
            # Получение оверлея из очереди
            overlay = None
            try:
                overlay = self.controller.overlay_queue.get_nowait()
            except queue.Empty:
                pass

            if overlay is not None:
                # Конвертация для Tkinter
                overlay_rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(overlay_rgb)

                # Масштабирование
                width = self.canvas.winfo_width()
                height = self.canvas.winfo_height()

                if width > 1 and height > 1:
                    image.thumbnail((width, height), Image.Resampling.LANCZOS)

                # Отображение
                self._photo_image = ImageTk.PhotoImage(image)
                self.canvas.delete('all')
                self.canvas.create_image(
                    width // 2, height // 2,
                    image=self._photo_image,
                    anchor='center'
                )

        except Exception as e:
            logger.error(f"Display update error: {e}")

        # Следующее обновление
        self.after(33, self._update_display)  # ~30 FPS