"""Модели данных для детекции"""

import numpy as np
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from .enums import ObjectCategory


@dataclass
class DetectionResult:
    """Результат детектирования объекта"""
    bbox: Tuple[int, int, int, int]
    center: Tuple[int, int]
    area: int
    contour: Optional[np.ndarray] = None
    category: ObjectCategory = ObjectCategory.UNKNOWN
    confidence: float = 0.5
    velocity: float = 0.0
    direction: float = 0.0
    id: int = 0

    def __post_init__(self):
        if self.id == 0:
            self.id = id(self)

    @property
    def width(self) -> int:
        return self.bbox[2]

    @property
    def height(self) -> int:
        return self.bbox[3]

    @property
    def x(self) -> int:
        return self.bbox[0]

    @property
    def y(self) -> int:
        return self.bbox[1]

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            'id': self.id,
            'bbox': self.bbox,
            'center': self.center,
            'area': self.area,
            'category': self.category.value,
            'confidence': self.confidence,
            'velocity': self.velocity,
            'direction': self.direction
        }