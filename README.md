# RIE-02 — Detección de redes de riesgo en microfinanzas

Prototipo para el hackathon Cajathon de Caja Trujillo. Identifica **relaciones
inusuales** entre personas, negocios y solicitudes para **priorizar revisión
humana**. No determina fraude, no rechaza créditos y no decide automáticamente.

> **Fase 1 entregada:** estructura, generador sintético con población legítima,
> anillos inyectados, IDs opacos, dificultad configurable y datos locales de
> Trujillo/La Libertad.

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

## Pruebas

```bash
pytest
```

Incluye pruebas de integridad referencial, determinismo, formato de DNI,
distribución local de direcciones, prevalencia, referencias circulares y
**opacidad de IDs**: los anillos no se separan por prefijo ni por posición.

## Privacidad

- La UI enmascarará documentos y teléfonos (fase 7).
- El motor no lee `data/ground_truth/`; solo `eval/` lo usa para medir.
- No se debe interpretar una coincidencia de teléfono, dirección o referencia
  como evidencia de fraude.
