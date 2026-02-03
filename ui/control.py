"""Панель управления"""

import tkinter as tk
from tkinter import ttk, messagebox
from .widgets import BaseWidget
from .settings import SettingsWindow
from models.enums import TrackingMethod
from utils.logger import logger


class ControlPanel(BaseWidget):
    """Панель управления"""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Кнопки управления
        button_frame = ttk.Frame(self, style='Control.TFrame')
        button_frame.pack(fill='x', padx=5, pady=5)

        self.start_button = ttk.Button(
            button_frame, text='▶ Старт',
            command=self._on_start
        )
        self.start_button.pack(side='left', padx=2)

        self.stop_button = ttk.Button(
            button_frame, text='⏹ Стоп',
            command=self._on_stop, state='disabled'
        )
        self.stop_button.pack(side='left', padx=2)

        self.settings_button = ttk.Button(
            button_frame, text='⚙ Настройки',
            command=self._on_settings
        )
        self.settings_button.pack(side='left', padx=2)

        ttk.Button(
            button_frame, text='🔄 Сброс',
            command=self._on_reset
        ).pack(side='left', padx=2)

        # Метод отслеживания
        method_frame = ttk.Frame(self)
        method_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(method_frame, text='Метод:').pack(side='left', padx=(0, 5))

        self.method_var = tk.StringVar(
            value=self.controller.config.method.value
        )
        self.method_combo = ttk.Combobox(
            method_frame, textvariable=self.method_var,
            values=[m.value for m in TrackingMethod],
            state='readonly', width=20
        )
        self.method_combo.pack(side='left')
        self.method_combo.bind('<<ComboboxSelected>>', self._on_method_change)

        # Статус
        self.status_var = tk.StringVar(value='Готов')
        self.status_label = ttk.Label(
            self, textvariable=self.status_var,
            foreground='green'
        )
        self.status_label.pack(pady=5)

    def _on_start(self) -> None:
        """Обработчик старта"""
        self.controller.start()
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_var.set('Отслеживание запущено')

    def _on_stop(self) -> None:
        """Обработчик остановки"""
        self.controller.stop()
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_var.set('Отслеживание остановлено')

    def _on_method_change(self, event=None) -> None:
        """Обработчик изменения метода"""
        method_name = self.method_var.get()
        for method in TrackingMethod:
            if method.value == method_name:
                self.controller.switch_method(method)
                break

    def _on_settings(self) -> None:
        """Обработчик открытия настроек"""
        SettingsWindow(self.winfo_toplevel(), self.controller)

    def _on_reset(self) -> None:
        """Обработчик сброса статистики"""
        if messagebox.askyesno("Сброс", "Сбросить статистику?"):
            from core.statistics import TrackingStatistics
            self.controller._stats = TrackingStatistics()
            logger.info("Statistics reset")