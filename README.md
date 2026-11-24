# RIE-02 — Detección de redes de riesgo en microfinanzas

Prototipo para el hackathon Cajathon de Caja Trujillo. Identifica **relaciones
inusuales** entre personas, negocios y solicitudes para **priorizar revisión
humana**. No determina fraude, no rechaza créditos y no decide automáticamente.

> **Fases 1–3 entregadas:** generador sintético con IDs opacos y anillos
> inyectados, grafo bipartito y proyección ponderada, y motor no supervisado
> de detección de redes con puntuación explicable.

## Datos

Todos los datos son **100 % sintéticos**. Los documentos (DNI de 8 dígitos),
nombres y teléfonos son ficticios; no se usa información real de personas. Las
etiquetas de anillos se guardan en `data/ground_truth/` y no se incluyen en las
tablas públicas. Al final de la generación todas las claves se reemplazan por
tokens opacos aleatorios y las filas se barajan para que ni el orden ni el
prefijo de un ID delaten a un anillo.

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## Generar el dataset

```bash
# Cartera de trabajo: 5.000 personas legítimas y 25 anillos (~0,5 %)
python -m data.generator --n-legit 5000 --rings 25 --seed 42 --difficulty medium
```

### Dificultad

```bash
python -m data.generator --n-legit 5000 --rings 25 --seed 42 --difficulty easy
python -m data.generator --n-legit 5000 --rings 25 --seed 42 --difficulty medium
python -m data.generator --n-legit 5000 --rings 25 --seed 42 --difficulty hard
```

- `easy`: patrones más concentrados y sin camuflaje.
- `medium`: configuración de trabajo, con cobertura parcial de mercados.
- `hard`: ruido en ~25 % de miembros, mayor camuflaje en direcciones de mercado
  y ráfagas más espaciadas. La dificultad queda registrada en
  `data/ground_truth/run_meta.json`.

### Baja prevalencia (5 anillos)

```bash
python -m data.generator --n-legit 5000 --rings 5 --seed 42 --difficulty hard --out data_lowprev
```

Equivale a **5 anillos por 5.000 personas** (~0,1 %), útil para evaluar el
rendimiento cuando el fraude es raro. Se escribe en `data_lowprev/` para no
mezclarlo con la cartera principal.

Salidas principales:

- `data/raw/persons.csv`, `businesses.csv`, `addresses.csv`, `phones.csv`,
  `devices.csv`, `applications.csv`, `references.csv`, `geocells.csv`
- `data/raw/dataset_meta.json`
- `data/ground_truth/ground_truth.csv`, `rings.csv` y `run_meta.json`
  (solo para evaluación)

Modalidades inyectadas: granja de dispositivos, teléfono rotando, cadena
circular de referencias, ráfaga de solicitudes y ubicaciones imposibles. Los
anillos circulares mezclan el ciclo con referencias a personas legítimas y
mantienen una media de ~1,9 referencias por solicitud, similar a la población
legítima. Una parte de los anillos usa una dirección de mercado legítima como
cobertura.

## Fase 2 — Grafo de riesgo

```bash
python -m graph.builder --input data/raw --output outputs/graph --k 25
```

`--k` es el umbral de multiplicidad (por defecto `25`). El comando lee solo las
tablas públicas y escribe:

- `outputs/graph/graph.graphml` — grafo bipartito entidad ↔ atributo.
- `outputs/graph/projection.graphml` — proyección entre solicitudes.
- `outputs/graph/graph.pkl` — ambas capas y tablas planas para reutilizarlas.
- `outputs/graph/graph_edges.csv` — aristas con peso, evidencia y ventana
  temporal; incluye una columna `graph_layer` (`bipartite` / `projection`).
- `outputs/graph/graph_nodes.csv` y `graph_attributes.csv`.
- `outputs/graph/graph_meta.json` — configuración, conteos y tiempo.

### Modelo de pesos

Cada atributo (teléfono, dispositivo, dirección, referencia o geocelda) recibe
un IDF suavizado `w = log((N + 1) / (df + 1))`, donde `N` es el total de
entidades de la izquierda (solicitudes + personas + negocios) y `df` su
frecuencia sobre esas entidades. El peso se limita con un tope por tipo para
que un atributo casi único no domine la agregación.

Un atributo compartido por **más de K entidades** se marca
`high_multiplicity` (y `multiplicity_label = "alta_multiplicidad"`) y no genera
todas las parejas de solicitudes. En la proyección se representa con un nodo
`hub:...`; cada solicitud se conecta al hub, de modo que el número de aristas
crece de forma lineal. Esto evita la explosión cuadrática de geoceldas y
direcciones de mercados.

Cada arista guarda `evidence_json` con la lista de atributos que la originan
(`type`, `value_hash` de 16 caracteres y `weight`) y las fechas mínima y máxima
de las solicitudes conectadas (`min_created_at`, `max_created_at`,
`span_hours`). La Fase 4 podrá citar esa evidencia exacta en un expediente.

Ejemplo de ejecución con la cartera de 5.000 solicitudes:

```text
n_applications: 5261
n_entities: 12607
n_attributes: 18096
atributos de alta multiplicidad: 24
aristas bipartitas: 60425
aristas de proyección: 19833
tiempo de construcción: ~3,5 s
```

## Fase 3 — Detección de redes de riesgo

```bash
python -m detection.engine --graph outputs/graph/graph.pkl --raw data/raw --output outputs/detection --threshold 60
```

El motor es no supervisado y no lee `data/ground_truth/`. Genera:

- `outputs/detection/clusters.csv` — comunidades de riesgo con puntuación,
  tamaño, densidad, evidencias y miembros.
- `outputs/detection/application_scores.csv` — puntuación por solicitud,
  cluster asignado, motivo principal y evidencia.
- `outputs/detection/detection_meta.json` — configuración, conteos y tiempo.

En la cartera de trabajo detecta 28 redes con 259 solicitudes, todas las
redes son puras y la precisión en el Top 259 es 1,0.

Evaluación offline (solo aquí se usa la verdad terreno):

```bash
python -m eval.evaluate --detection outputs/detection --truth data/ground_truth --output outputs/eval
```

Resultados de referencia: AP 0,9927, AUC 0,9926, 28 clusters puros y
259/261 anillos capturados.

## Pruebas

```bash
pytest
```

Incluye pruebas de integridad referencial, determinismo, formato de DNI,
distribución local de direcciones, prevalencia, referencias circulares y
**opacidad de IDs**: los anillos no se separan por prefijo ni por posición.

Las pruebas de la Fase 2 verifican que un teléfono compartido por 2 personas
pese más que una dirección compartida por 40, que la dirección se represente
con hub sin clique, que la evidencia y las fechas se exporten, y que la
construcción con 5.000 solicitudes termine en menos de 30 segundos.

## Privacidad

- La UI enmascarará documentos y teléfonos (fase 7).
- El motor no lee `data/ground_truth/`; solo `eval/` lo usa para medir.
- No se debe interpretar una coincidencia de teléfono, dirección o referencia
  como evidencia de fraude.
