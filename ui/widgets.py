"""Базовые виджеты"""

import tkinter as tk
from tkinter import ttk
from typing import Optional
from core.controller import TrackingController


class BaseWidget(ttk.Frame):
    """Базовый виджет с общей функциональностью"""

    def __init__(self, parent, controller: TrackingController, **kwargs):
        super().__init__(parent, **kwargs)
        self.controller = controller
        self._setup_styles()

    def _setup_styles(self) -> None:
        """Настройка стилей виджета"""
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Value.TLabel', font=('Arial', 10))
        style.configure('Stats.TFrame', relief='solid', borderwidth=1)
        style.configure('Control.TFrame', relief='raised', borderwidth=2)

    def create_labeled_slider(self, parent, label_text: str,
                              from_: float, to: float,
                              variable: tk.Variable,
                              resolution: float = 0.01,
                              show_value: bool = True) -> ttk.Frame:
        """Создание ползунка с меткой"""
        frame = ttk.Frame(parent)

        # Метка
        ttk.Label(frame, text=label_text, width=20).pack(side='left', padx=5)

        # Ползунок
        slider = ttk.Scale(frame, from_=from_, to=to,
                           variable=variable, orient='horizontal',
                           length=200)
        slider.pack(side='left', padx=5, fill='x', expand=True)

        # Значение
        if show_value:
            value_label = ttk.Label(frame, textvariable=tk.StringVar(
                value=f'{variable.get():.2f}'
            ), width=8)
            value_label.pack(side='right', padx=5)

            # Обновление значения при изменении ползунка
            def update_label(val):
                value_label.config(text=f'{float(val):.2f}')

            slider.configure(command=update_label)

        return frame

    def create_labeled_spinbox(self, parent, label_text: str,
                               from_: int, to: int,
                               variable: tk.Variable,
                               increment: int = 1) -> ttk.Frame:
        """Создание счетчика с меткой"""
        frame = ttk.Frame(parent)

        # Метка
        ttk.Label(frame, text=label_text, width=20).pack(side='left', padx=5)

        # Счетчик
        spinbox = ttk.Spinbox(frame, from_=from_, to=to,
                              increment=increment, textvariable=variable,
                              width=10)
        spinbox.pack(side='left', padx=5)

        return frame