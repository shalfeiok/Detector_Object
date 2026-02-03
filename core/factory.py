"""Фабрика детекторов"""

from .detectors.contour import ContourDetector
from .detectors.motion import MotionDetector
from .detectors.adaptive import AdaptiveDetector
from .detectors.sensitive import SensitiveDetector
from .detectors.multiscale import MultiScaleDetector
from .detectors.thermal import ThermalDetector
from .detectors.trails import TrailsDetector
from models.config import GlobalConfig
from models.enums import TrackingMethod
from utils.logger import logger


class DetectorFactory:
    """Фабрика детекторов"""

    @staticmethod
    def create(method: TrackingMethod, config: GlobalConfig):
        """Создание детектора по методу"""
        detectors = {
            TrackingMethod.CONTOUR_DETECTION: ContourDetector,
            TrackingMethod.MOTION_DETECTION: MotionDetector,
            TrackingMethod.ADAPTIVE_BACKGROUND: AdaptiveDetector,
            TrackingMethod.SENSITIVE_MOTION: SensitiveDetector,
            TrackingMethod.MULTI_SCALE: MultiScaleDetector,
            TrackingMethod.THERMAL_SIMULATION: ThermalDetector,
            TrackingMethod.MOVEMENT_TRAILS: TrailsDetector,
        }

        detector_class = detectors.get(method)
        if detector_class is None:
            logger.warning(f"Unknown method: {method}, using AdaptiveDetector")
            detector_class = AdaptiveDetector

        return detector_class(config)