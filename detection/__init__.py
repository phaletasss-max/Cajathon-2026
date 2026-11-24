"""Fase 3: motor de detección de redes de riesgo."""

from detection.engine import run_detection
from detection.model import DetectionConfig, DetectionResult

__all__ = ["DetectionConfig", "DetectionResult", "run_detection"]
