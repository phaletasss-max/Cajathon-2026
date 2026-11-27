"""Landing pública y demostración guiada de RedRiesgo."""

LANDING_HTML = r"""<!doctype html>
<html lang="es" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="RedRiesgo conecta señales dispersas para priorizar la revisión humana en microfinanzas.">
<title>RedRiesgo · Redes de riesgo en microfinanzas</title>
<link rel="icon" href="/logo.jpg" type="image/jpeg">
<script>
  try {
    document.documentElement.dataset.theme = localStorage.getItem('redriesgo-theme')
      ?? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  } catch {}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    color-scheme: light;
    --bg:#f5f8f6; --paper:#fff; --ink:#122d24; --muted:#476258; --line:#d5e3db;
    --brand:#17604a; --button:#185641; --on-button:#fff; --soft:#e7f3ec;
    --mint:#d7efdf; --lavender:#eeecfb; --amber:#fff0d6; --shadow:#153b2320;
    --edge:#669880;
  }
  [data-theme="dark"] {
    color-scheme: dark;
    --bg:#101916; --paper:#17241e; --ink:#eff9f1; --muted:#b0c9ba; --line:#344b3f;
    --brand:#9be4b9; --button:#a7edbe; --on-button:#113323; --soft:#21392c;
    --mint:#243e30; --lavender:#2f3049; --amber:#493b28; --shadow:#0006;
    --edge:#79b798;
  }
  * { box-sizing:border-box; }
  html { scroll-behavior:smooth; }
  body { margin:0; background:var(--bg); color:var(--ink); font: 1rem/1.6 'DM Sans',system-ui,sans-serif; }
  h1,h2,h3,p { margin:0; }
  h1,h2,h3,.wordmark { font-family:Manrope,system-ui,sans-serif; line-height:1.12; }
  a { color:inherit; }
  button { font:inherit; cursor:pointer; }
  :focus-visible { outline:3px solid var(--brand); outline-offset:4px; }
  .wrap { width:min(1160px, calc(100% - 48px)); margin-inline:auto; }
  .nav { display:flex; justify-content:space-between; align-items:center; gap:18px; padding-block:20px; }
  header { border-bottom:1px solid var(--line); }
  .wordmark { text-decoration:none; font-weight:800; font-size:1.25rem; display:inline-flex; align-items:center; gap:10px; }
  .brand-logo { display:block; width:106px; height:auto; border:1px solid var(--line); border-radius:10px; }
  .materials,.outcomes { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; margin-top:24px; }
  .material { margin:0; overflow:hidden; border:1px solid var(--line); border-radius:18px; background:var(--paper); }
  .material img { display:block; width:100%; height:auto; }
  .material figcaption { padding:12px 16px; font-weight:700; }
  .evidence,.review { margin-top:16px; border:1px solid var(--line); border-radius:18px; background:var(--paper); padding:clamp(16px,3vw,24px); }
  .evidence h3,.review h3 { margin-bottom:8px; }
  .evidence ul { padding-left:20px; margin:8px 0; }
  .evidence code { overflow-wrap:anywhere; }
  .review form { display:flex; flex-wrap:wrap; align-items:end; gap:10px; margin-top:12px; }
  .review label { display:grid; gap:5px; font-weight:700; }
  .review select { padding:10px; border:1px solid var(--line); border-radius:10px; background:var(--paper); color:var(--ink); font:inherit; }
  .review button:disabled { cursor:default; opacity:.55; }
  .review-status { margin-top:8px; }
  .evaluation { margin-block:16px; display:flex; flex-wrap:wrap; gap:10px; }
  .evaluation span { border:1px solid var(--line); padding:8px 12px; border-radius:10px; background:var(--paper); }
  @media (max-width:620px) { .materials,.outcomes { grid-template-columns:1fr; } }
  .nav-links,.actions,.case-options { display:flex; flex-wrap:wrap; align-items:center; gap:12px; }
  .nav-links a { text-decoration:none; color:var(--muted); font-weight:700; font-size:.88rem; margin-right:12px; }
  .btn,.theme,.case { border:1px solid var(--line); border-radius:10px; background:var(--paper); color:var(--ink); padding:10px 15px; text-decoration:none; font-weight:700; }
  .btn.primary,.case[aria-pressed="true"] { background:var(--button); color:var(--on-button); border-color:var(--button); }
  .btn:hover,.theme:hover,.case:hover { box-shadow:0 3px 12px var(--shadow); }
  .theme { padding:6px 10px; font-size:.82rem; min-width:102px; }
  .hero { display:grid; grid-template-columns:1.04fr 1fr; align-items:center; gap:clamp(32px,6vw,84px); padding-block:clamp(54px,9vw,120px); }
  .eyebrow { font-size:.77rem; text-transform:uppercase; letter-spacing:.13em; color:var(--brand); font-weight:800; }
  h1 { font-size:clamp(2.6rem,5.2vw,5.1rem); letter-spacing:-.07em; margin-block:15px 20px; font-weight:800; }
  h1 em { color:var(--brand); font-style:normal; }
  .lede { color:var(--muted); font-size:clamp(1rem,1.5vw,1.15rem); max-width:49ch; }
  .actions { margin-top:27px; }
  .graph-card { min-width:0; border:1px solid var(--line); border-radius:24px; overflow:hidden; background:var(--paper); box-shadow:0 20px 55px var(--shadow); }
  .graph-header { display:flex; justify-content:space-between; align-items:center; gap:10px; padding:17px 19px; font-size:.85rem; border-bottom:1px solid var(--line); font-weight:700; }
  .tag { background:var(--soft); color:var(--brand); border-radius:999px; padding:4px 10px; font-size:.73rem; white-space:nowrap; }
  .graph { position:relative; height:260px; isolation:isolate; background:radial-gradient(circle at center,var(--soft),transparent 75%),radial-gradient(var(--line) 1px,transparent 1px); background-size:auto,16px 16px; }
  .graph .node { position:absolute; translate:-50% -50%; z-index:1; display:grid; place-items:center; min-height:35px; min-width:42px; border:1px solid var(--line); border-radius:10px; padding:4px 7px; background:var(--paper); color:var(--muted); font-weight:800; font-size:.76rem; white-space:nowrap; }
  .graph .hub { background:var(--button); color:var(--on-button); padding:8px 11px; }
  .graph canvas { width:100%; height:100%; display:block; }
  .legend { padding:13px 19px; color:var(--muted); font-size:.83rem; border-top:1px solid var(--line); }
  .section { padding-block:clamp(48px,8vw,88px); border-top:1px solid var(--line); scroll-margin-top:16px; }
  h2 { margin-block:9px 15px; font-size:clamp(2rem,4vw,3.2rem); letter-spacing:-.055em; }
  .intro { color:var(--muted); max-width:65ch; }
  .steps { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; margin-top:25px; }
  .step { padding:24px; border-radius:18px; background:var(--mint); }
  .step:nth-child(2) { background:var(--lavender); }
  .step:nth-child(3) { background:var(--amber); }
  .step h3 { font-size:1.18rem; margin-bottom:10px; }
  .step p { color:var(--muted); }
  .demo { background:var(--soft); }
  .case-options { margin:20px 0; }
  .case { font-size:.9rem; }
  .demo-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; align-items:stretch; }
  .case-card { background:var(--paper); border:1px solid var(--line); border-radius:24px; padding:24px; }
  .case-card h3 { margin:6px 0 10px; font-size:clamp(1.4rem,2.5vw,2.1rem); letter-spacing:-.04em; }
  .case-card p { color:var(--muted); }
  .case-card dl { display:flex; flex-wrap:wrap; gap:12px 28px; margin:17px 0; padding:12px 0; border-block:1px solid var(--line); }
  .case-card dt { color:var(--muted); font-size:.79rem; }
  .case-card dd { margin:0; font-size:1.15rem; font-weight:800; }
  .case-card .question { color:var(--ink); border-left:3px solid var(--edge); padding-left:12px; }
  footer { border-top:1px solid var(--line); }
  .footer { padding-block:22px; display:flex; flex-wrap:wrap; justify-content:space-between; gap:10px 24px; color:var(--muted); font-size:.9rem; }
  @media (max-width:820px) { .hero,.demo-grid { grid-template-columns:1fr; } }
  @media (max-width:620px) {
    .wrap { width:calc(100% - 32px); }
    .steps { grid-template-columns:1fr; }
    .nav-links a { display:none; }
    .graph { height:220px; }
  }
  @media (prefers-reduced-motion:reduce) { html { scroll-behavior:auto; } }
</style>
</head>
<body>
<header>
  <nav class="wrap nav" aria-label="Navegación principal">
    <a class="wordmark" href="#" aria-label="RedRiesgo, inicio"><img class="brand-logo" src="/logo.jpg" width="1024" height="682" alt="RedRiesgo"></a>
    <div class="nav-links">
      <a href="#como-funciona">Cómo funciona</a>
      <a href="#demo">Demostración</a>
      <button class="theme" id="theme" type="button" aria-pressed="false">Modo oscuro</button>
    </div>
  </nav>
</header>
<main>
  <section class="wrap hero" aria-labelledby="title">
    <div>
      <p class="eyebrow">CAJATHON 2026 · RIE-02 · Caja Trujillo</p>
      <h1 id="title">El riesgo aparece <em>en las conexiones.</em></h1>
      <p class="lede">RedRiesgo conecta solicitudes de microcrédito que comparten datos, identifica patrones inusuales y prepara evidencia para que un analista decida qué investigar.</p>
      <div class="actions">
        <a class="btn primary" href="#demo">Explorar la demo ↓</a>
        <a class="btn" href="#como-funciona">Cómo funciona</a>
      </div>
    </div>
    <div class="graph-card">
      <div class="graph-header"><span>Una red detrás de varias solicitudes</span><span class="tag">Ilustración</span></div>
      <div class="graph" id="hero-graph" role="img" aria-label="Cinco solicitudes comparten la misma dirección.">
        <canvas aria-hidden="true"></canvas>
        <span class="node" style="left:18%;top:32%">S01</span><span class="node" style="left:50%;top:20%">S02</span>
        <span class="node" style="left:82%;top:32%">S03</span><span class="node" style="left:25%;top:77%">S04</span>
        <span class="node" style="left:75%;top:77%">S05</span><span class="node hub" style="left:50%;top:53%">Dirección</span>
      </div>
      <p class="legend">Cada línea representa un dato compartido entre una solicitud y la dirección.</p>
    </div>
  </section>

  <section class="section" id="como-funciona">
    <div class="wrap">
      <p class="eyebrow">Descubrir redes de riesgo ocultas</p>
      <h2>De solicitudes aisladas a evidencia revisable</h2><p class="intro">El reto de Caja Trujillo es detectar relaciones inusuales entre personas, negocios y créditos para orientar la prevención y la investigación. Compartir un dato puede tener una explicación legítima, como operar en el mismo mercado.</p>
      <div class="steps">
        <article class="step"><h3>Construye el grafo</h3><p>Conecta personas, negocios y solicitudes con teléfonos, dispositivos, direcciones, referencias y geoceldas. Los identificadores se tokenizan antes del análisis.</p></article>
        <article class="step"><h3>Detecta y prioriza</h3><p>La ponderación por frecuencia inversa (IDF) reduce el peso de coincidencias comunes. El motor combina esa información con comunidades, ciclos de referencias y concentraciones temporales.</p></article>
        <article class="step"><h3>Prepara el expediente</h3><p>Reúne las señales y las solicitudes vinculadas. El analista revisa la evidencia y decide si corresponde investigar más. La decisión crediticia queda a cargo de la entidad.</p></article>
      </div>
      <div class="materials">
        <figure class="material"><a href="/assets/arquitectura.jpg"><img loading="lazy" src="/assets/arquitectura.jpg" alt="Diagrama del flujo de datos, detección y revisión de RedRiesgo"></a><figcaption>Arquitectura del prototipo</figcaption></figure>
        <figure class="material"><a href="/assets/patrones-grafos.jpg"><img loading="lazy" src="/assets/patrones-grafos.jpg" alt="Comparación entre hubs legítimos y redes de riesgo en microfinanzas"></a><figcaption>Patrones de grafos en microfinanzas</figcaption></figure>
      </div>
    </div>
  </section>

  <section class="section demo" id="demo">
    <div class="wrap">
      <p class="eyebrow">Demostración guiada</p>
      <h2>¿Qué merece una investigación?</h2>
      <p class="intro">Cambia de caso para ver qué detectaría el sistema y qué pregunta podría hacerse el analista. Las alertas proceden de la cartera sintética del prototipo. El mercado es un ejemplo ilustrativo de una coincidencia legítima.</p>
      <div class="case-options" role="group" aria-label="Casos de demostración">
        <button class="case" type="button" aria-pressed="true" data-case="address">Dirección compartida</button>
        <button class="case" type="button" aria-pressed="false" data-case="reference">Ciclo de referencias</button>
        <button class="case" type="button" aria-pressed="false" data-case="phone">Teléfono compartido</button>
        <button class="case" type="button" aria-pressed="false" data-case="device">Dispositivo compartido</button>
        <button class="case" type="button" aria-pressed="false" data-case="market">Mercado legítimo</button>
      </div>
      <div class="demo-grid">
        <div class="graph-card">
          <div class="graph-header"><span>Patrón de conexión</span><span class="tag">Esquema</span></div>
          <div class="graph" id="case-graph" role="img" aria-label="Cuatro solicitudes enlazadas a una dirección compartida">
            <canvas aria-hidden="true"></canvas>
            <span class="node" style="left:22%;top:26%">S01</span><span class="node" style="left:78%;top:26%">S02</span>
            <span class="node" style="left:78%;top:75%">S03</span><span class="node" style="left:22%;top:75%">S04</span>
            <span class="node hub" style="left:50%;top:50%">Dirección</span>
          </div>
          <p class="legend" id="graph-legend">El esquema muestra parte del patrón de la red.</p>
        </div>
        <article class="case-card" aria-live="polite" aria-atomic="true">
          <p class="eyebrow" id="case-id">Caso C00001</p>
          <h3 id="case-title">Una dirección, diez solicitudes</h3>
          <p id="case-signal">Diez solicitudes comparten dirección y se concentran en poco más de dos días.</p>
          <dl><div><dt>Riesgo estimado</dt><dd id="case-score">81,83 / 100</dd></div><div><dt>Solicitudes vinculadas</dt><dd id="case-count">10</dd></div></dl>
          <p class="question"><strong>Pregunta para revisión</strong><br><span id="case-question">¿Es un punto comercial que explica la coincidencia o hay otros vínculos entre los solicitantes?</span></p>
        </article>
      </div>
      <section class="evidence" aria-labelledby="evidence-title">
        <h3 id="evidence-title">Evidencia del expediente</h3>
        <div id="case-evidence" aria-live="polite">Consultando el expediente de la API…</div>
      </section>
      <section class="review" aria-labelledby="review-title">
        <h3 id="review-title">Ensaya la revisión humana</h3>
        <p class="intro">La decisión de práctica se guarda en este navegador durante la sesión.</p>
        <form id="review-demo">
          <label>Resultado de revisión
            <select id="demo-decision" required>
              <option value="">Elige un resultado</option>
              <option>En seguimiento</option>
              <option>Escalar a investigación</option>
              <option>Descartar como falso positivo</option>
            </select>
          </label>
          <button class="btn primary" type="submit">Registrar en la demo</button>
        </form>
        <p id="demo-status" class="review-status" role="status">Pendiente de revisión</p>
      </section>
      <noscript><p>Activa JavaScript para cambiar de caso o elegir otro tema.</p></noscript>
    </div>
  </section>
  <section class="section" id="validacion">
    <div class="wrap">
      <p class="eyebrow">Validación del prototipo</p>
      <h2>Medir la detección y los falsos positivos</h2>
      <p class="intro">La muestra pública permite revisar los resultados del motor de grafos y sus expedientes. La propuesta contempla una prueba ampliada con más de 5.000 solicitudes sintéticas y una comparación de precisión, recall y falsos positivos frente a un modelo base.</p>
      <div class="evaluation" id="evaluation" aria-live="polite"></div>
      <div class="outcomes">
        <article class="step"><h3>Prevenir antes</h3><p>El objetivo es detectar redes que pasan desapercibidas al revisar cada solicitud por separado y ordenar la investigación según la evidencia.</p></article>
        <article class="step"><h3>Proteger al cliente</h3><p>El analista verifica explicaciones legítimas antes de escalar. La calibración inicial usa datos sintéticos y el prototipo opera fuera del core bancario.</p></article>
      </div>
      <div class="actions"><a class="btn" href="/metrics">Ver métricas de la muestra</a><a class="btn" href="/docs">Explorar la API del prototipo</a></div>
    </div>
  </section>
</main>
<footer>
  <div class="wrap footer">
    <span><strong>RedRiesgo</strong> · Prototipo con datos sintéticos para CAJATHON 2026</span>
    <a href="/docs">Documentación de la API</a>
  </div>
</footer>
<script>
  const themeButton = document.getElementById('theme');
  const root = document.documentElement;
  const hero = document.getElementById('hero-graph');
  const graph = document.getElementById('case-graph');
  const nodes = [...graph.querySelectorAll('.node')];
  const options = [...document.querySelectorAll('[data-case]')];
  const cases = {
    address: {
      id:'C00001', title:'Una dirección, diez solicitudes', score:'81,83', count:10, hub:'Dirección',
      signal:'Diez solicitudes comparten dirección y se concentran en poco más de dos días.',
      question:'¿Es un punto comercial que explica la coincidencia o hay otros vínculos entre los solicitantes?',
      alt:'Cuatro solicitudes enlazadas a una dirección compartida.'
    },
    reference: {
      id:'C00002', title:'Un circuito de referencias', score:'75,00', count:7, hub:'',
      signal:'Las referencias entre siete personas forman un ciclo cerrado.',
      question:'¿Hay una relación comunitaria conocida que explique por qué las referencias vuelven al punto de partida?',
      alt:'Cuatro personas se refieren entre sí en un ciclo cerrado.'
    },
    phone: {
      id:'C00003', title:'El mismo teléfono en varias solicitudes', score:'72,62', count:7, hub:'Teléfono',
      signal:'El teléfono compartido aparece en 21 conexiones dentro de la red de solicitudes.',
      question:'¿El número pertenece a un negocio que tramita solicitudes o se reutilizó como contacto personal?',
      alt:'Cuatro solicitudes enlazadas al mismo teléfono.'
    },
    device: {
      id:'C00004', title:'Un dispositivo reutilizado', score:'72,07', count:8, hub:'Dispositivo',
      signal:'La red reúne ocho solicitudes. El dispositivo compartido aparece en 12 conexiones.',
      question:'¿El equipo pertenece a un canal de atención compartido o vincula solicitudes de personas que deberían operar por separado?',
      alt:'Cuatro solicitudes enlazadas al mismo dispositivo.'
    },
    market: {
      id:'', title:'Distintos negocios en un mercado', score:null, count:null, hub:'Mercado',
      signal:'Varios negocios comparten la ubicación del mercado. El grafo trata esa concentración como un hub y reduce el peso de la coincidencia común.',
      question:'¿Qué señal independiente, como un dispositivo reutilizado en poco tiempo, justificaría revisar este caso?',
      alt:'Cuatro negocios comparten la ubicación de un mismo mercado.'
    }
  };
  let active = cases.address;
  const evidencePanel = document.getElementById('case-evidence');
  const reviewForm = document.getElementById('review-demo');
  const reviewSelect = document.getElementById('demo-decision');
  const reviewStatus = document.getElementById('demo-status');
  const savedReviews = new Map();
  const attributeLabels = {
    address:'Dirección', phone:'Teléfono', reference:'Referencia',
    device:'Dispositivo', geocell:'Zona geográfica'
  };
  const format = value => new Intl.NumberFormat('es-PE', {maximumFractionDigits:2}).format(value);
  let evidenceRequest;
  async function loadEvidence() {
    evidenceRequest?.abort();
    const id = active.id;
    if (!id) {
      evidencePanel.textContent = 'Ejemplo ilustrativo. La ubicación compartida recibe menos peso; una investigación requeriría señales adicionales.';
      return;
    }
    const request = new AbortController();
    evidenceRequest = request;
    evidencePanel.textContent = 'Consultando el expediente de la API…';
    try {
      const response = await fetch('/clusters/' + encodeURIComponent(id), {signal:request.signal});
      if (!response.ok) throw new Error();
      const { dossier } = await response.json();
      if (request.signal.aborted) return;
      const attributes = dossier?.shared_attributes;
      if (!Array.isArray(attributes) || !attributes.length) {
        evidencePanel.textContent = 'El expediente no contiene atributos compartidos.';
        return;
      }
      const description = document.createElement('p');
      const span = dossier.time_window?.span_hours;
      description.textContent = span == null ? 'Atributos tokenizados' : 'Ventana observada de ' + format(span) + ' horas';
      const list = document.createElement('ul');
      for (const entry of attributes) {
        const item = document.createElement('li');
        const token = document.createElement('code');
        token.textContent = entry.value_hash;
        item.append((attributeLabels[entry.type] ?? entry.type) + ' · ', token, ' · peso ' + format(entry.weight));
        list.append(item);
      }
      evidencePanel.replaceChildren(description, list);
    } catch {
      if (!request.signal.aborted) evidencePanel.textContent = 'El expediente no está disponible en este momento.';
    }
  }
  async function loadEvaluation() {
    try {
      const response = await fetch('/metrics');
      if (!response.ok) return;
      const { application, cluster } = await response.json();
      const metrics = [
        ['Solicitudes evaluadas', application?.n_applications],
        ['Clústeres detectados', cluster?.n_clusters],
        ['Precisión promedio', application?.average_precision],
        ['Recall de miembros', cluster?.ring_recall]
      ];
      for (const [label, value] of metrics) {
        if (!Number.isFinite(value)) continue;
        const item = document.createElement('span');
        item.textContent = label + ' · ' + format(value);
        document.getElementById('evaluation').append(item);
      }
    } catch {}
  }
  function syncReview() {
    const key = active.id || 'market';
    let saved = savedReviews.get(key);
    if (!saved) {
      try { saved = sessionStorage.getItem('redriesgo-review-' + key); } catch {}
    }
    reviewSelect.value = saved || '';
    reviewStatus.textContent = saved ? 'Resultado de práctica · ' + saved : 'Pendiente de revisión';
  }
  reviewForm.addEventListener('submit', event => {
    event.preventDefault();
    const key = active.id || 'market';
    const value = reviewSelect.value;
    if (!value) return;
    savedReviews.set(key, value);
    try { sessionStorage.setItem('redriesgo-review-' + key, value); } catch {}
    syncReview();
  });
  function draw(container, cycle = false) {
    const canvas = container.querySelector('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const width = container.clientWidth;
    const height = container.clientHeight;
    const scale = devicePixelRatio || 1;
    canvas.width = width * scale;
    canvas.height = height * scale;
    ctx.scale(scale, scale);
    const positions = [...container.querySelectorAll('.node')].map(node => [
      parseFloat(node.style.left) * width / 100, parseFloat(node.style.top) * height / 100
    ]);
    const hub = positions.pop();
    ctx.strokeStyle = getComputedStyle(container).getPropertyValue('--edge').trim();
    ctx.lineWidth = 2;
    positions.forEach(([x,y], index) => {
      const [endX,endY] = cycle ? positions[(index + 1) % positions.length] : hub;
      ctx.beginPath();
      ctx.moveTo(x,y);
      ctx.lineTo(endX,endY);
      ctx.stroke();
      if (cycle) {
        const angle = Math.atan2(endY-y,endX-x);
        const midX = (x+endX)/2, midY = (y+endY)/2;
        ctx.beginPath();
        ctx.moveTo(midX-9*Math.cos(angle-.5),midY-9*Math.sin(angle-.5));
        ctx.lineTo(midX,midY);
        ctx.lineTo(midX-9*Math.cos(angle+.5),midY-9*Math.sin(angle+.5));
        ctx.stroke();
      }
    });
  }
  function redraw() {
    draw(hero);
    draw(graph, !active.hub);
  }
  function syncTheme() {
    const dark = root.dataset.theme === 'dark';
    themeButton.setAttribute('aria-pressed', String(dark));
    themeButton.textContent = dark ? 'Modo claro' : 'Modo oscuro';
    redraw();
  }
  themeButton.addEventListener('click', () => {
    root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('redriesgo-theme', root.dataset.theme); } catch {}
    syncTheme();
  });
  for (const option of options) {
    option.addEventListener('click', () => {
      active = cases[option.dataset.case];
      for (const item of options) item.setAttribute('aria-pressed', String(item === option));
      document.getElementById('case-id').textContent = active.id ? 'Caso ' + active.id : 'Ejemplo ilustrativo';
      document.getElementById('case-title').textContent = active.title;
      document.getElementById('case-signal').textContent = active.signal;
      document.getElementById('case-score').textContent = active.score ? active.score + ' / 100' : 'Sin puntuación';
      document.getElementById('case-count').textContent = active.count ?? '—';
      document.getElementById('case-question').textContent = active.question;
      document.getElementById('graph-legend').textContent = active.hub
        ? 'El esquema muestra parte del patrón de la red.'
        : 'Las flechas representan referencias declaradas entre personas.';
      graph.setAttribute('aria-label', active.alt);
      for (const [index,node] of nodes.slice(0,-1).entries()) node.textContent = (active.id ? (active.hub ? 'S' : 'P') : 'N') + '0' + (index + 1);
      const hub = nodes.at(-1);
      hub.hidden = !active.hub;
      hub.style.display = active.hub ? '' : 'none';
      hub.textContent = active.hub;
      syncReview();
      loadEvidence();
      draw(graph, !active.hub);
    });
  }
  const observer = new ResizeObserver(redraw);
  observer.observe(hero);
  observer.observe(graph);
  syncTheme();
  syncReview();
  loadEvidence();
  loadEvaluation();
</script>
</body>
</html>
"""
