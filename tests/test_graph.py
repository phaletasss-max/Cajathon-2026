"""Pruebas de la Fase 2: pesos IDF, hubs, evidencia y exportación."""

from __future__ import annotations

import json
import pickle
import time
from datetime import datetime, timedelta
from itertools import combinations
from pathlib import Path

import networkx as nx
import pandas as pd
import pytest

from data.generator import generate_dataset
from data.schema import PUBLIC_SCHEMAS
from graph.builder import build_graph, load_tables
from graph.export import export_graph
from graph.model import GraphConfig, attribute_weight


def _row(table: str, **values: object) -> dict[str, str]:
    return {
        column: str(values.get(column, ""))
        for column in PUBLIC_SCHEMAS[table]
    }


def _micro_tables() -> dict[str, pd.DataFrame]:
    """42 solicitudes: 2 comparten teléfono y 40 comparten dirección."""
    base = datetime(2024, 1, 1, 8, 0, 0)
    persons: list[dict[str, str]] = []
    phones: list[dict[str, str]] = []
    devices: list[dict[str, str]] = []
    addresses: list[dict[str, str]] = []
    applications: list[dict[str, str]] = []
    shared_phone_added = False

    for index in range(42):
        person_id = f"P{index:03d}"
        app_id = f"A{index:03d}"
        if index < 2:
            phone_id = "PH-SHARED"
            address_id = f"AD-{index:03d}"
        else:
            phone_id = f"PH-{index:03d}"
            address_id = "AD-SHARED"
        device_id = f"DV-{index:03d}"

        if phone_id == "PH-SHARED":
            if not shared_phone_added:
                phones.append(_row(
                    "phones",
                    phone_id=phone_id,
                    phone_number="999000111",
                    line_type="móvil",
                    owner_person_id="P000",
                    activation_date="2022-01-01 00:00:00",
                ))
                shared_phone_added = True
        else:
            phones.append(_row(
                "phones",
                phone_id=phone_id,
                phone_number=f"999{index:06d}",
                line_type="móvil",
                owner_person_id=person_id,
                activation_date="2022-01-01 00:00:00",
            ))

        devices.append(_row(
            "devices",
            device_id=device_id,
            device_fingerprint=f"FP-{index:012d}",
            device_type="smartphone",
            owner_person_id=person_id,
            first_seen="2022-01-01 00:00:00",
        ))

        if index < 2:
            addresses.append(_row(
                "addresses",
                address_id=address_id,
                address_type="vivienda",
                street=f"Calle {index} 100",
                district="Trujillo",
                province="Trujillo",
                department="La Libertad",
                geocell_id="GEO-T1",
                latitude="-8.11",
                longitude="-79.03",
            ))

        persons.append(_row(
            "persons",
            person_id=person_id,
            full_name=f"Persona {index}",
            doc_type="DNI",
            doc_number=f"{index:08d}",
            birth_date="1990-01-01",
            gender="F",
            home_address_id=address_id,
            primary_phone_id=phone_id,
            primary_device_id=device_id,
            occupation="comerciante",
            monthly_income_pen="2000",
            coop_id="",
            created_at="2020-01-01 00:00:00",
        ))

        applications.append(_row(
            "applications",
            application_id=app_id,
            person_id=person_id,
            business_id="",
            product="microcrédito",
            amount_pen="5000",
            term_months="12",
            channel="app",
            purpose="capital_trabajo",
            created_at=(base + timedelta(hours=3 * index)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            declared_address_id=address_id,
            application_geocell_id="GEO-T1",
            device_id=device_id,
            phone_id=phone_id,
            coop_id="",
            status="recibida",
        ))

    addresses.append(_row(
        "addresses",
        address_id="AD-SHARED",
        address_type="vivienda",
        street="Calle Compartida 200",
        district="Trujillo",
        province="Trujillo",
        department="La Libertad",
        geocell_id="GEO-T1",
        latitude="-8.11",
        longitude="-79.03",
    ))

    return {
        "applications": pd.DataFrame(applications, columns=PUBLIC_SCHEMAS["applications"]),
        "persons": pd.DataFrame(persons, columns=PUBLIC_SCHEMAS["persons"]),
        "businesses": pd.DataFrame(columns=PUBLIC_SCHEMAS["businesses"]),
        "addresses": pd.DataFrame(addresses, columns=PUBLIC_SCHEMAS["addresses"]),
        "phones": pd.DataFrame(phones, columns=PUBLIC_SCHEMAS["phones"]),
        "devices": pd.DataFrame(devices, columns=PUBLIC_SCHEMAS["devices"]),
        "references": pd.DataFrame(columns=PUBLIC_SCHEMAS["references"]),
        "geocells": pd.DataFrame(
            [_row(
                "geocells",
                geocell_id="GEO-T1",
                department="La Libertad",
                province="Trujillo",
                district="Trujillo",
                latitude="-8.11",
                longitude="-79.03",
                urban_rural="urbano",
            )],
            columns=PUBLIC_SCHEMAS["geocells"],
        ),
    }


@pytest.fixture(scope="module")
def micro_graph():
    return build_graph(_micro_tables(), GraphConfig(max_multiplicity=25))


def test_shared_phone_weighs_more_than_high_multiplicity_address(micro_graph) -> None:
    attributes = micro_graph.attributes
    phone = attributes[
        (attributes["attribute_type"] == "phone")
        & (attributes["multiplicity"] == 4)
    ].iloc[0]
    address = attributes[
        (attributes["attribute_type"] == "address")
        & (attributes["multiplicity"] == 80)
    ].iloc[0]

    assert bool(phone["high_multiplicity"]) is False
    assert bool(address["high_multiplicity"]) is True
    assert phone["multiplicity_label"] == "normal"
    assert address["multiplicity_label"] == "alta_multiplicidad"
    assert float(phone["weight"]) > float(address["weight"])
    assert float(phone["weight"]) == pytest.approx(
        attribute_weight(4, 84, "phone", micro_graph.config)
    )
    assert float(phone["weight"]) <= micro_graph.config.weight_caps["phone"]
    assert float(address["weight"]) <= micro_graph.config.weight_caps["address"]

    projection = micro_graph.projection
    assert projection.has_edge("A000", "A001")
    edge = projection["A000"]["A001"]
    assert edge["edge_type"] == "shared_attribute"
    assert edge["weight"] == pytest.approx(float(phone["weight"]))
    assert edge["n_shared_attributes"] == 1
    assert edge["min_created_at"] == "2024-01-01 08:00:00"
    assert edge["max_created_at"] == "2024-01-01 11:00:00"
    assert edge["span_hours"] == 3.0

    evidence = json.loads(edge["evidence_json"])
    assert evidence[0]["type"] == "phone"
    assert evidence[0]["value_hash"] != "PH-SHARED"
    assert len(evidence[0]["value_hash"]) == 16
    assert "PH-SHARED" not in edge["evidence_json"]

    hub_id = str(address["hub_node_id"])
    assert hub_id.startswith("hub:address:")
    assert hub_id in projection
    address_apps = [f"A{index:03d}" for index in range(2, 42)]
    for app_id in address_apps:
        assert projection.has_edge(app_id, hub_id)
    for first, second in combinations(address_apps, 2):
        assert not projection.has_edge(first, second)
    assert projection["A002"][hub_id]["edge_type"] == "high_multiplicity_hub"
    assert projection["A002"][hub_id]["high_multiplicity"] is True


def test_k_is_configurable_and_changes_hub_behavior() -> None:
    result = build_graph(_micro_tables(), GraphConfig(max_multiplicity=100))
    address = result.attributes[
        (result.attributes["attribute_type"] == "address")
        & (result.attributes["multiplicity"] == 80)
    ].iloc[0]

    assert bool(address["high_multiplicity"]) is False
    assert address["multiplicity_label"] == "normal"
    assert address["hub_node_id"] == ""
    edge = result.projection["A002"]["A003"]
    evidence = json.loads(edge["evidence_json"])
    assert any(item["type"] == "address" for item in evidence)


def test_graph_exports_are_reusable(micro_graph, tmp_path: Path) -> None:
    paths = export_graph(micro_graph, tmp_path / "graph")

    for name in [
        "bipartite_graphml",
        "projection_graphml",
        "pickle",
        "edges_csv",
        "nodes_csv",
        "attributes_csv",
        "meta",
    ]:
        assert paths[name].exists(), name

    bipartite = nx.read_graphml(paths["bipartite_graphml"])
    projection = nx.read_graphml(paths["projection_graphml"])
    assert bipartite.number_of_nodes() == micro_graph.bipartite.number_of_nodes()
    assert bipartite.number_of_edges() == micro_graph.bipartite.number_of_edges()
    assert projection.number_of_nodes() == micro_graph.projection.number_of_nodes()
    assert projection.number_of_edges() == micro_graph.projection.number_of_edges()
    assert bipartite.nodes["A000"]["node_type"] == "application"

    with paths["pickle"].open("rb") as handle:
        payload = pickle.load(handle)
    assert payload["schema_version"] == "2.0"
    assert "bipartite" in payload and "projection" in payload

    edges = pd.read_csv(paths["edges_csv"], keep_default_na=False)
    assert set(edges["graph_layer"]) == {"bipartite", "projection"}
    assert "evidence_json" in edges.columns
    meta = json.loads(paths["meta"].read_text(encoding="utf-8"))
    assert meta["counts"]["applications"] == 42
    assert meta["counts"]["attributes"] > 0


def test_build_time_with_5000_applications(tmp_path: Path) -> None:
    generate_dataset(
        n_legit=5000,
        n_rings=25,
        seed=42,
        out_dir=tmp_path,
        difficulty="medium",
    )
    tables = load_tables(tmp_path / "raw")

    started = time.perf_counter()
    result = build_graph(tables)
    elapsed = time.perf_counter() - started

    assert result.n_applications >= 5000
    assert result.projection.number_of_edges() > 0
    assert elapsed < 30.0, f"construcción demasiado lenta: {elapsed:.2f}s"

    high = result.attributes[result.attributes["high_multiplicity"]]
    assert len(high) > 0
    sample = high.iloc[0]
    hub_edges = result.edges[
        (result.edges["edge_type"] == "high_multiplicity_hub")
        & (result.edges["value_hash"] == sample["value_hash"])
    ]
    assert len(hub_edges) == int(sample["df_applications"])
