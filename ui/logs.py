"""Панель логов"""

import logging
import tkinter as tk
from tkinter import ttk, scrolledtext
from .widgets import BaseWidget
from utils.logger import logger


class LogPanel(BaseWidget):
    """Панель логов"""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        title = ttk.Label(self, text='Логи', style='Title.TLabel')
        title.pack(anchor='w', padx=5, pady=(5, 0))

        # Текстовое поле логов
        self.log_text = scrolledtext.ScrolledText(
            self, height=10, width=50,
            wrap='word', state='disabled'
        )
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Кнопки управления логами
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', padx=5, pady=(0, 5))

        ttk.Button(
            button_frame, text='Очистить',
            command=self._clear_logs
        ).pack(side='left', padx=2)

        ttk.Button(
            button_frame, text='Сохранить',
            command=self._save_logs
        ).pack(side='left', padx=2)

        # Обработчик логов
        self._setup_log_handler()

    def _setup_log_handler(self) -> None:
        """Настройка обработчика логов"""

        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
                self.setFormatter(logging.Formatter(
                    '%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S'
                ))

            def emit(self, record):
                msg = self.format(record)

                def append():
                    self.text_widget.config(state='normal')
                    self.text_widget.insert('end', msg + '\n')
                    self.text_widget.see('end')
                    self.text_widget.config(state='disabled')

                self.text_widget.after(0, append)

        handler = TextHandler(self.log_text)
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)

    def _clear_logs(self) -> None:
        """Очистка логов"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')

    def _save_logs(self) -> None:
        """Сохранение логов в файл"""
        try:
            from tkinter import filedialog
            import os

            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )

            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))

                logger.info(f"Logs saved to {os.path.basename(filename)}")

        except Exception as e:
            logger.error(f"Failed to save logs: {e}")