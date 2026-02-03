"""Модели перечислений"""

from enum import Enum, auto

class TrackingMethod(Enum):
    """Методы отслеживания объектов"""
    CONTOUR_DETECTION = "Контурный"
    MOTION_DETECTION = "Движение"
    ADAPTIVE_BACKGROUND = "Адаптивный фон"
    SENSITIVE_MOTION = "Чувствительный"
    MULTI_SCALE = "Многоуровневый"
    THERMAL_SIMULATION = "Тепловизионный"
    MOVEMENT_TRAILS = "Следы движения"

class ObjectCategory(Enum):
    """Категории объектов"""
    SMALL = "Мелкий"
    MEDIUM = "Средний"
    LARGE = "Крупный"
    BIRD = "Птица"
    UNKNOWN = "Неизвестно"

class CaptureSource(Enum):
    """Источники захвата"""
    FULL_SCREEN = "Весь экран"
    ACTIVE_WINDOW = "Активное окно"
    WINDOW_BY_TITLE = "Окно по названию"
    REGION = "Область экрана"