"""Anonimización final de identificadores y mezcla de filas.

Los anillos se crean después de la población legítima, por lo que sus IDs
originales quedarían en un rango contiguo. Este módulo reemplaza todas las
claves por tokens aleatorios de 48 bits y baraja cada tabla con una semilla
independiente. Las relaciones se conservan mediante mapas por tipo de entidad.
"""

from __future__ import annotations

import random

import pandas as pd

# Columna de cada tabla -> tipo de entidad referenciada.
ID_COLUMN_ENTITY: dict[str, str] = {
    "person_id": "person",
    "owner_person_id": "person",
    "ref_person_id": "person",
    "business_id": "business",
    "address_id": "address",
    "home_address_id": "address",
    "commercial_address_id": "address",
    "declared_address_id": "address",
    "phone_id": "phone",
    "primary_phone_id": "phone",
    "ref_phone_id": "phone",
    "device_id": "device",
    "primary_device_id": "device",
    "application_id": "application",
    "reference_id": "reference",
    "coop_id": "coop",
    "geocell_id": "geocell",
    "application_geocell_id": "geocell",
    "home_geocell": "geocell",
    "ring_id": "ring",
}


def _is_empty(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    text = str(value)
    return text == "" or text.lower() in {"nan", "none"}


def _collect_values(
    frames: list[pd.DataFrame],
) -> dict[str, set[str]]:
    values: dict[str, set[str]] = {}
    for frame in frames:
        for column, entity in ID_COLUMN_ENTITY.items():
            if column not in frame.columns:
                continue
            for value in frame[column].dropna().unique():
                if not _is_empty(value):
                    values.setdefault(entity, set()).add(str(value))
    return values


def _build_mappings(
    values: dict[str, set[str]], rng: random.Random
) -> dict[str, dict[str, str]]:
    used: set[str] = set()
    mappings: dict[str, dict[str, str]] = {}
    for entity in sorted(values):
        mapping: dict[str, str] = {}
        for old_value in sorted(values[entity]):
            while True:
                new_value = f"{rng.getrandbits(48):012x}"
                if new_value not in used:
                    used.add(new_value)
                    break
            mapping[old_value] = new_value
        mappings[entity] = mapping
    return mappings


def _apply_mappings(
    frame: pd.DataFrame, mappings: dict[str, dict[str, str]]
) -> pd.DataFrame:
    result = frame.copy()
    for column, entity in ID_COLUMN_ENTITY.items():
        if column not in result.columns:
            continue
        mapping = mappings.get(entity, {})
        result[column] = result[column].map(
            lambda value: value if _is_empty(value) else mapping.get(str(value), value)
        )
    return result


def obfuscate_and_shuffle(
    tables: dict[str, pd.DataFrame],
    truth: pd.DataFrame,
    rings: pd.DataFrame,
    seed: int,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    """Reemplaza IDs por tokens opacos y baraja todas las tablas."""
    id_rng = random.Random(seed * 1_000_003 + 17)
    shuffle_rng = random.Random(seed * 7_919 + 13)
    frames = [*tables.values(), truth, rings]
    mappings = _build_mappings(_collect_values(frames), id_rng)

    def transform(frame: pd.DataFrame, *, shuffle: bool = True) -> pd.DataFrame:
        mapped = _apply_mappings(frame, mappings)
        if shuffle and len(mapped) > 1:
            order = list(range(len(mapped)))
            shuffle_rng.shuffle(order)
            mapped = mapped.iloc[order]
        return mapped.reset_index(drop=True)

    shuffled_tables = {name: transform(frame) for name, frame in tables.items()}
    shuffled_truth = transform(truth)
    shuffled_rings = transform(rings)
    return shuffled_tables, shuffled_truth, shuffled_rings
