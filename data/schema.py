"""Esquemas, catálogos y utilidades compartidas del generador sintético.

Este módulo no contiene lógica de generación: solo contratos de columnas,
geoceldas de referencia y helpers de escritura. Mantenerlo libre de etiquetas
ocultas evita que la verdad terreno se filtre al motor de detección.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Sequence, TypeVar

SCHEMA_VERSION = "1.0"
DATA_DIR = Path(__file__).resolve().parent
DEFAULT_OUT_DIR = DATA_DIR

T = TypeVar("T")

# Geoceldas sintéticas de Trujillo y La Libertad, más algunas geoceldas
# nacionales usadas únicamente para migración y ubicaciones imposibles.
GEOCELLS: list[dict[str, object]] = [
    {"geocell_id": "GEO-TRU-01", "department": "La Libertad", "province": "Trujillo", "district": "Trujillo", "latitude": -8.1116, "longitude": -79.0287, "urban_rural": "urbano"},
    {"geocell_id": "GEO-TRU-02", "department": "La Libertad", "province": "Trujillo", "district": "El Porvenir", "latitude": -8.0750, "longitude": -78.9870, "urban_rural": "urbano"},
    {"geocell_id": "GEO-TRU-03", "department": "La Libertad", "province": "Trujillo", "district": "La Esperanza", "latitude": -8.0667, "longitude": -79.0333, "urban_rural": "urbano"},
    {"geocell_id": "GEO-TRU-04", "department": "La Libertad", "province": "Trujillo", "district": "Víctor Larco Herrera", "latitude": -8.1333, "longitude": -79.0500, "urban_rural": "urbano"},
    {"geocell_id": "GEO-TRU-05", "department": "La Libertad", "province": "Trujillo", "district": "Huanchaco", "latitude": -8.0833, "longitude": -79.1167, "urban_rural": "urbano"},
    {"geocell_id": "GEO-TRU-06", "department": "La Libertad", "province": "Trujillo", "district": "Laredo", "latitude": -8.0833, "longitude": -78.9500, "urban_rural": "urbano"},
    {"geocell_id": "GEO-TRU-07", "department": "La Libertad", "province": "Trujillo", "district": "Moche", "latitude": -8.1667, "longitude": -79.0000, "urban_rural": "urbano"},
    {"geocell_id": "GEO-TRU-08", "department": "La Libertad", "province": "Trujillo", "district": "Salaverry", "latitude": -8.2167, "longitude": -78.9833, "urban_rural": "urbano"},
    {"geocell_id": "GEO-LIB-01", "department": "La Libertad", "province": "Pacasmayo", "district": "Pacasmayo", "latitude": -7.4000, "longitude": -79.5667, "urban_rural": "urbano"},
    {"geocell_id": "GEO-LIB-02", "department": "La Libertad", "province": "Chepén", "district": "Chepén", "latitude": -7.2333, "longitude": -79.4333, "urban_rural": "urbano"},
    {"geocell_id": "GEO-LIB-03", "department": "La Libertad", "province": "Ascope", "district": "Ascope", "latitude": -7.7167, "longitude": -79.1167, "urban_rural": "urbano"},
    {"geocell_id": "GEO-LIB-04", "department": "La Libertad", "province": "Virú", "district": "Virú", "latitude": -8.4167, "longitude": -78.7500, "urban_rural": "urbano"},
    {"geocell_id": "GEO-LIB-05", "department": "La Libertad", "province": "Otuzco", "district": "Otuzco", "latitude": -7.9000, "longitude": -78.5667, "urban_rural": "urbano"},
    {"geocell_id": "GEO-LIB-06", "department": "La Libertad", "province": "Santiago de Chuco", "district": "Santiago de Chuco", "latitude": -8.1333, "longitude": -78.1833, "urban_rural": "urbano"},
    {"geocell_id": "GEO-LIB-07", "department": "La Libertad", "province": "Sánchez Carrión", "district": "Huamachuco", "latitude": -7.8167, "longitude": -78.0667, "urban_rural": "urbano"},
    {"geocell_id": "GEO-LIM-01", "department": "Lima", "province": "Lima", "district": "Comas", "latitude": -11.9500, "longitude": -77.0500, "urban_rural": "urbano"},
    {"geocell_id": "GEO-PIU-01", "department": "Piura", "province": "Piura", "district": "Piura", "latitude": -5.1945, "longitude": -80.6328, "urban_rural": "urbano"},
    {"geocell_id": "GEO-CHI-01", "department": "Lambayeque", "province": "Chiclayo", "district": "Chiclayo", "latitude": -6.7714, "longitude": -79.8409, "urban_rural": "urbano"},
    {"geocell_id": "GEO-IQT-01", "department": "Loreto", "province": "Maynas", "district": "Iquitos", "latitude": -3.7437, "longitude": -73.2516, "urban_rural": "urbano"},
    {"geocell_id": "GEO-CUS-01", "department": "Cusco", "province": "Cusco", "district": "Cusco", "latitude": -13.5319, "longitude": -71.9675, "urban_rural": "urbano"},
    {"geocell_id": "GEO-PUN-01", "department": "Puno", "province": "Puno", "district": "Puno", "latitude": -15.8402, "longitude": -70.0219, "urban_rural": "urbano"},
    {"geocell_id": "GEO-AQP-01", "department": "Arequipa", "province": "Arequipa", "district": "Arequipa", "latitude": -16.4090, "longitude": -71.5375, "urban_rural": "urbano"},
]
GEOCELL_BY_ID: dict[str, dict[str, object]] = {g["geocell_id"]: g for g in GEOCELLS}  # type: ignore[index]

# Peso relativo de residencia: ~88 % La Libertad, con migración interna mínima.
CITY_WEIGHTS: dict[str, float] = {
    "GEO-TRU-01": 0.21, "GEO-TRU-02": 0.11, "GEO-TRU-03": 0.09,
    "GEO-TRU-04": 0.05, "GEO-TRU-05": 0.04, "GEO-TRU-06": 0.04,
    "GEO-TRU-07": 0.03, "GEO-TRU-08": 0.02, "GEO-LIB-01": 0.07,
    "GEO-LIB-02": 0.05, "GEO-LIB-03": 0.04, "GEO-LIB-04": 0.04,
    "GEO-LIB-05": 0.03, "GEO-LIB-06": 0.03, "GEO-LIB-07": 0.03,
    "GEO-LIM-01": 0.05, "GEO-PIU-01": 0.04, "GEO-CHI-01": 0.03,
}

# Geoceldas lejanas usadas por la modalidad de ubicaciones imposibles.
FAR_GEOCELLS = ["GEO-IQT-01", "GEO-CUS-01", "GEO-PUN-01", "GEO-AQP-01"]

PUBLIC_SCHEMAS: dict[str, list[str]] = {
    "persons": [
        "person_id", "full_name", "doc_type", "doc_number", "birth_date", "gender",
        "home_address_id", "primary_phone_id", "primary_device_id", "occupation",
        "monthly_income_pen", "coop_id", "created_at",
    ],
    "businesses": [
        "business_id", "owner_person_id", "business_name", "sector",
        "commercial_address_id", "monthly_sales_pen", "created_at",
    ],
    "addresses": [
        "address_id", "address_type", "street", "district", "province",
        "department", "geocell_id", "latitude", "longitude",
    ],
    "phones": [
        "phone_id", "phone_number", "line_type", "owner_person_id", "activation_date",
    ],
    "devices": [
        "device_id", "device_fingerprint", "device_type", "owner_person_id", "first_seen",
    ],
    "applications": [
        "application_id", "person_id", "business_id", "product", "amount_pen",
        "term_months", "channel", "purpose", "created_at", "declared_address_id",
        "application_geocell_id", "device_id", "phone_id", "coop_id", "status",
    ],
    "references": [
        "reference_id", "application_id", "ref_person_id", "relationship",
        "ref_phone_id", "created_at",
    ],
    "geocells": [
        "geocell_id", "department", "province", "district", "latitude",
        "longitude", "urban_rural",
    ],
}

TRUTH_SCHEMAS: dict[str, list[str]] = {
    "ground_truth": [
        "application_id", "person_id", "ring_id", "ring_type", "cover_pattern", "ring_size",
    ],
    "rings": [
        "ring_id", "ring_type", "cover_pattern", "ring_size", "n_applications", "home_geocell",
    ],
}

# Columnas que jamás deben aparecer en las tablas públicas.
FORBIDDEN_PUBLIC_TOKENS = ("ring", "fraud", "label", "truth", "is_synthetic")


@dataclass
class IdAllocator:
    """Genera identificadores legibles y deterministas por prefijo."""

    counters: dict[str, int] = field(default_factory=dict)

    def next(self, prefix: str, width: int = 6) -> str:
        value = self.counters.get(prefix, 0) + 1
        self.counters[prefix] = value
        return f"{prefix}{value:0{width}d}"


def pick_weighted(rng: random.Random, items: Sequence[T], weights: Sequence[float]) -> T:
    """Elige un elemento con pesos relativos usando el RNG recibido."""
    return rng.choices(list(items), weights=list(weights), k=1)[0]


def jitter_coords(
    rng: random.Random, geocell_id: str, radius: float = 0.035
) -> tuple[float, float]:
    """Desplaza levemente las coordenadas de una geocelda para simular direcciones."""
    geo = GEOCELL_BY_ID[geocell_id]
    lat = float(geo["latitude"]) + rng.uniform(-radius, radius)
    lon = float(geo["longitude"]) + rng.uniform(-radius, radius)
    return round(lat, 6), round(lon, 6)


def fmt_dt(value: datetime) -> str:
    """Formato ISO sencillo y estable para CSV."""
    return value.strftime("%Y-%m-%d %H:%M:%S")


def ensure_output_dirs(base_dir: Path) -> tuple[Path, Path]:
    """Crea y devuelve (raw, ground_truth) bajo el directorio base."""
    raw = base_dir / "raw"
    truth = base_dir / "ground_truth"
    raw.mkdir(parents=True, exist_ok=True)
    truth.mkdir(parents=True, exist_ok=True)
    return raw, truth


def frame_columns(table: str) -> list[str]:
    """Devuelve las columnas esperadas para una tabla pública o de verdad."""
    return PUBLIC_SCHEMAS.get(table) or TRUTH_SCHEMAS[table]
