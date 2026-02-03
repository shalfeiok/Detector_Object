"""Модели конфигураций"""

from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Optional
from .enums import TrackingMethod, ObjectCategory, CaptureSource
from abc import ABC, abstractmethod

@dataclass
class AlgorithmConfig(ABC):
    """Базовый класс конфигурации алгоритма"""
    sensitivity: float = 1.0  # Общий параметр чувствительности от 0.1 до 3.0

    @abstractmethod
    def validate(self) -> bool:
        """Валидация параметров"""
        pass

@dataclass
class ContourConfig(AlgorithmConfig):
    """Конфигурация контурного детектора"""
    min_area: int = 30
    max_area: int = 50000
    threshold: int = 25
    blur_size: int = 3
    aspect_ratio_min: float = 0.2
    aspect_ratio_max: float = 5.0
    solidity_threshold: float = 0.5

    def validate(self) -> bool:
        return (self.min_area > 0 and
                self.max_area > self.min_area and
                self.blur_size >= 0)

@dataclass
class MotionConfig(AlgorithmConfig):
    """Конфигурация детектора движения"""
    min_pixel_change: int = 5
    temporal_buffer_size: int = 3
    motion_threshold: float = 0.1
    persistence_frames: int = 5
    velocity_threshold: float = 5.0

    def validate(self) -> bool:
        return (self.min_pixel_change > 0 and
                self.temporal_buffer_size >= 2)

@dataclass
class AdaptiveConfig(AlgorithmConfig):
    """Конфигурация адаптивного фона"""
    learning_rate: float = 0.001
    history_length: int = 200
    var_threshold: float = 16.0
    detect_shadows: bool = True
    shadow_threshold: float = 0.5

    def validate(self) -> bool:
        return (0 < self.learning_rate <= 1 and
                self.history_length > 0)

@dataclass
class SensitiveConfig(AlgorithmConfig):
    """Конфигурация чувствительного детектора"""
    min_pixel_change: int = 3
    frame_buffer_size: int = 5
    accumulation_threshold: int = 2
    temporal_filter: bool = True
    spatial_filter: bool = True
    enhancement_factor: float = 2.0
    noise_reduction: float = 0.8

    def validate(self) -> bool:
        return (self.min_pixel_change > 0 and
                self.frame_buffer_size >= 3)

@dataclass
class MultiScaleConfig(AlgorithmConfig):
    """Конфигурация многоуровневого детектора"""
    scales: List[float] = field(default_factory=lambda: [1.0, 0.5, 0.25])
    scale_weights: List[float] = field(default_factory=lambda: [1.0, 0.7, 0.5])
    merge_threshold: float = 0.5
    pyramid_levels: int = 3
    adaptive_scaling: bool = True

    def validate(self) -> bool:
        return (len(self.scales) > 0 and
                all(s > 0 for s in self.scales))

@dataclass
class ThermalConfig(AlgorithmConfig):
    """Конфигурация тепловизионной симуляции"""
    color_map: str = "jet"  # jet, hot, cool, autumn
    temperature_min: float = 0.0
    temperature_max: float = 100.0
    highlight_cold: bool = False
    cold_threshold: float = 20.0

    def validate(self) -> bool:
        return self.temperature_max > self.temperature_min

@dataclass
class TrailsConfig(AlgorithmConfig):
    """Конфигурация следов движения"""
    trail_length: int = 50
    decay_rate: float = 0.95
    color_cycling: bool = True
    show_history: bool = True
    prediction_length: int = 10
    smooth_trails: bool = True

    def validate(self) -> bool:
        return self.trail_length > 0

@dataclass
class CaptureConfig:
    """Конфигурация захвата экрана"""
    source: CaptureSource = CaptureSource.FULL_SCREEN
    window_title: str = ""
    region: Optional[Tuple[int, int, int, int]] = None  # x, y, width, height
    fps_limit: int = 30
    buffer_size: int = 5

@dataclass
class DisplayConfig:
    """Конфигурация отображения"""
    show_original: bool = False
    show_heatmap: bool = False
    show_grid: bool = False
    show_info: bool = True
    zoom_factor: float = 1.0
    brightness: float = 1.0
    contrast: float = 1.0

@dataclass
class AlertConfig:
    """Конфигурация оповещений"""
    enabled: bool = False
    threshold: int = 3
    sound_enabled: bool = True
    visual_enabled: bool = True
    categories: List[ObjectCategory] = field(default_factory=lambda: [
        ObjectCategory.MEDIUM, ObjectCategory.LARGE
    ])

@dataclass
class GlobalConfig:
    """Глобальная конфигурация приложения"""
    method: TrackingMethod = TrackingMethod.ADAPTIVE_BACKGROUND
    update_interval: float = 0.05

    # Конфигурации подсистем
    capture: CaptureConfig = field(default_factory=CaptureConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    alerts: AlertConfig = field(default_factory=AlertConfig)

    # Конфигурации алгоритмов
    contour: ContourConfig = field(default_factory=ContourConfig)
    motion: MotionConfig = field(default_factory=MotionConfig)
    adaptive: AdaptiveConfig = field(default_factory=AdaptiveConfig)
    sensitive: SensitiveConfig = field(default_factory=SensitiveConfig)
    multiscale: MultiScaleConfig = field(default_factory=MultiScaleConfig)
    thermal: ThermalConfig = field(default_factory=ThermalConfig)
    trails: TrailsConfig = field(default_factory=TrailsConfig)

    # Цветовая схема
    colors: Dict[str, Tuple[int, int, int]] = field(default_factory=lambda: {
        ObjectCategory.SMALL.value: (0, 255, 0),      # Зеленый
        ObjectCategory.MEDIUM.value: (255, 165, 0),   # Оранжевый
        ObjectCategory.LARGE.value: (255, 0, 0),      # Красный
        ObjectCategory.BIRD.value: (0, 191, 255),     # Голубой
        ObjectCategory.UNKNOWN.value: (128, 0, 128),  # Фиолетовый
    })

    def validate_all(self) -> bool:
        """Валидация всех конфигураций"""
        return all([
            self.contour.validate(),
            self.motion.validate(),
            self.adaptive.validate(),
            self.sensitive.validate(),
            self.multiscale.validate(),
            self.thermal.validate(),
            self.trails.validate()
        ])