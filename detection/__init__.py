"""Fase 3: motor de detección de redes de riesgo."""

_LAZY = {"run_detection", "DetectionConfig", "DetectionResult"}


def __getattr__(name: str):
    if name in _LAZY:
        if name == "run_detection":
            from detection.engine import run_detection

            return run_detection
        from detection.model import DetectionConfig, DetectionResult

        return {"DetectionConfig": DetectionConfig, "DetectionResult": DetectionResult}[name]
    raise AttributeError(name)


__all__ = ["DetectionConfig", "DetectionResult", "run_detection"]
