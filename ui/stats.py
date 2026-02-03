"""Панель статистики"""

import tkinter as tk
from tkinter import ttk
import queue
from collections import deque
from .widgets import BaseWidget
from models.enums import ObjectCategory
from utils.logger import logger


class StatisticsPanel(BaseWidget):
    """Панель статистики"""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.title_label = ttk.Label(
            self, text='Статистика', style='Title.TLabel'
        )
        self.title_label.pack(anchor='w', padx=5, pady=(5, 0))

        # Поля статистики
        self.stats_vars = {
            'fps': tk.StringVar(value='FPS: 0.0'),
            'dps': tk.StringVar(value='Объекты/сек: 0.0'),
            'detections': tk.StringVar(value='Обнаружено: 0'),
            'current': tk.StringVar(value='Сейчас: 0'),
            'small': tk.StringVar(value='Мелкие: 0'),
            'medium': tk.StringVar(value='Средние: 0'),
            'large': tk.StringVar(value='Крупные: 0'),
            'uptime': tk.StringVar(value='Время работы: 00:00')
        }

        for var in self.stats_vars.values():
            label = ttk.Label(self, textvariable=var, style='Value.TLabel')
            label.pack(anchor='w', padx=10, pady=2)

        # График активности
        self.graph_frame = ttk.Frame(self, style='Stats.TFrame')
        self.graph_frame.pack(fill='x', padx=5, pady=10)

        self.graph_canvas = tk.Canvas(
            self.graph_frame, height=80, bg='white'
        )
        self.graph_canvas.pack(fill='x', padx=2, pady=2)

        self._activity_data = deque(maxlen=50)

        # Запуск обновления
        self._update_statistics()

    def _update_statistics(self) -> None:
        """Обновление статистики"""
        try:
            # Получение статистики
            stats = None
            try:
                stats = self.controller.stats_queue.get_nowait()
            except queue.Empty:
                pass

            if stats:
                # Обновление значений
                self.stats_vars['fps'].set(f'FPS: {stats.get("fps", 0):.1f}')
                self.stats_vars['dps'].set(f'Объекты/сек: {stats.get("dps", 0):.1f}')
                self.stats_vars['detections'].set(f'Обнаружено: {stats.get("total", 0)}')
                self.stats_vars['current'].set(f'Сейчас: {stats.get("current", 0)}')

                # Категории
                categories = stats.get('categories', {})
                self.stats_vars['small'].set(
                    f'Мелкие: {categories.get(ObjectCategory.SMALL.value, 0)}'
                )
                self.stats_vars['medium'].set(
                    f'Средние: {categories.get(ObjectCategory.MEDIUM.value, 0)}'
                )
                self.stats_vars['large'].set(
                    f'Крупные: {categories.get(ObjectCategory.LARGE.value, 0)}'
                )

                # Время работы
                uptime = stats.get('uptime', 0)
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                seconds = int(uptime % 60)
                if hours > 0:
                    self.stats_vars['uptime'].set(
                        f'Время работы: {hours:02d}:{minutes:02d}:{seconds:02d}'
                    )
                else:
                    self.stats_vars['uptime'].set(
                        f'Время работы: {minutes:02d}:{seconds:02d}'
                    )

                # Обновление графика
                self._activity_data.append(stats.get('current', 0))
                self._draw_activity_graph()

        except Exception as e:
            logger.error(f"Statistics update error: {e}")

        # Следующее обновление
        self.after(1000, self._update_statistics)

    def _draw_activity_graph(self) -> None:
        """Отрисовка графика активности"""
        if not self._activity_data:
            return

        canvas = self.graph_canvas
        canvas.delete('all')

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width <= 1 or height <= 1:
            return

        # Масштабирование
        max_val = max(self._activity_data) if self._activity_data else 1
        if max_val == 0:
            max_val = 1
        scale_y = (height - 20) / max_val

        # Отрисовка графика
        points = []
        for i, value in enumerate(self._activity_data):
            x = (i / len(self._activity_data)) * (width - 40) + 20
            y = height - 10 - (value * scale_y)
            points.append((x, y))

        # Линия
        if len(points) >= 2:
            for i in range(1, len(points)):
                canvas.create_line(
                    points[i - 1][0], points[i - 1][1],
                    points[i][0], points[i][1],
                    fill='blue', width=2
                )

        # Точки
        for x, y in points:
            canvas.create_oval(
                x - 2, y - 2, x + 2, y + 2,
                fill='red', outline='red'
            )

        # Подписи
        canvas.create_text(
            5, 5,
            text=f'Макс: {max_val}',
            anchor='nw', fill='black'
        )