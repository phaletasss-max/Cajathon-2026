"""Pruebas mínimas de la Fase 1: contrato, integridad y reproducibilidad."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd

from data.generator import generate_dataset
from data.rings import DIFFICULTY_CONFIG, RING_TYPES
from data.schema import FORBIDDEN_PUBLIC_TOKENS


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")


def test_generates_public_and_truth_tables(tmp_path: Path) -> None:
    paths = generate_dataset(n_legit=120, n_rings=5, seed=7, out_dir=tmp_path)

    for name in ["persons", "businesses", "applications", "references", "geocells"]:
        assert paths[name].exists(), name
    assert paths["ground_truth"].exists()
    assert paths["rings"].exists()

    persons = _read(paths["persons"])
    applications = _read(paths["applications"])
    truth = _read(paths["ground_truth"])
    rings = _read(paths["rings"])

    assert len(persons) >= 120
    assert len(applications) >= 120
    assert len(rings) == 5
    assert set(rings["ring_type"]) == set(RING_TYPES)
    assert len(truth) > 0
    assert set(truth["ring_type"]) == set(RING_TYPES)
    assert "100% datos sintéticos" in (tmp_path / "raw" / "dataset_meta.json").read_text(encoding="utf-8")


def test_public_tables_have_no_hidden_labels(tmp_path: Path) -> None:
    paths = generate_dataset(n_legit=80, n_rings=3, seed=11, out_dir=tmp_path)
    for table in ["persons", "businesses", "addresses", "phones", "devices", "applications", "references"]:
        columns = _read(paths[table]).columns
        assert not [
            column for column in columns
            if any(token in column.lower() for token in FORBIDDEN_PUBLIC_TOKENS)
        ], table


def test_referential_integrity(tmp_path: Path) -> None:
    paths = generate_dataset(n_legit=150, n_rings=5, seed=13, out_dir=tmp_path)
    persons = _read(paths["persons"])
    businesses = _read(paths["businesses"])
    addresses = _read(paths["addresses"])
    phones = _read(paths["phones"])
    devices = _read(paths["devices"])
    applications = _read(paths["applications"])
    references = _read(paths["references"])
    geocells = _read(paths["geocells"])
    truth = _read(paths["ground_truth"])

    def ids(frame: pd.DataFrame, column: str) -> set[str]:
        return set(frame[column])

    person_ids = ids(persons, "person_id")
    business_ids = ids(businesses, "business_id")
    address_ids = ids(addresses, "address_id")
    phone_ids = ids(phones, "phone_id")
    device_ids = ids(devices, "device_id")
    app_ids = ids(applications, "application_id")
    geocell_ids = ids(geocells, "geocell_id")

    assert len(person_ids) == len(persons)
    assert len(app_ids) == len(applications)
    assert set(applications["person_id"]) <= person_ids
    assert set(applications["declared_address_id"]) <= address_ids
    assert set(applications["application_geocell_id"]) <= geocell_ids
    assert set(applications["device_id"]) <= device_ids
    assert set(applications["phone_id"]) <= phone_ids
    assert set(applications["business_id"]) - {""} <= business_ids

    assert set(persons["home_address_id"]) <= address_ids
    assert set(persons["primary_phone_id"]) <= phone_ids
    assert set(persons["primary_device_id"]) <= device_ids
    assert set(businesses["owner_person_id"]) <= person_ids
    assert set(businesses["commercial_address_id"]) <= address_ids
    assert set(references["application_id"]) <= app_ids
    assert set(references["ref_person_id"]) <= person_ids
    assert set(references["ref_phone_id"]) <= phone_ids

    assert set(truth["application_id"]) <= app_ids
    assert set(truth["person_id"]) <= person_ids
    assert truth["application_id"].is_unique
    assert truth["ring_id"].nunique() == 5


def test_generation_is_deterministic(tmp_path: Path) -> None:
    first = generate_dataset(n_legit=90, n_rings=3, seed=99, out_dir=tmp_path / "a")
    second = generate_dataset(n_legit=90, n_rings=3, seed=99, out_dir=tmp_path / "b")

    for name in ["persons", "applications", "references", "ground_truth", "rings"]:
        left = hashlib.sha256(first[name].read_bytes()).hexdigest()
        right = hashlib.sha256(second[name].read_bytes()).hexdigest()
        assert left == right, name


def test_ring_ids_are_opaque_and_not_positionally_separable(tmp_path: Path) -> None:
    paths = generate_dataset(n_legit=300, n_rings=5, seed=21, out_dir=tmp_path)
    persons = _read(paths["persons"])
    applications = _read(paths["applications"])
    truth = _read(paths["ground_truth"])

    ring_people = set(truth["person_id"])
    legit_people = set(persons["person_id"]) - ring_people
    ring_apps = set(truth["application_id"])
    legit_apps = set(applications["application_id"]) - ring_apps

    for identifier in ring_people | legit_people | ring_apps | legit_apps:
        assert re.fullmatch(r"[0-9a-f]{12}", identifier), identifier
        assert not identifier.upper().startswith(("PER", "APP", "RING"))

    # Un prefijo compartido por todos los anillos delataría su origen.
    assert len({identifier[:2] for identifier in ring_people}) >= 10
    assert len({identifier[:2] for identifier in legit_people}) >= 50
    assert len({identifier[:2] for identifier in ring_apps}) >= 8
    assert len({identifier[:2] for identifier in legit_apps}) >= 50

    # Las filas también se barajan: la posición media del anillo debe ser central.
    person_position = {pid: index for index, pid in enumerate(persons["person_id"])}
    ring_positions = [person_position[pid] for pid in ring_people]
    mean_position = sum(ring_positions) / len(ring_positions) / len(persons)
    assert 0.20 <= mean_position <= 0.80

    app_position = {
        app_id: index for index, app_id in enumerate(applications["application_id"])
    }
    ring_app_positions = [app_position[app_id] for app_id in ring_apps]
    mean_app_position = sum(ring_app_positions) / len(ring_app_positions) / len(applications)
    assert 0.20 <= mean_app_position <= 0.80


def test_circular_ring_references_match_legit_distribution(tmp_path: Path) -> None:
    paths = generate_dataset(n_legit=500, n_rings=10, seed=33, out_dir=tmp_path)
    applications = _read(paths["applications"])
    references = _read(paths["references"])
    truth = _read(paths["ground_truth"])

    circular_apps = set(truth.loc[truth["ring_type"] == "circular_references", "application_id"])
    legit_apps = set(applications["application_id"]) - set(truth["application_id"])
    counts = references.groupby("application_id").size()
    circular_mean = counts.reindex(list(circular_apps)).dropna().mean()
    legit_mean = counts.reindex(list(legit_apps)).dropna().mean()

    assert 1.6 <= circular_mean <= 2.3
    assert abs(circular_mean - legit_mean) < 0.5
    ring_people = set(truth["person_id"])
    referenced_people = set(
        references.loc[references["application_id"].isin(circular_apps), "ref_person_id"]
    )
    assert referenced_people - ring_people, "el ciclo debe mezclarse con referencias legítimas"


def test_difficulty_is_persisted_and_changes_ring_noise(tmp_path: Path) -> None:
    easy = generate_dataset(
        n_legit=200, n_rings=5, seed=41, out_dir=tmp_path / "easy", difficulty="easy"
    )
    hard = generate_dataset(
        n_legit=200, n_rings=5, seed=41, out_dir=tmp_path / "hard", difficulty="hard"
    )
    easy_meta = json.loads(easy["run_meta"].read_text(encoding="utf-8"))
    hard_meta = json.loads(hard["run_meta"].read_text(encoding="utf-8"))
    easy_rings = _read(easy["rings"])

    assert easy_meta["difficulty"] == "easy"
    assert hard_meta["difficulty"] == "hard"
    assert hard_meta["difficulty_config"]["noise_rate"] > easy_meta["difficulty_config"]["noise_rate"]
    assert hard_meta["difficulty_config"]["burst_window_hours"] > easy_meta["difficulty_config"]["burst_window_hours"]
    assert set(easy_rings["cover_pattern"]) == {"none"}
    assert DIFFICULTY_CONFIG["hard"]["cover_probability"] > DIFFICULTY_CONFIG["medium"]["cover_probability"]


def test_dni_format_and_local_address_distribution(tmp_path: Path) -> None:
    paths = generate_dataset(n_legit=300, n_rings=5, seed=17, out_dir=tmp_path)
    persons = _read(paths["persons"])
    addresses = _read(paths["addresses"])
    geocells = _read(paths["geocells"])

    assert all(re.fullmatch(r"\d{8}", value) for value in persons["doc_number"])
    merged = addresses.merge(geocells, on="geocell_id", how="left")
    assert merged["department_x"].notna().all()
    assert (merged["department_x"] == "La Libertad").mean() >= 0.75


def test_low_prevalence_metadata(tmp_path: Path) -> None:
    paths = generate_dataset(n_legit=500, n_rings=5, seed=8, out_dir=tmp_path)
    run_meta = json.loads(paths["run_meta"].read_text(encoding="utf-8"))
    assert run_meta["n_rings"] == 5
    assert run_meta["prevalence_rings_per_1000_persons"] == 10.0
