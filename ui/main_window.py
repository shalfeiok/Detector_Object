"""Главное окно приложения"""

import tkinter as tk
from tkinter import ttk, messagebox
from .video import VideoDisplay
from .stats import StatisticsPanel
from .control import ControlPanel
from .logs import LogPanel
from core.controller import TrackingController
from utils.logger import logger


class MainApplication:
    """Главное окно приложения"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Wildlife Motion Tracker Pro')
        self.root.geometry('1200x800')

        # Инициализация контроллера
        self.controller = TrackingController()

        # Настройка интерфейса
        self._setup_ui()

        # Обработка закрытия
        self.root.protocol('WM_DELETE_WINDOW', self._on_closing)

    def _setup_ui(self) -> None:
        """Настройка пользовательского интерфейса"""
        # Главный контейнер
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)

        # Левая панель - видео
        left_panel = ttk.Frame(main_container)
        left_panel.pack(side='left', fill='both', expand=True)

        self.video_display = VideoDisplay(left_panel, self.controller)
        self.video_display.pack(fill='both', expand=True)

        # Правая панель - элементы управления
        right_panel = ttk.Frame(main_container, width=400)
        right_panel.pack(side='right', fill='y')
        right_panel.pack_propagate(False)

        # Панель управления
        control_panel = ControlPanel(right_panel, self.controller)
        control_panel.pack(fill='x', padx=5, pady=5)

        # Панель статистики
        stats_panel = StatisticsPanel(right_panel, self.controller)
        stats_panel.pack(fill='x', padx=5, pady=10)

        # Панель логов
        log_panel = LogPanel(right_panel, self.controller)
        log_panel.pack(fill='both', expand=True, padx=5, pady=5)

    def _on_closing(self) -> None:
        """Обработчик закрытия приложения"""
        if self.controller.is_running:
            if messagebox.askyesno("Выход", "Отслеживание активно. Завершить работу?"):
                self.controller.stop()
                self.root.destroy()
        else:
            self.root.destroy()

        logger.info('Application closed')

    def run(self) -> None:
        """Запуск приложения"""
        self.root.mainloop()