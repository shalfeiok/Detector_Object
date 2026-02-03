"""Окно настроек"""

import tkinter as tk
from tkinter import ttk, messagebox
import re
from typing import Dict, Tuple
from models.config import (
    GlobalConfig, CaptureConfig, DisplayConfig, AlertConfig,
    ContourConfig, MotionConfig, AdaptiveConfig, SensitiveConfig,
    MultiScaleConfig, ThermalConfig, TrailsConfig
)
from models.enums import TrackingMethod, CaptureSource, ObjectCategory
from .widgets import BaseWidget
from core.capture import WindowManager
from utils.logger import logger

class SettingsWindow(tk.Toplevel):
    """Окно настроек"""

    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.title('Настройки отслеживания')
        self.geometry('700x800')
        self.resizable(True, True)

        # Защита от множественных окон
        self.transient(parent)
        self.grab_set()

        # Создание вкладок
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Вкладки
        self._create_capture_tab()
        self._create_display_tab()
        self._create_alerts_tab()
        self._create_algorithms_tab()

        # Кнопки
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(
            button_frame, text='Применить',
            command=self._apply_settings
        ).pack(side='left', padx=5)

        ttk.Button(
            button_frame, text='Сбросить',
            command=self._reset_settings
        ).pack(side='left', padx=5)

        ttk.Button(
            button_frame, text='Закрыть',
            command=self.destroy
        ).pack(side='right', padx=5)

        # Статус
        self.status_label = ttk.Label(self, text='')
        self.status_label.pack(pady=5)

        # Инициализация значений
        self._load_current_settings()

    def _create_capture_tab(self):
        """Создание вкладки захвата"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text='Захват')

        # Источник захвата
        row = 0
        ttk.Label(frame, text='Источник захвата:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.capture_source_var = tk.StringVar()
        source_combo = ttk.Combobox(
            frame, textvariable=self.capture_source_var,
            values=[s.value for s in CaptureSource],
            state='readonly', width=20
        )
        source_combo.grid(row=row, column=1, sticky='w', padx=5, pady=5)
        row += 1

        # Заголовок окна
        ttk.Label(frame, text='Заголовок окна:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.window_title_var = tk.StringVar()
        self.window_title_entry = ttk.Entry(
            frame, textvariable=self.window_title_var, width=30
        )
        self.window_title_entry.grid(
            row=row, column=1, sticky='ew', padx=5, pady=5
        )

        # Кнопка обновления списка окон
        ttk.Button(
            frame, text='Обновить список окон',
            command=self._refresh_window_list
        ).grid(row=row, column=2, padx=5, pady=5)
        row += 1

        # Выпадающий список окон
        ttk.Label(frame, text='Доступные окна:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.windows_listbox = tk.Listbox(frame, height=10, width=50)
        self.windows_listbox.grid(
            row=row, column=1, columnspan=2, sticky='ew', padx=5, pady=5
        )
        self.windows_listbox.bind('<<ListboxSelect>>', self._on_window_select)
        row += 1

        # FPS лимит
        ttk.Label(frame, text='Ограничение FPS:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.fps_limit_var = tk.IntVar()
        ttk.Spinbox(
            frame, from_=1, to=60, textvariable=self.fps_limit_var,
            width=10
        ).grid(row=row, column=1, sticky='w', padx=5, pady=5)
        row += 1

        # Размер буфера
        ttk.Label(frame, text='Размер буфера:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.buffer_size_var = tk.IntVar()
        ttk.Spinbox(
            frame, from_=1, to=20, textvariable=self.buffer_size_var,
            width=10
        ).grid(row=row, column=1, sticky='w', padx=5, pady=5)

    def _create_display_tab(self):
        """Создание вкладки отображения"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text='Отображение')

        row = 0
        # Показать оригинал
        self.show_original_var = tk.BooleanVar()
        ttk.Checkbutton(
            frame, text='Показать оригинальное изображение',
            variable=self.show_original_var
        ).grid(row=row, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        row += 1

        # Тепловая карта
        self.show_heatmap_var = tk.BooleanVar()
        ttk.Checkbutton(
            frame, text='Показать тепловую карту',
            variable=self.show_heatmap_var
        ).grid(row=row, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        row += 1

        # Яркость
        ttk.Label(frame, text='Яркость:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.brightness_var = tk.DoubleVar()
        brightness_scale = ttk.Scale(
            frame, from_=0.5, to=2.0,
            variable=self.brightness_var, orient='horizontal'
        )
        brightness_scale.grid(row=row, column=1, sticky='ew', padx=5, pady=5)

        brightness_label = ttk.Label(
            frame, textvariable=tk.StringVar(
                value=f'{self.brightness_var.get():.1f}'
            )
        )
        brightness_label.grid(row=row, column=2, padx=5, pady=5)

        brightness_scale.configure(
            command=lambda v: brightness_label.config(
                text=f'{float(v):.1f}'
            )
        )
        row += 1

        # Контраст
        ttk.Label(frame, text='Контраст:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.contrast_var = tk.DoubleVar()
        contrast_scale = ttk.Scale(
            frame, from_=0.5, to=2.0,
            variable=self.contrast_var, orient='horizontal'
        )
        contrast_scale.grid(row=row, column=1, sticky='ew', padx=5, pady=5)

        contrast_label = ttk.Label(
            frame, textvariable=tk.StringVar(
                value=f'{self.contrast_var.get():.1f}'
            )
        )
        contrast_label.grid(row=row, column=2, padx=5, pady=5)

        contrast_scale.configure(
            command=lambda v: contrast_label.config(
                text=f'{float(v):.1f}'
            )
        )
        row += 1

        # Цвета объектов
        ttk.Label(frame, text='Цвета объектов:').grid(
            row=row, column=0, sticky='w', padx=5, pady=(10, 5)
        )
        row += 1

        self.color_vars = {}
        colors = self.controller.config.colors
        for i, (category, color) in enumerate(colors.items()):
            ttk.Label(frame, text=category).grid(
                row=row, column=0, sticky='w', padx=20, pady=2
            )

            color_var = tk.StringVar(value=self._rgb_to_hex(color))
            color_entry = ttk.Entry(frame, textvariable=color_var, width=10)
            color_entry.grid(row=row, column=1, padx=5, pady=2)

            # Кнопка выбора цвета
            ttk.Button(
                frame, text='Выбрать',
                command=lambda cv=color_var: self._choose_color(cv)
            ).grid(row=row, column=2, padx=5, pady=2)

            self.color_vars[category] = color_var
            row += 1

    def _create_alerts_tab(self):
        """Создание вкладки оповещений"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text='Оповещения')

        row = 0
        # Включить алерты
        self.alerts_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(
            frame, text='Включить оповещения',
            variable=self.alerts_enabled_var
        ).grid(row=row, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        row += 1

        # Порог алерта
        ttk.Label(frame, text='Порог оповещения:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.alert_threshold_var = tk.IntVar()
        ttk.Spinbox(
            frame, from_=1, to=20, textvariable=self.alert_threshold_var,
            width=10
        ).grid(row=row, column=1, sticky='w', padx=5, pady=5)
        row += 1

        # Звуковые оповещения
        self.sound_alerts_var = tk.BooleanVar()
        ttk.Checkbutton(
            frame, text='Звуковые оповещения',
            variable=self.sound_alerts_var
        ).grid(row=row, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        row += 1

        # Визуальные оповещения
        self.visual_alerts_var = tk.BooleanVar()
        ttk.Checkbutton(
            frame, text='Визуальные оповещения',
            variable=self.visual_alerts_var
        ).grid(row=row, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        row += 1

        # Категории для оповещений
        ttk.Label(frame, text='Категории для оповещений:').grid(
            row=row, column=0, sticky='w', padx=5, pady=(10, 5)
        )
        row += 1

        self.category_vars = {}
        for category in ObjectCategory:
            var = tk.BooleanVar()
            self.category_vars[category] = var

            ttk.Checkbutton(
                frame, text=category.value,
                variable=var
            ).grid(row=row, column=0, columnspan=2, sticky='w', padx=20, pady=2)
            row += 1

    def _create_algorithms_tab(self):
        """Создание вкладки алгоритмов"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text='Алгоритмы')

        # Создаем вложенные вкладки для каждого алгоритма
        algorithm_notebook = ttk.Notebook(frame)
        algorithm_notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Контурный детектор
        contour_frame = ttk.Frame(algorithm_notebook)
        algorithm_notebook.add(contour_frame, text='Контурный')
        self._create_contour_settings(contour_frame)

        # Детектор движения
        motion_frame = ttk.Frame(algorithm_notebook)
        algorithm_notebook.add(motion_frame, text='Движение')
        self._create_motion_settings(motion_frame)

        # Адаптивный фон
        adaptive_frame = ttk.Frame(algorithm_notebook)
        algorithm_notebook.add(adaptive_frame, text='Адаптивный')
        self._create_adaptive_settings(adaptive_frame)

        # Чувствительный
        sensitive_frame = ttk.Frame(algorithm_notebook)
        algorithm_notebook.add(sensitive_frame, text='Чувствительный')
        self._create_sensitive_settings(sensitive_frame)

        # Многоуровневый
        multiscale_frame = ttk.Frame(algorithm_notebook)
        algorithm_notebook.add(multiscale_frame, text='Многоуровневый')
        self._create_multiscale_settings(multiscale_frame)

        # Тепловизионный
        thermal_frame = ttk.Frame(algorithm_notebook)
        algorithm_notebook.add(thermal_frame, text='Тепловизионный')
        self._create_thermal_settings(thermal_frame)

        # Следы движения
        trails_frame = ttk.Frame(algorithm_notebook)
        algorithm_notebook.add(trails_frame, text='Следы')
        self._create_trails_settings(trails_frame)

    def _create_contour_settings(self, parent):
        """Настройки контурного детектора"""
        row = 0

        # Чувствительность
        ttk.Label(parent, text='Чувствительность:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.contour_sensitivity_var = tk.DoubleVar()
        sensitivity_scale = ttk.Scale(
            parent, from_=0.1, to=3.0,
            variable=self.contour_sensitivity_var, orient='horizontal'
        )
        sensitivity_scale.grid(row=row, column=1, sticky='ew', padx=5, pady=5)

        sensitivity_label = ttk.Label(
            parent, textvariable=tk.StringVar(
                value=f'{self.contour_sensitivity_var.get():.1f}'
            )
        )
        sensitivity_label.grid(row=row, column=2, padx=5, pady=5)

        sensitivity_scale.configure(
            command=lambda v: sensitivity_label.config(
                text=f'{float(v):.1f}'
            )
        )
        row += 1

        # Минимальная площадь
        ttk.Label(parent, text='Минимальная площадь:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.contour_min_area_var = tk.IntVar()
        ttk.Entry(parent, textvariable=self.contour_min_area_var, width=10).grid(
            row=row, column=1, sticky='w', padx=5, pady=5
        )
        row += 1

        # Порог
        ttk.Label(parent, text='Порог:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.contour_threshold_var = tk.IntVar()
        ttk.Entry(parent, textvariable=self.contour_threshold_var, width=10).grid(
            row=row, column=1, sticky='w', padx=5, pady=5
        )
        row += 1

        # Размер размытия
        ttk.Label(parent, text='Размер размытия:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.contour_blur_var = tk.IntVar()
        ttk.Entry(parent, textvariable=self.contour_blur_var, width=10).grid(
            row=row, column=1, sticky='w', padx=5, pady=5
        )

    def _create_motion_settings(self, parent):
        """Настройки детектора движения"""
        row = 0

        # Чувствительность
        ttk.Label(parent, text='Чувствительность:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.motion_sensitivity_var = tk.DoubleVar()
        sensitivity_scale = ttk.Scale(
            parent, from_=0.1, to=3.0,
            variable=self.motion_sensitivity_var, orient='horizontal'
        )
        sensitivity_scale.grid(row=row, column=1, sticky='ew', padx=5, pady=5)

        sensitivity_label = ttk.Label(
            parent, textvariable=tk.StringVar(
                value=f'{self.motion_sensitivity_var.get():.1f}'
            )
        )
        sensitivity_label.grid(row=row, column=2, padx=5, pady=5)

        sensitivity_scale.configure(
            command=lambda v: sensitivity_label.config(
                text=f'{float(v):.1f}'
            )
        )
        row += 1

        # Минимальное изменение пикселя
        ttk.Label(parent, text='Мин. изменение пикселя:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.motion_min_pixel_var = tk.IntVar()
        ttk.Entry(parent, textvariable=self.motion_min_pixel_var, width=10).grid(
            row=row, column=1, sticky='w', padx=5, pady=5
        )
        row += 1

        # Порог движения
        ttk.Label(parent, text='Порог движения:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.motion_threshold_var = tk.DoubleVar()
        ttk.Entry(parent, textvariable=self.motion_threshold_var, width=10).grid(
            row=row, column=1, sticky='w', padx=5, pady=5
        )

    def _create_adaptive_settings(self, parent):
        """Настройки адаптивного фона"""
        row = 0

        # Чувствительность
        ttk.Label(parent, text='Чувствительность:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.adaptive_sensitivity_var = tk.DoubleVar()
        sensitivity_scale = ttk.Scale(
            parent, from_=0.1, to=3.0,
            variable=self.adaptive_sensitivity_var, orient='horizontal'
        )
        sensitivity_scale.grid(row=row, column=1, sticky='ew', padx=5, pady=5)

        sensitivity_label = ttk.Label(
            parent, textvariable=tk.StringVar(
                value=f'{self.adaptive_sensitivity_var.get():.1f}'
            )
        )
        sensitivity_label.grid(row=row, column=2, padx=5, pady=5)

        sensitivity_scale.configure(
            command=lambda v: sensitivity_label.config(
                text=f'{float(v):.1f}'
            )
        )
        row += 1

        # Скорость обучения
        ttk.Label(parent, text='Скорость обучения:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.adaptive_learning_var = tk.DoubleVar()
        ttk.Entry(parent, textvariable=self.adaptive_learning_var, width=10).grid(
            row=row, column=1, sticky='w', padx=5, pady=5
        )
        row += 1

        # Порог дисперсии
        ttk.Label(parent, text='Порог дисперсии:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.adaptive_var_threshold_var = tk.DoubleVar()
        ttk.Entry(parent, textvariable=self.adaptive_var_threshold_var, width=10).grid(
            row=row, column=1, sticky='w', padx=5, pady=5
        )

    def _create_sensitive_settings(self, parent):
        """Настройки чувствительного детектора"""
        row = 0

        # Чувствительность
        ttk.Label(parent, text='Чувствительность:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.sensitive_sensitivity_var = tk.DoubleVar()
        sensitivity_scale = ttk.Scale(
            parent, from_=0.1, to=3.0,
            variable=self.sensitive_sensitivity_var, orient='horizontal'
        )
        sensitivity_scale.grid(row=row, column=1, sticky='ew', padx=5, pady=5)

        sensitivity_label = ttk.Label(
            parent, textvariable=tk.StringVar(
                value=f'{self.sensitive_sensitivity_var.get():.1f}'
            )
        )
        sensitivity_label.grid(row=row, column=2, padx=5, pady=5)

        sensitivity_scale.configure(
            command=lambda v: sensitivity_label.config(
                text=f'{float(v):.1f}'
            )
        )
        row += 1

        # Усиление контраста
        ttk.Label(parent, text='Усиление контраста:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.sensitive_enhancement_var = tk.DoubleVar()
        ttk.Entry(parent, textvariable=self.sensitive_enhancement_var, width=10).grid(
            row=row, column=1, sticky='w', padx=5, pady=5
        )
        row += 1

        # Снижение шума
        ttk.Label(parent, text='Снижение шума:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.sensitive_noise_reduction_var = tk.DoubleVar()
        ttk.Entry(parent, textvariable=self.sensitive_noise_reduction_var, width=10).grid(
            row=row, column=1, sticky='w', padx=5, pady=5
        )

    def _create_multiscale_settings(self, parent):
        """Настройки многоуровневого детектора"""
        row = 0

        # Чувствительность
        ttk.Label(parent, text='Чувствительность:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.multiscale_sensitivity_var = tk.DoubleVar()
        sensitivity_scale = ttk.Scale(
            parent, from_=0.1, to=3.0,
            variable=self.multiscale_sensitivity_var, orient='horizontal'
        )
        sensitivity_scale.grid(row=row, column=1, sticky='ew', padx=5, pady=5)

        sensitivity_label = ttk.Label(
            parent, textvariable=tk.StringVar(
                value=f'{self.multiscale_sensitivity_var.get():.1f}'
            )
        )
        sensitivity_label.grid(row=row, column=2, padx=5, pady=5)

        sensitivity_scale.configure(
            command=lambda v: sensitivity_label.config(
                text=f'{float(v):.1f}'
            )
        )
        row += 1

        # Уровни масштабирования
        ttk.Label(parent, text='Уровни масштабирования:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.multiscale_levels_var = tk.IntVar()
        ttk.Entry(parent, textvariable=self.multiscale_levels_var, width=10).grid(
            row=row, column=1, sticky='w', padx=5, pady=5
        )

    def _create_thermal_settings(self, parent):
        """Настройки тепловизионного детектора"""
        row = 0

        # Чувствительность
        ttk.Label(parent, text='Чувствительность:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.thermal_sensitivity_var = tk.DoubleVar()
        sensitivity_scale = ttk.Scale(
            parent, from_=0.1, to=3.0,
            variable=self.thermal_sensitivity_var, orient='horizontal'
        )
        sensitivity_scale.grid(row=row, column=1, sticky='ew', padx=5, pady=5)

        sensitivity_label = ttk.Label(
            parent, textvariable=tk.StringVar(
                value=f'{self.thermal_sensitivity_var.get():.1f}'
            )
        )
        sensitivity_label.grid(row=row, column=2, padx=5, pady=5)

        sensitivity_scale.configure(
            command=lambda v: sensitivity_label.config(
                text=f'{float(v):.1f}'
            )
        )
        row += 1

        # Цветовая карта
        ttk.Label(parent, text='Цветовая карта:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.thermal_colormap_var = tk.StringVar()
        colormap_combo = ttk.Combobox(
            parent, textvariable=self.thermal_colormap_var,
            values=['jet', 'hot', 'cool', 'autumn'],
            state='readonly', width=10
        )
        colormap_combo.grid(row=row, column=1, sticky='w', padx=5, pady=5)

    def _create_trails_settings(self, parent):
        """Настройки следов движения"""
        row = 0

        # Чувствительность
        ttk.Label(parent, text='Чувствительность:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.trails_sensitivity_var = tk.DoubleVar()
        sensitivity_scale = ttk.Scale(
            parent, from_=0.1, to=3.0,
            variable=self.trails_sensitivity_var, orient='horizontal'
        )
        sensitivity_scale.grid(row=row, column=1, sticky='ew', padx=5, pady=5)

        sensitivity_label = ttk.Label(
            parent, textvariable=tk.StringVar(
                value=f'{self.trails_sensitivity_var.get():.1f}'
            )
        )
        sensitivity_label.grid(row=row, column=2, padx=5, pady=5)

        sensitivity_scale.configure(
            command=lambda v: sensitivity_label.config(
                text=f'{float(v):.1f}'
            )
        )
        row += 1

        # Длина следа
        ttk.Label(parent, text='Длина следа:').grid(
            row=row, column=0, sticky='w', padx=5, pady=5
        )

        self.trails_length_var = tk.IntVar()
        ttk.Entry(parent, textvariable=self.trails_length_var, width=10).grid(
            row=row, column=1, sticky='w', padx=5, pady=5
        )

    def _load_current_settings(self):
        """Загрузка текущих настроек"""
        cfg = self.controller.config

        # Захват
        self.capture_source_var.set(cfg.capture.source.value)
        self.window_title_var.set(cfg.capture.window_title)
        self.fps_limit_var.set(cfg.capture.fps_limit)
        self.buffer_size_var.set(cfg.capture.buffer_size)

        # Отображение
        self.show_original_var.set(cfg.display.show_original)
        self.show_heatmap_var.set(cfg.display.show_heatmap)
        self.brightness_var.set(cfg.display.brightness)
        self.contrast_var.set(cfg.display.contrast)

        # Оповещения
        self.alerts_enabled_var.set(cfg.alerts.enabled)
        self.alert_threshold_var.set(cfg.alerts.threshold)
        self.sound_alerts_var.set(cfg.alerts.sound_enabled)
        self.visual_alerts_var.set(cfg.alerts.visual_enabled)

        # Категории оповещений
        for category in ObjectCategory:
            var = self.category_vars.get(category)
            if var:
                var.set(category in cfg.alerts.categories)

        # Алгоритмы
        self.contour_sensitivity_var.set(cfg.contour.sensitivity)
        self.contour_min_area_var.set(cfg.contour.min_area)
        self.contour_threshold_var.set(cfg.contour.threshold)
        self.contour_blur_var.set(cfg.contour.blur_size)

        self.motion_sensitivity_var.set(cfg.motion.sensitivity)
        self.motion_min_pixel_var.set(cfg.motion.min_pixel_change)
        self.motion_threshold_var.set(cfg.motion.motion_threshold)

        self.adaptive_sensitivity_var.set(cfg.adaptive.sensitivity)
        self.adaptive_learning_var.set(cfg.adaptive.learning_rate)
        self.adaptive_var_threshold_var.set(cfg.adaptive.var_threshold)

        self.sensitive_sensitivity_var.set(cfg.sensitive.sensitivity)
        self.sensitive_enhancement_var.set(cfg.sensitive.enhancement_factor)
        self.sensitive_noise_reduction_var.set(cfg.sensitive.noise_reduction)

        self.multiscale_sensitivity_var.set(cfg.multiscale.sensitivity)
        self.multiscale_levels_var.set(cfg.multiscale.pyramid_levels)

        self.thermal_sensitivity_var.set(cfg.thermal.sensitivity)
        self.thermal_colormap_var.set(cfg.thermal.color_map)

        self.trails_sensitivity_var.set(cfg.trails.sensitivity)
        self.trails_length_var.set(cfg.trails.trail_length)

        # Обновление списка окон
        self._refresh_window_list()

    def _refresh_window_list(self):
        """Обновление списка окон"""
        try:
            windows = WindowManager.list_windows()
            self.windows_listbox.delete(0, tk.END)

            for window in windows[:50]:  # Ограничиваем показ 50 окнами
                self.windows_listbox.insert(tk.END, window)

        except Exception as e:
            logger.error(f"Failed to refresh window list: {e}")

    def _on_window_select(self, event):
        """Обработчик выбора окна из списка"""
        selection = self.windows_listbox.curselection()
        if selection:
            window_title = self.windows_listbox.get(selection[0])
            self.window_title_var.set(window_title)

    def _choose_color(self, color_var: tk.StringVar):
        """Выбор цвета через диалог"""
        from tkinter import colorchooser

        color = colorchooser.askcolor(
            initialcolor=color_var.get(),
            title="Выберите цвет"
        )

        if color[1]:  # color[1] - hex представление
            color_var.set(color[1])

    def _apply_settings(self):
        """Применение настроек"""
        try:
            cfg = self.controller.config

            # Захват
            source_value = self.capture_source_var.get()
            for source in CaptureSource:
                if source.value == source_value:
                    cfg.capture.source = source
                    break

            cfg.capture.window_title = self.window_title_var.get()
            cfg.capture.fps_limit = self.fps_limit_var.get()
            cfg.capture.buffer_size = self.buffer_size_var.get()

            # Отображение
            cfg.display.show_original = self.show_original_var.get()
            cfg.display.show_heatmap = self.show_heatmap_var.get()
            cfg.display.brightness = self.brightness_var.get()
            cfg.display.contrast = self.contrast_var.get()

            # Оповещения
            cfg.alerts.enabled = self.alerts_enabled_var.get()
            cfg.alerts.threshold = self.alert_threshold_var.get()
            cfg.alerts.sound_enabled = self.sound_alerts_var.get()
            cfg.alerts.visual_enabled = self.visual_alerts_var.get()

            # Категории оповещений
            cfg.alerts.categories = []
            for category, var in self.category_vars.items():
                if var.get():
                    cfg.alerts.categories.append(category)

            # Цвета
            for category, color_var in self.color_vars.items():
                hex_color = color_var.get()
                if self._is_valid_hex(hex_color):
                    rgb = self._hex_to_rgb(hex_color)
                    cfg.colors[category] = rgb

            # Алгоритмы
            cfg.contour.sensitivity = self.contour_sensitivity_var.get()
            cfg.contour.min_area = self.contour_min_area_var.get()
            cfg.contour.threshold = self.contour_threshold_var.get()
            cfg.contour.blur_size = self.contour_blur_var.get()

            cfg.motion.sensitivity = self.motion_sensitivity_var.get()
            cfg.motion.min_pixel_change = self.motion_min_pixel_var.get()
            cfg.motion.motion_threshold = self.motion_threshold_var.get()

            cfg.adaptive.sensitivity = self.adaptive_sensitivity_var.get()
            cfg.adaptive.learning_rate = self.adaptive_learning_var.get()
            cfg.adaptive.var_threshold = self.adaptive_var_threshold_var.get()

            cfg.sensitive.sensitivity = self.sensitive_sensitivity_var.get()
            cfg.sensitive.enhancement_factor = self.sensitive_enhancement_var.get()
            cfg.sensitive.noise_reduction = self.sensitive_noise_reduction_var.get()

            cfg.multiscale.sensitivity = self.multiscale_sensitivity_var.get()
            cfg.multiscale.pyramid_levels = self.multiscale_levels_var.get()

            cfg.thermal.sensitivity = self.thermal_sensitivity_var.get()
            cfg.thermal.color_map = self.thermal_colormap_var.get()

            cfg.trails.sensitivity = self.trails_sensitivity_var.get()
            cfg.trails.trail_length = self.trails_length_var.get()

            # Применение конфигурации
            self.controller.update_config(cfg)

            self.status_label.config(
                text='Настройки применены',
                foreground='green'
            )

            logger.info('Settings applied successfully')

        except Exception as e:
            self.status_label.config(
                text=f'Ошибка: {str(e)}',
                foreground='red'
            )
            logger.error(f'Error applying settings: {e}')

    def _reset_settings(self):
        """Сброс настроек к значениям по умолчанию"""
        if messagebox.askyesno("Сброс", "Сбросить все настройки к значениям по умолчанию?"):
            self.controller.config = GlobalConfig()
            self._load_current_settings()
            self.status_label.config(
                text='Настройки сброшены',
                foreground='green'
            )
            logger.info('Settings reset to default')

    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Конвертация RGB в HEX"""
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Конвертация HEX в RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _is_valid_hex(self, color: str) -> bool:
        """Проверка валидности HEX цвета"""
        pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        return bool(re.match(pattern, color))