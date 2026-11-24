"""Constructor del grafo bipartito y de la proyección entre solicitudes.

La unidad de evidencia es un atributo compartido. Para cada atributo se calcula
su frecuencia documental ``df`` sobre las entidades de la izquierda
(solicitudes + personas + negocios) y un IDF suavizado con tope por tipo.

Si ``df > K`` el atributo se marca como ``alta_multiplicidad``. En la
proyección no se generan todas las parejas: cada solicitud se conecta a un nodo
hub. Así el número de aristas crece de forma lineal y no cuadrática.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable, Mapping

import networkx as nx
import pandas as pd

from data.schema import PUBLIC_SCHEMAS
from graph.model import (
    GraphBuildResult,
    GraphConfig,
    attribute_weight,
    evidence_entry,
    hash_attribute,
)

TABLE_NAMES = (
    "applications",
    "persons",
    "businesses",
    "addresses",
    "phones",
    "devices",
    "references",
    "geocells",
)

NODE_DEFAULTS: dict[str, Any] = {
    "node_type": "",
    "label": "",
    "attribute_type": "",
    "value_hash": "",
    "weight": 0.0,
    "multiplicity": 0,
    "df_applications": 0,
    "high_multiplicity": False,
    "multiplicity_label": "",
    "created_at": "",
    "min_created_at": "",
    "max_created_at": "",
    "person_id": "",
    "business_id": "",
    "owner_person_id": "",
}

EDGE_DEFAULTS: dict[str, Any] = {
    "edge_type": "",
    "weight": 0.0,
    "attribute_type": "",
    "value_hash": "",
    "n_shared_attributes": 1,
    "high_multiplicity": False,
    "multiplicity_label": "",
    "evidence_json": "",
    "min_created_at": "",
    "max_created_at": "",
    "span_hours": 0.0,
}


@dataclass
class _AttributeState:
    """Acumulado de un atributo antes de calcular su IDF y sus aristas."""

    attribute_type: str
    raw_value: str
    value_hash: str
    entities: set[str] = field(default_factory=set)
    applications: set[str] = field(default_factory=set)
    min_dt: datetime | None = None
    max_dt: datetime | None = None
    df: int = 0
    weight: float = 0.0
    high_multiplicity: bool = False


@dataclass
class _PairState:
    """Evidencia acumulada para una pareja de solicitudes."""

    weight: float = 0.0
    evidence: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)
    min_dt: datetime | None = None
    max_dt: datetime | None = None

    def add(
        self,
        entry: dict[str, Any],
        first: datetime | None,
        second: datetime | None,
    ) -> None:
        self.weight += float(entry["weight"])
        self.evidence[(str(entry["type"]), str(entry["value_hash"]))] = entry
        for value in (first, second):
            if value is None:
                continue
            if self.min_dt is None or value < self.min_dt:
                self.min_dt = value
            if self.max_dt is None or value > self.max_dt:
                self.max_dt = value


def _clean_frame(name: str, frame: pd.DataFrame) -> pd.DataFrame:
    expected = PUBLIC_SCHEMAS[name]
    missing = [column for column in expected if column not in frame.columns]
    if missing:
        raise ValueError(f"Falta la columna {missing} en la tabla {name}")
    cleaned = frame.loc[:, expected].copy()
    for column in expected:
        cleaned[column] = cleaned[column].fillna("").astype(str).str.strip()
    return cleaned


def load_tables(raw_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Lee las tablas públicas de ``data/raw`` sin usar la verdad terreno."""
    base = Path(raw_dir)
    tables: dict[str, pd.DataFrame] = {}
    for name in TABLE_NAMES:
        path = base / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(f"No existe {path}")
        frame = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")
        tables[name] = _clean_frame(name, frame)
    return tables


def _parse_dt(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _iso(value: datetime | None) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S") if value is not None else ""


def _span_hours(first: datetime | None, second: datetime | None) -> float:
    if first is None or second is None:
        return 0.0
    return round(abs((second - first).total_seconds()) / 3600.0, 3)


def _window(values: Iterable[datetime | None]) -> tuple[datetime | None, datetime | None]:
    present = [value for value in values if value is not None]
    if not present:
        return None, None
    return min(present), max(present)


def _add_node(graph: nx.Graph, node_id: str, **attributes: Any) -> None:
    payload = dict(NODE_DEFAULTS)
    payload.update(attributes)
    graph.add_node(str(node_id), **payload)


def _add_edge(graph: nx.Graph, source: str, target: str, **attributes: Any) -> None:
    payload = dict(EDGE_DEFAULTS)
    payload.update(attributes)
    graph.add_edge(str(source), str(target), **payload)


def _attribute_label(
    state: _AttributeState,
    phone_meta: Mapping[str, Mapping[str, str]],
    device_meta: Mapping[str, Mapping[str, str]],
    address_meta: Mapping[str, Mapping[str, str]],
    geocell_meta: Mapping[str, Mapping[str, str]],
    person_name: Mapping[str, str],
) -> str:
    raw = state.raw_value
    if state.attribute_type == "phone":
        number = str(phone_meta.get(raw, {}).get("phone_number", ""))
        return f"Tel. ****{number[-4:]}" if number else f"Tel. {raw[:8]}"
    if state.attribute_type == "device":
        fingerprint = str(device_meta.get(raw, {}).get("device_fingerprint", ""))
        return f"Equipo {fingerprint[:10]}" if fingerprint else f"Equipo {raw[:8]}"
    if state.attribute_type == "address":
        address = address_meta.get(raw, {})
        street = str(address.get("street", ""))
        district = str(address.get("district", ""))
        return f"{street} ({district})" if street else f"Dirección {raw[:8]}"
    if state.attribute_type == "geocell":
        geocell = geocell_meta.get(raw, {})
        district = str(geocell.get("district", ""))
        province = str(geocell.get("province", ""))
        return f"{district} / {province}" if district else f"Geocelda {raw}"
    if state.attribute_type == "reference":
        return f"Referencia: {person_name.get(raw, raw[:8])}"
    return f"{state.attribute_type}:{raw[:8]}"


def build_graph(
    tables: Mapping[str, pd.DataFrame],
    config: GraphConfig | None = None,
) -> GraphBuildResult:
    """Construye las dos capas del grafo y devuelve tablas exportables."""
    started = time.perf_counter()
    config = config or GraphConfig()

    required = [name for name in TABLE_NAMES if name not in tables]
    if required:
        raise ValueError(f"Faltan tablas: {required}")
    frames = {name: _clean_frame(name, tables[name]) for name in TABLE_NAMES}

    applications = frames["applications"]
    persons = frames["persons"]
    businesses = frames["businesses"]
    addresses = frames["addresses"]
    phones = frames["phones"]
    devices = frames["devices"]
    references = frames["references"]
    geocells = frames["geocells"]

    app_records = applications.to_dict("records")
    person_records = persons.to_dict("records")
    business_records = businesses.to_dict("records")
    reference_records = references.to_dict("records")

    app_dt: dict[str, datetime | None] = {
        str(row["application_id"]): _parse_dt(row["created_at"]) for row in app_records
    }
    app_ids = set(app_dt)
    person_ids = {str(row["person_id"]) for row in person_records}
    business_ids = {str(row["business_id"]) for row in business_records}
    entity_ids = app_ids | person_ids | business_ids
    n_entities = len(entity_ids)

    apps_by_person: dict[str, list[str]] = defaultdict(list)
    apps_by_business: dict[str, list[str]] = defaultdict(list)
    for row in app_records:
        app_id = str(row["application_id"])
        apps_by_person[str(row["person_id"])].append(app_id)
        if str(row["business_id"]):
            apps_by_business[str(row["business_id"])].append(app_id)

    person_window = {
        person_id: _window(app_dt.get(app_id) for app_id in app_list)
        for person_id, app_list in apps_by_person.items()
    }
    business_window = {
        business_id: _window(app_dt.get(app_id) for app_id in app_list)
        for business_id, app_list in apps_by_business.items()
    }

    address_geocell = {
        str(row["address_id"]): str(row["geocell_id"]) for row in addresses.to_dict("records")
    }
    phone_meta = {str(row["phone_id"]): row for row in phones.to_dict("records")}
    device_meta = {str(row["device_id"]): row for row in devices.to_dict("records")}
    address_meta = {str(row["address_id"]): row for row in addresses.to_dict("records")}
    geocell_meta = {str(row["geocell_id"]): row for row in geocells.to_dict("records")}
    person_name = {str(row["person_id"]): str(row["full_name"]) for row in person_records}

    bipartite = nx.Graph()
    for row in app_records:
        app_id = str(row["application_id"])
        _add_node(
            bipartite,
            app_id,
            node_type="application",
            label=app_id,
            created_at=_iso(app_dt[app_id]),
            min_created_at=_iso(app_dt[app_id]),
            max_created_at=_iso(app_dt[app_id]),
            person_id=str(row["person_id"]),
            business_id=str(row["business_id"]),
        )
    for row in person_records:
        person_id = str(row["person_id"])
        first, last = person_window.get(person_id, (None, None))
        _add_node(
            bipartite,
            person_id,
            node_type="person",
            label=str(row["full_name"]) or person_id,
            created_at=str(row["created_at"]),
            min_created_at=_iso(first),
            max_created_at=_iso(last),
            person_id=person_id,
        )
    for row in business_records:
        business_id = str(row["business_id"])
        first, last = business_window.get(business_id, (None, None))
        _add_node(
            bipartite,
            business_id,
            node_type="business",
            label=str(row["business_name"]) or business_id,
            created_at=str(row["created_at"]),
            min_created_at=_iso(first),
            max_created_at=_iso(last),
            business_id=business_id,
            owner_person_id=str(row["owner_person_id"]),
        )

    attributes: dict[tuple[str, str], _AttributeState] = {}

    def add_attribute(
        entity_id: str,
        attribute_type: str,
        raw_value: object,
        application_id: str | None = None,
    ) -> None:
        value = str(raw_value or "").strip()
        if not value:
            return
        key = (attribute_type, value)
        state = attributes.get(key)
        if state is None:
            state = _AttributeState(
                attribute_type=attribute_type,
                raw_value=value,
                value_hash=hash_attribute(attribute_type, value, config.salt),
            )
            attributes[key] = state
        state.entities.add(entity_id)
        if application_id is not None:
            state.applications.add(application_id)
            moment = app_dt.get(application_id)
            if moment is not None:
                if state.min_dt is None or moment < state.min_dt:
                    state.min_dt = moment
                if state.max_dt is None or moment > state.max_dt:
                    state.max_dt = moment

    for row in app_records:
        app_id = str(row["application_id"])
        add_attribute(app_id, "phone", row["phone_id"], app_id)
        add_attribute(app_id, "device", row["device_id"], app_id)
        add_attribute(app_id, "address", row["declared_address_id"], app_id)
        add_attribute(app_id, "geocell", row["application_geocell_id"], app_id)

    for row in person_records:
        person_id = str(row["person_id"])
        add_attribute(person_id, "phone", row["primary_phone_id"])
        add_attribute(person_id, "device", row["primary_device_id"])
        add_attribute(person_id, "address", row["home_address_id"])
        add_attribute(
            person_id, "geocell", address_geocell.get(str(row["home_address_id"]))
        )

    for row in business_records:
        business_id = str(row["business_id"])
        add_attribute(business_id, "address", row["commercial_address_id"])
        add_attribute(
            business_id,
            "geocell",
            address_geocell.get(str(row["commercial_address_id"])),
        )

    for row in reference_records:
        app_id = str(row["application_id"])
        ref_person_id = str(row["ref_person_id"])
        add_attribute(app_id, "reference", ref_person_id, app_id)
        add_attribute(ref_person_id, "reference", ref_person_id)

    def entity_window(entity_id: str) -> tuple[datetime | None, datetime | None]:
        if entity_id in app_dt:
            return app_dt[entity_id], app_dt[entity_id]
        if entity_id in person_window:
            return person_window[entity_id]
        if entity_id in business_window:
            return business_window[entity_id]
        return None, None

    for state in attributes.values():
        state.df = len(state.entities)
        state.weight = attribute_weight(
            state.df, n_entities, state.attribute_type, config
        )
        state.high_multiplicity = state.df > config.max_multiplicity
        attribute_node_id = (
            f"attr:{state.attribute_type}:{state.value_hash}"
        )
        _add_node(
            bipartite,
            attribute_node_id,
            node_type="attribute",
            label=_attribute_label(
                state,
                phone_meta,
                device_meta,
                address_meta,
                geocell_meta,
                person_name,
            ),
            attribute_type=state.attribute_type,
            value_hash=state.value_hash,
            weight=state.weight,
            multiplicity=state.df,
            df_applications=len(state.applications),
            high_multiplicity=state.high_multiplicity,
            multiplicity_label=(
                "alta_multiplicidad" if state.high_multiplicity else "normal"
            ),
            min_created_at=_iso(state.min_dt),
            max_created_at=_iso(state.max_dt),
        )
        entry = evidence_entry(
            state.attribute_type, state.value_hash, state.weight, state.df
        )
        evidence_json = json.dumps([entry], ensure_ascii=False)
        for entity_id in sorted(state.entities):
            first, last = entity_window(entity_id)
            _add_edge(
                bipartite,
                entity_id,
                attribute_node_id,
                edge_type="entity_attribute",
                weight=state.weight,
                attribute_type=state.attribute_type,
                value_hash=state.value_hash,
                n_shared_attributes=1,
                high_multiplicity=state.high_multiplicity,
                multiplicity_label=(
                    "alta_multiplicidad" if state.high_multiplicity else "normal"
                ),
                evidence_json=evidence_json,
                min_created_at=_iso(first),
                max_created_at=_iso(last),
                span_hours=_span_hours(first, last),
            )

    projection = nx.Graph()
    for row in app_records:
        app_id = str(row["application_id"])
        _add_node(
            projection,
            app_id,
            node_type="application",
            label=app_id,
            created_at=_iso(app_dt[app_id]),
            min_created_at=_iso(app_dt[app_id]),
            max_created_at=_iso(app_dt[app_id]),
            person_id=str(row["person_id"]),
            business_id=str(row["business_id"]),
        )

    pair_states: dict[tuple[str, str], _PairState] = {}
    hub_edges = 0
    application_edges = 0

    for state in attributes.values():
        app_list = sorted(state.applications)
        if len(app_list) < 2:
            continue
        entry = evidence_entry(
            state.attribute_type, state.value_hash, state.weight, state.df
        )
        if state.high_multiplicity:
            if not config.include_hubs:
                continue
            hub_id = f"hub:{state.attribute_type}:{state.value_hash}"
            _add_node(
                projection,
                hub_id,
                node_type="attribute_hub",
                label=f"Hub {state.attribute_type}",
                attribute_type=state.attribute_type,
                value_hash=state.value_hash,
                weight=state.weight,
                multiplicity=state.df,
                df_applications=len(state.applications),
                high_multiplicity=True,
                multiplicity_label="alta_multiplicidad",
                min_created_at=_iso(state.min_dt),
                max_created_at=_iso(state.max_dt),
            )
            evidence_json = json.dumps([entry], ensure_ascii=False)
            for app_id in app_list:
                moment = app_dt.get(app_id)
                _add_edge(
                    projection,
                    app_id,
                    hub_id,
                    edge_type="high_multiplicity_hub",
                    weight=state.weight,
                    attribute_type=state.attribute_type,
                    value_hash=state.value_hash,
                    n_shared_attributes=1,
                    high_multiplicity=True,
                    multiplicity_label="alta_multiplicidad",
                    evidence_json=evidence_json,
                    min_created_at=_iso(moment),
                    max_created_at=_iso(moment),
                    span_hours=0.0,
                )
                hub_edges += 1
            continue

        for first_app, second_app in combinations(app_list, 2):
            key = (first_app, second_app)
            pair = pair_states.get(key)
            if pair is None:
                pair = _PairState()
                pair_states[key] = pair
            pair.add(entry, app_dt.get(first_app), app_dt.get(second_app))

    for (first_app, second_app), pair in pair_states.items():
        _add_edge(
            projection,
            first_app,
            second_app,
            edge_type="shared_attribute",
            weight=round(pair.weight, 6),
            attribute_type="multiple",
            n_shared_attributes=len(pair.evidence),
            high_multiplicity=False,
            multiplicity_label="normal",
            evidence_json=json.dumps(
                list(pair.evidence.values()), ensure_ascii=False
            ),
            min_created_at=_iso(pair.min_dt),
            max_created_at=_iso(pair.max_dt),
            span_hours=_span_hours(pair.min_dt, pair.max_dt),
        )
        application_edges += 1

    edge_rows: list[dict[str, Any]] = []
    for layer, graph in (("bipartite", bipartite), ("projection", projection)):
        for source, target, edge_attrs in graph.edges(data=True):
            edge_rows.append({
                "graph_layer": layer,
                "source": source,
                "target": target,
                **edge_attrs,
            })
    edges = pd.DataFrame(edge_rows)
    edges = edges.reindex(
        columns=["edge_id", "graph_layer", "source", "target", *EDGE_DEFAULTS]
    )
    edges = edges.sort_values(
        ["graph_layer", "source", "target"], kind="stable"
    ).reset_index(drop=True)
    edges["edge_id"] = [f"E{index:08d}" for index in range(len(edges))]

    node_rows: list[dict[str, Any]] = []
    for layer, graph in (("bipartite", bipartite), ("projection", projection)):
        for node_id, node_attrs in graph.nodes(data=True):
            node_rows.append({
                "graph_layer": layer,
                "node_id": node_id,
                **node_attrs,
            })
    nodes = pd.DataFrame(node_rows)
    nodes = nodes.reindex(columns=["graph_layer", "node_id", *NODE_DEFAULTS])
    nodes = nodes.sort_values(
        ["graph_layer", "node_type", "node_id"], kind="stable"
    ).reset_index(drop=True)

    attribute_rows: list[dict[str, Any]] = []
    for state in attributes.values():
        attribute_rows.append({
            "attribute_key": f"attr:{state.attribute_type}:{state.value_hash}",
            "attribute_type": state.attribute_type,
            "value_hash": state.value_hash,
            "multiplicity": state.df,
            "df_applications": len(state.applications),
            "weight": state.weight,
            "high_multiplicity": state.high_multiplicity,
            "multiplicity_label": (
                "alta_multiplicidad" if state.high_multiplicity else "normal"
            ),
            "min_created_at": _iso(state.min_dt),
            "max_created_at": _iso(state.max_dt),
            "hub_node_id": (
                f"hub:{state.attribute_type}:{state.value_hash}"
                if state.high_multiplicity
                else ""
            ),
        })
    attribute_frame = pd.DataFrame(
        attribute_rows,
        columns=[
            "attribute_key",
            "attribute_type",
            "value_hash",
            "multiplicity",
            "df_applications",
            "weight",
            "high_multiplicity",
            "multiplicity_label",
            "min_created_at",
            "max_created_at",
            "hub_node_id",
        ],
    ).sort_values(
        ["attribute_type", "weight", "value_hash"], ascending=[True, False, True]
    ).reset_index(drop=True)

    elapsed = round(time.perf_counter() - started, 4)
    stats = {
        "n_applications": len(app_records),
        "n_persons": len(person_records),
        "n_businesses": len(business_records),
        "n_entities": n_entities,
        "n_attributes": len(attributes),
        "n_high_multiplicity_attributes": sum(
            1 for state in attributes.values() if state.high_multiplicity
        ),
        "n_bipartite_nodes": bipartite.number_of_nodes(),
        "n_bipartite_edges": bipartite.number_of_edges(),
        "n_projection_nodes": projection.number_of_nodes(),
        "n_projection_edges": projection.number_of_edges(),
        "n_projection_hub_edges": hub_edges,
        "n_projection_application_edges": application_edges,
        "max_multiplicity": config.max_multiplicity,
        "elapsed_seconds": elapsed,
    }

    return GraphBuildResult(
        bipartite=bipartite,
        projection=projection,
        edges=edges,
        nodes=nodes,
        attributes=attribute_frame,
        config=config,
        n_applications=len(app_records),
        n_entities=n_entities,
        elapsed_seconds=elapsed,
        stats=stats,
    )


def build_graph_from_dir(
    input_dir: str | Path,
    config: GraphConfig | None = None,
) -> GraphBuildResult:
    """Construye el grafo desde un directorio con CSVs públicos."""
    root = Path(input_dir)
    raw_dir = root / "raw" if (root / "raw" / "applications.csv").exists() else root
    return build_graph(load_tables(raw_dir), config)


def main(argv: list[str] | None = None) -> int:
    from graph.export import export_graph

    parser = argparse.ArgumentParser(
        description="Construye el grafo bipartito y la proyección de solicitudes"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw"),
        help="directorio con los CSV públicos o la raíz del dataset",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/graph"),
        help="directorio de salida",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=25,
        help="umbral K de multiplicidad; un atributo con df > K se vuelve hub",
    )
    parser.add_argument(
        "--salt",
        default="rie02-fase2",
        help="sal para hashear los valores de evidencia",
    )
    args = parser.parse_args(argv)

    config = GraphConfig(max_multiplicity=args.k, salt=args.salt)
    result = build_graph_from_dir(args.input, config)
    paths = export_graph(result, args.output)
    summary = {
        "stats": result.stats,
        "outputs": {name: str(path) for name, path in paths.items()},
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
