"""Fase 2: grafo bipartito y proyección ponderada de solicitudes.

Las funciones del constructor se cargan de forma perezosa para que
``python -m graph.builder`` no importe el módulo dos veces.
"""

from graph.export import export_graph
from graph.model import (
    ATTRIBUTE_TYPES,
    DEFAULT_WEIGHT_CAPS,
    GraphBuildResult,
    GraphConfig,
    attribute_weight,
    hash_attribute,
)

_LAZY_BUILDER_EXPORTS = {
    "build_graph",
    "build_graph_from_dir",
    "load_tables",
}


def __getattr__(name: str):
    if name in _LAZY_BUILDER_EXPORTS:
        from graph import builder

        return getattr(builder, name)
    raise AttributeError(f"module 'graph' has no attribute {name!r}")


__all__ = [
    "ATTRIBUTE_TYPES",
    "DEFAULT_WEIGHT_CAPS",
    "GraphBuildResult",
    "GraphConfig",
    "attribute_weight",
    "build_graph",
    "build_graph_from_dir",
    "export_graph",
    "hash_attribute",
    "load_tables",
]
