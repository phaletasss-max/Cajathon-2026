"""Inyección de anillos de fraude sintéticos con cinco modalidades.

Cada anillo crea personas, dispositivos, teléfonos, direcciones y solicitudes
nuevas. Las etiquetas se guardan únicamente en ``data/ground_truth`` y nunca se
añaden a las tablas públicas. La dificultad controla ruido, camuflaje y
separación temporal de las ráfagas.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import pandas as pd

from data.names import (
    business_name,
    first_name,
    street_address,
    surname as random_surname,
)
from data.population import OCCUPATIONS, Population
from data.schema import (
    CITY_WEIGHTS,
    FAR_GEOCELLS,
    GEOCELL_BY_ID,
    PUBLIC_SCHEMAS,
    TRUTH_SCHEMAS,
    fmt_dt,
    jitter_coords,
    pick_weighted,
)

RING_TYPES = [
    "device_farm",
    "rotating_phone",
    "circular_references",
    "application_burst",
    "impossible_locations",
]

DIFFICULTY_CONFIG: dict[str, dict[str, float | int]] = {
    "easy": {
        "cover_probability": 0.0,
        "noise_rate": 0.0,
        "burst_window_hours": 36,
        "burst_noise_rate": 0.0,
        "cycle_noise_rate": 0.0,
    },
    "medium": {
        "cover_probability": 0.24,
        "noise_rate": 0.0,
        "burst_window_hours": 72,
        "burst_noise_rate": 0.0,
        "cycle_noise_rate": 0.0,
    },
    "hard": {
        "cover_probability": 0.75,
        "noise_rate": 0.25,
        "burst_window_hours": 168,
        "burst_noise_rate": 0.25,
        "cycle_noise_rate": 0.20,
    },
}


@dataclass
class InjectionResult:
    """Filas nuevas inyectadas y verdad terreno asociada."""

    persons: pd.DataFrame
    businesses: pd.DataFrame
    addresses: pd.DataFrame
    phones: pd.DataFrame
    devices: pd.DataFrame
    applications: pd.DataFrame
    references: pd.DataFrame
    truth: pd.DataFrame
    rings: pd.DataFrame


class _RingBuilder:
    """Constructor interno con contadores y utilidades para todos los anillos."""

    def __init__(self, population: Population, difficulty: str) -> None:
        if difficulty not in DIFFICULTY_CONFIG:
            raise ValueError(f"Dificultad inválida: {difficulty}")
        self.pop = population
        self.rng = population.rng
        self.ids = population.ids
        self.difficulty = difficulty
        self.config = DIFFICULTY_CONFIG[difficulty]
        self.person_rows: list[dict[str, object]] = []
        self.business_rows: list[dict[str, object]] = []
        self.address_rows: list[dict[str, object]] = []
        self.phone_rows: list[dict[str, object]] = []
        self.device_rows: list[dict[str, object]] = []
        self.app_rows: list[dict[str, object]] = []
        self.ref_rows: list[dict[str, object]] = []
        self.truth_rows: list[dict[str, object]] = []
        self.ring_rows: list[dict[str, object]] = []
        self.people: dict[str, dict[str, object]] = {}
        self.address_geocell = dict(
            zip(population.addresses["address_id"], population.addresses["geocell_id"])
        )
        self.market_choices = list(population.market_addresses.values())
        self.legit_ids = [str(value) for value in population.persons["person_id"]]
        self.legit_by_geocell: dict[str, list[str]] = {}
        for person_id, geocell_id in population.home_geocell.items():
            self.legit_by_geocell.setdefault(geocell_id, []).append(person_id)

    # --- Fábricas de entidades ------------------------------------------------
    def _add_address(
        self, geocell_id: str, address_type: str = "vivienda", street: str | None = None
    ) -> str:
        address_id = self.ids.next("ADR")
        lat, lon = jitter_coords(self.rng, geocell_id)
        geo = GEOCELL_BY_ID[geocell_id]
        self.address_rows.append({
            "address_id": address_id,
            "address_type": address_type,
            "street": street or street_address(self.rng, geocell_id),
            "district": geo["district"],
            "province": geo["province"],
            "department": geo["department"],
            "geocell_id": geocell_id,
            "latitude": lat,
            "longitude": lon,
        })
        self.address_geocell[address_id] = geocell_id
        return address_id

    def _add_phone(self) -> str:
        phone_id = self.ids.next("PHN")
        while True:
            number = f"9{self.rng.randint(0, 99_999_999):08d}"
            if number not in self.pop.used_phones:
                self.pop.used_phones.add(number)
                break
        self.phone_rows.append({
            "phone_id": phone_id,
            "phone_number": number,
            "line_type": "móvil",
            "owner_person_id": None,
            "activation_date": fmt_dt(datetime(2016, 1, 1) + timedelta(days=self.rng.randrange(0, 3200))),
        })
        return phone_id

    def _add_device(self, device_type: str = "smartphone") -> str:
        device_id = self.ids.next("DEV")
        self.device_rows.append({
            "device_id": device_id,
            "device_fingerprint": f"FP-{self.rng.getrandbits(48):012x}",
            "device_type": device_type,
            "owner_person_id": None,
            "first_seen": fmt_dt(datetime(2017, 1, 1) + timedelta(days=self.rng.randrange(0, 2900))),
        })
        return device_id

    def _unique_doc(self) -> str:
        while True:
            number = f"{self.rng.randint(0, 99_999_999):08d}"
            if number not in self.pop.used_docs:
                self.pop.used_docs.add(number)
                return number

    def _add_person(
        self, geocell_id: str, home_address_id: str, phone_id: str, device_id: str
    ) -> str:
        person_id = self.ids.next("PER")
        gender = self.rng.choice(["F", "M"])
        first = first_name(self.rng, gender)
        last = random_surname(self.rng)
        self.person_rows.append({
            "person_id": person_id,
            "full_name": f"{first} {last}",
            "doc_type": "DNI",
            "doc_number": self._unique_doc(),
            "birth_date": (date(1970, 1, 1) + timedelta(days=self.rng.randrange(0, 33 * 365))).isoformat(),
            "gender": gender,
            "home_address_id": home_address_id,
            "primary_phone_id": phone_id,
            "primary_device_id": device_id,
            "occupation": self.rng.choice(OCCUPATIONS),
            "monthly_income_pen": max(
                900, min(25_000, int(round(self.rng.lognormvariate(7.95, 0.55), -2)))
            ),
            "coop_id": None,
            "created_at": fmt_dt(datetime(2017, 1, 1) + timedelta(days=self.rng.randrange(0, 2550))),
        })
        self.people[person_id] = {
            "home_address_id": home_address_id,
            "phone_id": phone_id,
            "device_id": device_id,
            "geocell_id": geocell_id,
            "business_id": None,
            "surname": last,
        }
        return person_id

    def _add_business(self, person_id: str, address_id: str | None = None) -> str:
        business_id = self.ids.next("BUS")
        sector = self.rng.choice(["comercio", "servicios", "manufactura", "transporte"])
        self.business_rows.append({
            "business_id": business_id,
            "owner_person_id": person_id,
            "business_name": business_name(
                self.rng, sector, str(self.people[person_id]["surname"])
            ),
            "sector": sector,
            "commercial_address_id": address_id or self.people[person_id]["home_address_id"],
            "monthly_sales_pen": self.rng.randint(2500, 30_000),
            "created_at": fmt_dt(datetime(2020, 1, 1) + timedelta(days=self.rng.randrange(0, 1400))),
        })
        self.people[person_id]["business_id"] = business_id
        return business_id

    def _add_application(
        self,
        person_id: str,
        created_at: datetime,
        *,
        geocell_id: str | None = None,
        declared_address_id: str | None = None,
        business_id: str | None = None,
        amount: float | None = None,
        product: str = "microcrédito",
        channel: str | None = None,
    ) -> str:
        info = self.people[person_id]
        application_id = self.ids.next("APP")
        self.app_rows.append({
            "application_id": application_id,
            "person_id": person_id,
            "business_id": business_id,
            "product": product,
            "amount_pen": amount or max(1000, int(round(self.rng.uniform(4000, 18_000), -2))),
            "term_months": self.rng.choice([6, 12, 18, 24]),
            "channel": channel or self.rng.choice(["app", "web", "agencia", "asesor"]),
            "purpose": "capital_trabajo",
            "created_at": fmt_dt(created_at),
            "declared_address_id": declared_address_id or info["home_address_id"],
            "application_geocell_id": geocell_id or info["geocell_id"],
            "device_id": info["device_id"],
            "phone_id": info["phone_id"],
            "coop_id": None,
            "status": "recibida",
        })
        return application_id

    def _add_reference(
        self, application_id: str, ref_person_id: str, created_at: datetime,
        relationship: str = "socio",
    ) -> None:
        ring_person = self.people.get(ref_person_id, {})
        phone_id = ring_person.get("phone_id") or self.pop.phone_by_person.get(ref_person_id)
        if not phone_id:
            return
        self.ref_rows.append({
            "reference_id": self.ids.next("REF"),
            "application_id": application_id,
            "ref_person_id": ref_person_id,
            "relationship": relationship,
            "ref_phone_id": phone_id,
            "created_at": fmt_dt(created_at),
        })

    def _mark(self, app_id: str, person_id: str, ring_id: str, ring_type: str,
              cover: str, ring_size: int) -> None:
        self.truth_rows.append({
            "application_id": app_id,
            "person_id": person_id,
            "ring_id": ring_id,
            "ring_type": ring_type,
            "cover_pattern": cover,
            "ring_size": ring_size,
        })

    # --- Utilidades de tiempo, dificultad y cobertura ------------------------
    def _city(self) -> str:
        return pick_weighted(self.rng, list(CITY_WEIGHTS), list(CITY_WEIGHTS.values()))

    def _random_dt(self) -> datetime:
        return datetime(2024, 1, 1) + timedelta(seconds=self.rng.randrange(547 * 86400))

    def _cover_address(self, cover: str) -> str | None:
        if cover != "market_cover" or not self.market_choices:
            return None
        return str(self.rng.choice(self.market_choices))

    def _amount(self, base: int, spread: int = 1500) -> int:
        return max(1000, base + self.rng.randint(-spread, spread))

    def _noise_indices(self, size: int, rate: float | None = None) -> set[int]:
        effective_rate = float(self.config["noise_rate"] if rate is None else rate)
        count = int(round(size * effective_rate))
        return set(self.rng.sample(range(size), count)) if count else set()

    def _legit_reference(
        self, home_geocell: str, exclude: set[str]
    ) -> tuple[str, str]:
        candidates = [
            person_id for person_id in self.legit_by_geocell.get(home_geocell, [])
            if person_id not in exclude
        ]
        relationship = "vecino"
        if not candidates:
            candidates = [person_id for person_id in self.legit_ids if person_id not in exclude]
            relationship = "referencia_personal"
        return self.rng.choice(candidates), relationship

    def _ring_refs(self, apps: list[tuple[str, str, datetime]], prob: float) -> None:
        for index, (app_id, _person_id, created_at) in enumerate(apps):
            if len(apps) > 1 and self.rng.random() < prob:
                next_person = apps[(index + 1) % len(apps)][1]
                self._add_reference(app_id, next_person, created_at - timedelta(days=2))

    # --- Modalidades ----------------------------------------------------------
    def _device_farm(self, ring_id: str, cover: str) -> str:
        size = self.rng.randint(6, 12)
        cover_address = self._cover_address(cover)
        city = self.address_geocell[cover_address] if cover_address else self._city()
        device_pool = [self._add_device() for _ in range(self.rng.randint(2, 4))]
        noisy = self._noise_indices(size)
        office = self._add_address(city, "comercial") if self.rng.random() < 0.5 else None
        base_amount = self.rng.randint(5000, 18_000)
        start = self._random_dt()
        people: list[tuple[str, str | None, str]] = []
        for index in range(size):
            home = self._add_address(city)
            phone = self._add_phone()
            device = self._add_device() if index in noisy else device_pool[index % len(device_pool)]
            person_id = self._add_person(city, home, phone, device)
            business_id = self._add_business(person_id) if self.rng.random() < 0.4 else None
            people.append((person_id, business_id, home))
        apps: list[tuple[str, str, datetime]] = []
        for index, (person_id, business_id, home) in enumerate(people):
            declared = cover_address if cover_address and index < size // 2 else (office or home)
            created_at = start + timedelta(hours=self.rng.randint(0, 14 * 24), minutes=self.rng.randrange(60))
            app_id = self._add_application(
                person_id, created_at, geocell_id=self.address_geocell[declared],
                declared_address_id=declared, business_id=business_id,
                amount=self._amount(base_amount),
            )
            self._mark(app_id, person_id, ring_id, "device_farm", cover, size)
            apps.append((app_id, person_id, created_at))
        self._ring_refs(apps, 0.5)
        return city

    def _rotating_phone(self, ring_id: str, cover: str) -> str:
        size = self.rng.randint(5, 9)
        cover_address = self._cover_address(cover)
        city = self.address_geocell[cover_address] if cover_address else self._city()
        shared_phone = self._add_phone()
        noisy = self._noise_indices(size)
        office = self._add_address(city, "comercial") if self.rng.random() < 0.5 else None
        start = self._random_dt()
        people: list[tuple[str, str | None, str]] = []
        for index in range(size):
            home = self._add_address(city)
            device = self._add_device()
            phone = self._add_phone() if index in noisy else shared_phone
            person_id = self._add_person(city, home, phone, device)
            business_id = self._add_business(person_id) if self.rng.random() < 0.35 else None
            people.append((person_id, business_id, home))
        apps: list[tuple[str, str, datetime]] = []
        for index, (person_id, business_id, home) in enumerate(people):
            declared = cover_address if cover_address and index % 3 == 0 else (office or home)
            created_at = start + timedelta(hours=self.rng.randint(0, 21 * 24), minutes=self.rng.randrange(60))
            amount = self._amount(self.rng.randint(4000, 14_000), 2000)
            app_id = self._add_application(
                person_id, created_at, geocell_id=self.address_geocell[declared],
                declared_address_id=declared, business_id=business_id, amount=amount,
            )
            self._mark(app_id, person_id, ring_id, "rotating_phone", cover, size)
            apps.append((app_id, person_id, created_at))
        self._ring_refs(apps, 0.6)
        return city

    def _circular_references(self, ring_id: str, cover: str) -> str:
        size = self.rng.randint(5, 9)
        city = self._city()
        cover_address = self._cover_address(cover)
        noisy_cycle = self._noise_indices(size, float(self.config["cycle_noise_rate"]))
        start = self._random_dt()
        people: list[tuple[str, str | None, str]] = []
        for _ in range(size):
            home = self._add_address(city)
            phone = self._add_phone()
            device = self._add_device()
            person_id = self._add_person(city, home, phone, device)
            business_id = self._add_business(person_id) if self.rng.random() < 0.4 else None
            people.append((person_id, business_id, home))
        apps: list[tuple[str, str, datetime]] = []
        for index, (person_id, business_id, home) in enumerate(people):
            declared = cover_address if cover_address and index == 0 else home
            created_at = start + timedelta(hours=self.rng.randint(0, 45 * 24), minutes=self.rng.randrange(60))
            app_id = self._add_application(
                person_id, created_at, geocell_id=self.address_geocell[declared],
                declared_address_id=declared, business_id=business_id,
                amount=self._amount(self.rng.randint(5000, 16_000), 2500),
            )
            self._mark(app_id, person_id, ring_id, "circular_references", cover, size)
            apps.append((app_id, person_id, created_at))
        for index, (app_id, _person_id, created_at) in enumerate(apps):
            reference_count = self.rng.choices([1, 2, 3], weights=[0.25, 0.55, 0.20], k=1)[0]
            references: list[tuple[str, str]] = []
            if index not in noisy_cycle:
                references.append((people[(index + 1) % size][0], "socio"))
            used = {person_id for person_id, _ in references}
            while len(references) < reference_count:
                legit_person, relationship = self._legit_reference(city, used)
                references.append((legit_person, relationship))
                used.add(legit_person)
            for ref_person_id, relationship in references:
                self._add_reference(
                    app_id, ref_person_id,
                    created_at - timedelta(days=self.rng.randint(2, 10)), relationship,
                )
        return city

    def _application_burst(self, ring_id: str, cover: str) -> str:
        size = self.rng.randint(10, 20)
        cover_address = self._cover_address(cover)
        city = self.address_geocell[cover_address] if cover_address else self._city()
        office = self._add_address(city, "comercial")
        noisy = self._noise_indices(size, float(self.config["burst_noise_rate"]))
        base_amount = self.rng.randint(6000, 22_000)
        start = self._random_dt()
        people: list[tuple[str, str | None, str]] = []
        for _ in range(size):
            home = self._add_address(city)
            people.append((self._add_person(city, home, self._add_phone(), self._add_device()), None, home))
        apps: list[tuple[str, str, datetime]] = []
        for index, (person_id, _business_id, _home) in enumerate(people):
            declared = cover_address if cover_address and index % 2 == 0 else office
            if index in noisy:
                created_at = start + timedelta(days=self.rng.randint(10, 40), hours=self.rng.randrange(24))
            else:
                created_at = start + timedelta(
                    hours=self.rng.randint(0, int(self.config["burst_window_hours"])),
                    minutes=self.rng.randrange(60),
                )
            spread = 900 if index not in noisy else 4000
            app_id = self._add_application(
                person_id, created_at, geocell_id=self.address_geocell[declared],
                declared_address_id=declared, amount=self._amount(base_amount, spread),
                product="microcrédito", channel="app",
            )
            self._mark(app_id, person_id, ring_id, "application_burst", cover, size)
            apps.append((app_id, person_id, created_at))
        self._ring_refs(apps, 0.3)
        return city

    def _impossible_locations(self, ring_id: str, cover: str) -> str:
        size = self.rng.randint(5, 8)
        home_city = pick_weighted(
            self.rng, ["GEO-TRU-01", "GEO-TRU-02", "GEO-TRU-03", "GEO-LIB-01"],
            [0.45, 0.20, 0.20, 0.15],
        )
        far_city = self.rng.choice(FAR_GEOCELLS)
        noisy = self._noise_indices(size)
        start = self._random_dt()
        for index in range(size):
            home = self._add_address(home_city)
            person_id = self._add_person(home_city, home, self._add_phone(), self._add_device())
            business_id = self._add_business(person_id) if self.rng.random() < 0.3 else None
            amount = self.rng.randint(8000, 25_000)
            first_time = start + timedelta(hours=self.rng.randint(0, 20 * 24))
            app_geocell = home_city if index in noisy else far_city
            app_id = self._add_application(
                person_id, first_time, geocell_id=app_geocell, declared_address_id=home,
                business_id=business_id, amount=amount,
            )
            self._mark(app_id, person_id, ring_id, "impossible_locations", cover, size)
            if index not in noisy and (index < size // 2 or self.rng.random() < 0.4):
                second = first_time + timedelta(hours=self.rng.randint(1, 36))
                second_app = self._add_application(
                    person_id, second, geocell_id=home_city, declared_address_id=home,
                    business_id=business_id, amount=self._amount(amount, 3000),
                )
                self._mark(second_app, person_id, ring_id, "impossible_locations", cover, size)
        return home_city

    # --- Orquestación ---------------------------------------------------------
    def build(self, n_rings: int) -> InjectionResult:
        for index in range(n_rings):
            ring_id = f"RING{index + 1:03d}"
            ring_type = RING_TYPES[index % len(RING_TYPES)]
            if ring_type == "impossible_locations":
                cover = "none"
            elif self.market_choices and self.rng.random() < float(self.config["cover_probability"]):
                cover = "market_cover"
            else:
                cover = "none"
            before_apps = len(self.app_rows)
            builder = getattr(self, f"_{ring_type}")
            home_geocell = builder(ring_id, cover)
            n_apps = len(self.app_rows) - before_apps
            self.ring_rows.append({
                "ring_id": ring_id,
                "ring_type": ring_type,
                "cover_pattern": cover,
                "ring_size": len({
                    row["person_id"] for row in self.truth_rows if row["ring_id"] == ring_id
                }),
                "n_applications": n_apps,
                "home_geocell": home_geocell,
            })
        return self._frames()

    def _frames(self) -> InjectionResult:
        return InjectionResult(
            persons=pd.DataFrame(self.person_rows, columns=PUBLIC_SCHEMAS["persons"]),
            businesses=pd.DataFrame(self.business_rows, columns=PUBLIC_SCHEMAS["businesses"]),
            addresses=pd.DataFrame(self.address_rows, columns=PUBLIC_SCHEMAS["addresses"]),
            phones=pd.DataFrame(self.phone_rows, columns=PUBLIC_SCHEMAS["phones"]),
            devices=pd.DataFrame(self.device_rows, columns=PUBLIC_SCHEMAS["devices"]),
            applications=pd.DataFrame(self.app_rows, columns=PUBLIC_SCHEMAS["applications"]),
            references=pd.DataFrame(self.ref_rows, columns=PUBLIC_SCHEMAS["references"]),
            truth=pd.DataFrame(self.truth_rows, columns=TRUTH_SCHEMAS["ground_truth"]),
            rings=pd.DataFrame(self.ring_rows, columns=TRUTH_SCHEMAS["rings"]),
        )


def inject_fraud_rings(
    population: Population, n_rings: int, difficulty: str = "medium"
) -> InjectionResult:
    """Inyecta ``n_rings`` anillos ciclando las cinco modalidades."""
    if n_rings < 0:
        raise ValueError("n_rings debe ser >= 0")
    return _RingBuilder(population, difficulty).build(n_rings)
