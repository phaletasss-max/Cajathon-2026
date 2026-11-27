"""Página web demostrativa de RedRiesgo servida en la raíz de FastAPI."""

LANDING_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RedRiesgo — Inteligencia de Grafos para Detección de Fraude</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #f8fafc;
      --surface: #ffffff;
      --surface-alt: #f1f5f9;
      --border: #e2e8f0;
      --border-strong: #cbd5e1;
      --navy: #0f172a;
      --text: #1e293b;
      --muted: #64748b;
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --primary-soft: #eff6ff;
      --danger: #ef4444;
      --danger-soft: #fef2f2;
      --warning: #d97706;
      --warning-soft: #fffbeb;
      --success: #059669;
      --success-soft: #ecfdf5;
      --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.05);
      --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.06);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
    }

    /* Topbar */
    .topbar {
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 0;
      z-index: 30;
    }
    .topbar-inner {
      max-width: 1280px;
      margin: 0 auto;
      padding: 0.75rem 1.5rem;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 0.9rem;
    }
    .brand img {
      height: 44px;
      width: auto;
      display: block;
    }
    .brand-divider {
      width: 1px;
      height: 28px;
      background: var(--border);
    }
    .brand-tag {
      font-size: 0.82rem;
      color: var(--muted);
      font-weight: 500;
    }
    .nav-actions {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      flex-wrap: wrap;
    }
    .pill-live {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--success);
      background: var(--success-soft);
      border: 1px solid #a7f3d0;
      padding: 0.32rem 0.7rem;
      border-radius: 999px;
    }
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
      padding: 0.48rem 0.9rem;
      border-radius: 8px;
      font-size: 0.84rem;
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--navy);
      transition: all 0.15s ease;
      font-family: inherit;
    }
    .btn:hover { background: var(--surface-alt); border-color: var(--border-strong); }
    .btn-primary {
      background: var(--primary);
      border-color: var(--primary);
      color: #ffffff;
    }
    .btn-primary:hover { background: var(--primary-hover); border-color: var(--primary-hover); }

    .container {
      max-width: 1280px;
      margin: 0 auto;
      padding: 1.5rem;
    }

    /* Hero Card */
    .hero {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 1.5rem 1.75rem;
      box-shadow: var(--shadow-sm);
      display: grid;
      grid-template-columns: 1.35fr 0.65fr;
      gap: 1.5rem;
      align-items: center;
      margin-bottom: 1.5rem;
    }
    @media (max-width: 900px) { .hero { grid-template-columns: 1fr; } }
    .hero-eyebrow {
      display: inline-block;
      font-size: 0.74rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--primary);
      background: var(--primary-soft);
      padding: 0.25rem 0.6rem;
      border-radius: 6px;
      margin-bottom: 0.6rem;
    }
    .hero h1 {
      font-size: 1.55rem;
      font-weight: 800;
      color: var(--navy);
      letter-spacing: -0.025em;
      margin-bottom: 0.45rem;
    }
    .hero p {
      font-size: 0.93rem;
      color: var(--muted);
      max-width: 700px;
    }
    .hero-steps {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.65rem;
    }
    .step-chip {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 0.6rem 0.75rem;
      font-size: 0.78rem;
    }
    .step-chip strong { display: block; color: var(--navy); font-size: 0.8rem; }
    .step-chip span { color: var(--muted); }

    /* KPIs */
    .kpis {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem;
      margin-bottom: 1.5rem;
    }
    @media (max-width: 900px) { .kpis { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 520px) { .kpis { grid-template-columns: 1fr; } }
    .kpi {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.1rem 1.25rem;
      box-shadow: var(--shadow-sm);
    }
    .kpi-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.4rem;
    }
    .kpi-label {
      font-size: 0.76rem;
      font-weight: 600;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .kpi-icon {
      width: 28px;
      height: 28px;
      border-radius: 8px;
      background: var(--primary-soft);
      color: var(--primary);
      display: grid;
      place-items: center;
      font-size: 0.85rem;
      font-weight: 700;
    }
    .kpi-icon.danger { background: var(--danger-soft); color: var(--danger); }
    .kpi-icon.success { background: var(--success-soft); color: var(--success); }
    .kpi-value {
      font-size: 1.75rem;
      font-weight: 800;
      color: var(--navy);
      letter-spacing: -0.02em;
    }
    .kpi-sub { font-size: 0.79rem; color: var(--muted); margin-top: 0.15rem; }

    /* Main Workspace */
    .workspace {
      display: grid;
      grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.85fr);
      gap: 1.25rem;
      align-items: start;
      margin-bottom: 1.5rem;
    }
    @media (max-width: 980px) { .workspace { grid-template-columns: minmax(0, 1fr); } }

    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      box-shadow: var(--shadow-sm);
      overflow: hidden;
    }
    .card-header {
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 0.75rem;
      background: var(--surface);
    }
    .card-header h2 {
      font-size: 1rem;
      font-weight: 700;
      color: var(--navy);
    }
    .controls {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
    .input-sm {
      padding: 0.38rem 0.65rem;
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 0.82rem;
      color: var(--navy);
      background: var(--bg);
      font-family: inherit;
    }
    .input-sm:focus { outline: none; border-color: var(--primary); background: #fff; }

    /* Table */
    .table-wrap { overflow-x: auto; max-height: 540px; overflow-y: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
    thead th {
      position: sticky;
      top: 0;
      background: var(--bg);
      color: var(--muted);
      font-weight: 600;
      font-size: 0.74rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      text-align: left;
      padding: 0.7rem 1rem;
      border-bottom: 1px solid var(--border);
      z-index: 2;
    }
    tbody td {
      padding: 0.75rem 1rem;
      border-bottom: 1px solid var(--border);
      vertical-align: middle;
    }
    tbody tr { cursor: pointer; transition: background 0.12s; }
    tbody tr:hover { background: var(--bg); }
    tbody tr.active { background: var(--primary-soft); }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      padding: 0.22rem 0.6rem;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 700;
    }
    .badge-high { background: var(--danger-soft); color: var(--danger); border: 1px solid #fecaca; }
    .badge-med { background: var(--warning-soft); color: var(--warning); border: 1px solid #fde68a; }
    .badge-low { background: var(--success-soft); color: var(--success); border: 1px solid #a7f3d0; }
    .badge-neutral { background: var(--surface-alt); color: var(--navy); border: 1px solid var(--border); }

    /* Dossier */
    .card-body { padding: 1.2rem 1.25rem; }
    .dossier-overview {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 0.75rem;
      margin-bottom: 1rem;
      text-align: center;
    }
    .section-title {
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--muted);
      margin: 1rem 0 0.5rem;
    }
    .evidence-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.5rem;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.55rem 0.75rem;
      margin-bottom: 0.45rem;
      font-size: 0.82rem;
    }
    .evidence-item code {
      background: var(--surface);
      border: 1px solid var(--border);
      padding: 0.1rem 0.4rem;
      border-radius: 5px;
      font-size: 0.78rem;
      color: var(--navy);
    }

    .review-form {
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid var(--border);
      display: grid;
      gap: 0.65rem;
    }
    .review-form select,
    .review-form input,
    .review-form textarea {
      width: 100%;
      padding: 0.55rem 0.75rem;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--navy);
      font-size: 0.85rem;
      font-family: inherit;
    }
    .review-form select:focus,
    .review-form input:focus,
    .review-form textarea:focus {
      outline: none;
      border-color: var(--primary);
    }
    .status-msg { font-size: 0.82rem; font-weight: 600; min-height: 1.2rem; }

    /* Visual Architecture Section */
    .visuals-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.25rem;
      margin-bottom: 1.5rem;
    }
    @media (max-width: 900px) { .visuals-grid { grid-template-columns: 1fr; } }
    .visual-card img {
      width: 100%;
      height: auto;
      display: block;
      border-top: 1px solid var(--border);
      background: #ffffff;
    }

    .feedback { padding: 0.65rem 1rem; font-size: 0.82rem; color: var(--muted); }
    .pill-live[data-error] { color: #92400e; background: var(--warning-soft); border-color: #fde68a; }
    .feedback:empty { display: none; }
    .cluster-link {
      border: 0;
      background: transparent;
      color: var(--primary-hover);
      cursor: pointer;
      font: inherit;
      font-weight: 700;
      text-decoration: underline;
      text-underline-offset: 3px;
    }
    :is(button, a, input, select, textarea):focus-visible {
      outline: 2px solid var(--primary);
      outline-offset: 3px;
    }
    .dossier-summary { font-size: 0.9rem; overflow-wrap: anywhere; }
    .dossier-facts { color: var(--muted); font-size: 0.82rem; margin-top: 0.5rem; }
    .signals { padding-left: 1.25rem; font-size: 0.85rem; }
    .evidence-item code { overflow-wrap: anywhere; }
    .review-form label { font-size: 0.82rem; font-weight: 600; }
    .review-form button:disabled { opacity: 0.65; cursor: wait; }
    .review-hint { color: var(--muted); font-size: 0.8rem; }
    .members-list { overflow-wrap: anywhere; font-size: 0.82rem; }
    .members-list summary { cursor: pointer; }
    .members-list ul { padding-left: 1.25rem; margin-top: 0.5rem; }
    @media (max-width: 650px) {
      .topbar { position: static; }
      .brand-tag, .brand-divider { display: none; }
      .container { padding-inline: 0.85rem; }
      .hero { padding: 1.2rem; }
    }

    footer {
      border-top: 1px solid var(--border);
      padding: 1.25rem 0 0.5rem;
      font-size: 0.8rem;
      color: var(--muted);
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand">
        <img src="/logo.jpg" alt="RedRiesgo">
        <div class="brand-divider"></div>
        <span class="brand-tag">Desafío RIE-02 · Redes de Riesgo en Microfinanzas</span>
      </div>
      <div class="nav-actions">
        <span id="api-status" class="pill-live" role="status">Conectando…</span>
        <a class="btn" href="/docs">Swagger API</a>
        <a class="btn" href="/metrics">Métricas JSON</a>
        <a class="btn btn-primary" href="/clusters">Clústeres JSON</a>
      </div>
    </div>
  </header>

  <main class="container">
    <section class="hero">
      <div>
        <span class="hero-eyebrow">CAJATHON 2026 · Human-in-the-Loop</span>
        <h1>Inteligencia de Grafos para Detección Temprana de Redes de Fraude</h1>
        <p>
          Analiza relaciones ocultas entre solicitudes, personas, negocios, dispositivos, teléfonos y referencias.
          Filtra concentraciones comerciales legítimas (mercados) mediante ponderación IDF y genera expedientes
          auditables para priorizar la revisión humana, sin emitir decisiones crediticias automáticas.
        </p>
      </div>
      <div class="hero-steps">
        <div class="step-chip"><strong>1. Ingesta & Privacidad</strong><span>Datos tokenizados / hash</span></div>
        <div class="step-chip"><strong>2. Grafo Heterogéneo</strong><span>Pesos IDF + Hubs de mercado</span></div>
        <div class="step-chip"><strong>3. Motor de Detección</strong><span>Louvain, ciclos y ráfagas</span></div>
        <div class="step-chip"><strong>4. Revisión Humana</strong><span>Dossier con evidencia exacta</span></div>
      </div>
    </section>

    <section class="kpis">
      <div class="kpi">
        <div class="kpi-top"><span class="kpi-label">Solicitudes Analizadas</span><span class="kpi-icon">S</span></div>
        <div class="kpi-value" id="kpi-apps">—</div>
        <div class="kpi-sub">Cartera sintética ofuscada</div>
      </div>
      <div class="kpi">
        <div class="kpi-top"><span class="kpi-label">Nodos del Grafo</span><span class="kpi-icon">G</span></div>
        <div class="kpi-value" id="kpi-nodes">—</div>
        <div class="kpi-sub">Entidades + atributos</div>
      </div>
      <div class="kpi">
        <div class="kpi-top"><span class="kpi-label">Redes Priorizadas</span><span class="kpi-icon danger">!</span></div>
        <div class="kpi-value" id="kpi-clusters">—</div>
        <div class="kpi-sub">Clústeres sospechosos</div>
      </div>
      <div class="kpi">
        <div class="kpi-top"><span class="kpi-label">Precisión promedio / Recall</span><span class="kpi-icon success">✓</span></div>
        <div class="kpi-value" id="kpi-metrics">—</div>
        <div class="kpi-sub">Recall de miembros detectados</div>
      </div>
    </section>

    <section class="workspace">
      <div class="card">
        <div class="card-header">
          <h2>Bandeja de Clústeres Priorizados</h2>
          <div class="controls">
            <input id="search-box" class="input-sm" type="text" aria-label="Buscar por ID o patrón" placeholder="Buscar ID o patrón…" style="width:165px;">
            <label for="min-score" style="font-size:0.78rem;color:var(--muted);font-weight:600;">Riesgo ≥</label>
            <input id="min-score" class="input-sm" type="number" value="0" min="0" max="100" style="width:68px;">
          </div>
        </div>
        <p id="queue-status" class="feedback" role="status"></p>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Clúster</th>
                <th>Riesgo</th>
                <th>Solicitudes</th>
                <th>Señal Principal</th>
              </tr>
            </thead>
            <tbody id="clusters-body">
              <tr><td colspan="4" style="text-align:center;color:var(--muted);padding:2rem;">Cargando redes detectadas...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2>Expediente Auditable</h2>
          <span id="selected-id" class="badge badge-neutral" aria-live="polite">Selecciona un clúster</span>
        </div>
        <div class="card-body" id="dossier-panel">
          <p style="color:var(--muted);font-size:0.88rem;">
            Selecciona cualquier clúster de la bandeja para consultar sus señales y atributos compartidos, revisar la evidencia
            verificable y registrar tu decisión como analista.
          </p>
        </div>
      </div>
    </section>

    <section class="visuals-grid">
      <div class="card visual-card">
        <div class="card-header"><h2>Arquitectura del Sistema</h2><span class="badge badge-neutral">Pipeline RIE-02</span></div>
        <img src="/assets/arquitectura.jpg" alt="Arquitectura RedRiesgo">
      </div>
      <div class="card visual-card">
        <div class="card-header"><h2>Diferenciador: Hubs Legítimos vs. Redes de Riesgo</h2><span class="badge badge-neutral">Ponderación IDF</span></div>
        <img src="/assets/patrones-grafos.jpg" alt="Patrones de Grafos">
      </div>
    </section>

    <footer>
      <span><strong>RedRiesgo</strong> · Prototipo funcional para CAJATHON 2026 (RIE-02)</span>
      <span>100% datos sintéticos ofuscados · Apoyo a la decisión humana (sin rechazo automático)</span>
    </footer>
  </main>

  <noscript><p class="feedback">Activa JavaScript para consultar la bandeja y registrar decisiones.</p></noscript>
  <script>
    const byId = id => document.getElementById(id);
    const number = new Intl.NumberFormat('es-PE');
    const decimal = new Intl.NumberFormat('es-PE', { maximumFractionDigits: 2 });
    const decisionLabels = {
      pendiente: 'Pendiente',
      confirmado: 'Riesgo confirmado',
      descartado: 'Descartado',
      falso_positivo: 'Falso positivo'
    };
    const attributeLabels = {
      address: 'Dirección', phone: 'Teléfono', device: 'Dispositivo',
      reference: 'Referencia', geocell: 'Zona geográfica'
    };
    const entities = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
    const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => entities[char]);
    const format = (value, formatter = number) =>
      value == null || value === '' || !Number.isFinite(Number(value)) ? '—' : formatter.format(Number(value));

    let allClusters = [];
    let activeClusterId = null;
    let activeRequest;
    let queueReady = false;
    const decisions = new Map();

    function list(value) {
      try {
        const items = typeof value === 'string' ? JSON.parse(value) : value;
        return Array.isArray(items) ? items : [];
      } catch {
        return [];
      }
    }

    async function json(url, options) {
      const response = await fetch(url, options);
      const body = await response.json().catch(() => null);
      if (!response.ok || body === null) {
        throw new Error(typeof body?.detail === 'string' ? body.detail : 'La API no pudo completar la solicitud.');
      }
      return body;
    }

    function scoreBadge(score) {
      if (Number(score) >= 75) return `<span class="badge badge-high">Crítico · ${format(score, decimal)}</span>`;
      if (Number(score) >= 55) return `<span class="badge badge-med">Alto · ${format(score, decimal)}</span>`;
      return `<span class="badge badge-low">${format(score, decimal)}</span>`;
    }

    async function loadDashboard() {
      const [statsResult, metricsResult, clustersResult, queueResult] = await Promise.allSettled([
        json('/stats'), json('/metrics'), json('/clusters?limit=1000'), json('/review/queue?limit=500')
      ]);
      const stats = statsResult.value ?? {};
      const metrics = metricsResult.value ?? {};
      const graph = stats.graph?.stats ?? stats.graph ?? {};
      const count = stats.detection?.stats?.n_clusters ?? metrics.cluster?.n_clusters;
      byId('kpi-apps').textContent = format(graph.n_applications ?? metrics.application?.n_applications);
      byId('kpi-nodes').textContent = format(graph.n_bipartite_nodes ?? stats.graph?.counts?.bipartite_nodes);
      byId('kpi-metrics').textContent =
        `${format(metrics.application?.average_precision, decimal)} / ${format(metrics.cluster?.ring_recall, decimal)}`;

      queueReady = Array.isArray(clustersResult.value);
      const unavailable = !queueReady || [statsResult, metricsResult, queueResult].some(result => result.status === 'rejected');
      byId('api-status').toggleAttribute('data-error', unavailable);
      byId('api-status').textContent = unavailable
        ? 'Algunos datos no están disponibles' : 'API conectada';
      byId('kpi-clusters').textContent = format(count ?? clustersResult.value?.length);
      if (!queueReady) {
        byId('clusters-body').textContent = '';
        byId('queue-status').innerHTML = 'No se pudo cargar la bandeja. <button class="cluster-link" type="button">Reintentar</button>';
        byId('queue-status').querySelector('button').addEventListener('click', loadDashboard, { once: true });
        return;
      }

      allClusters = clustersResult.value;
      for (const item of list(queueResult.value)) decisions.set(item.cluster_id, item.decision);
      renderClusters();
      if (allClusters.length) selectCluster(allClusters[0].cluster_id);
    }

    function renderClusters() {
      if (!queueReady) return;
      const threshold = Math.max(0, Math.min(100, Number(byId('min-score').value) || 0));
      const query = byId('search-box').value.trim().toLocaleLowerCase('es');
      const visible = allClusters.filter(cluster =>
        Number(cluster.risk_score) >= threshold &&
        [cluster.cluster_id, ...list(cluster.reasons)].join(' ').toLocaleLowerCase('es').includes(query)
      );
      byId('queue-status').textContent = visible.length
        ? `${number.format(visible.length)} de ${number.format(allClusters.length)} clústeres cargados`
        : allClusters.length ? 'No hay clústeres que coincidan con los filtros.' : 'La bandeja está vacía.';
      byId('clusters-body').innerHTML = visible.map(cluster => {
        const id = escapeHtml(cluster.cluster_id);
        const selected = cluster.cluster_id === activeClusterId;
        const decision = decisionLabels[decisions.get(cluster.cluster_id)] ?? '—';
        return `
          <tr data-cluster="${id}" class="${selected ? 'active' : ''}">
            <td><button class="cluster-link" type="button" aria-pressed="${selected}">${id}</button>
              <div class="review-hint">${decision}</div></td>
            <td>${scoreBadge(cluster.risk_score)}</td>
            <td>${format(cluster.size)}</td>
            <td>${escapeHtml(list(cluster.reasons)[0] ?? '—')}</td>
          </tr>`;
      }).join('');
    }

    async function selectCluster(clusterId) {
      activeRequest?.abort();
      const request = new AbortController();
      activeRequest = request;
      activeClusterId = clusterId;
      for (const row of byId('clusters-body').rows) {
        const selected = row.dataset.cluster === clusterId;
        row.classList.toggle('active', selected);
        row.querySelector('button').setAttribute('aria-pressed', String(selected));
      }
      byId('selected-id').textContent = clusterId;
      const panel = byId('dossier-panel');
      panel.setAttribute('aria-busy', 'true');
      panel.innerHTML = '<p role="status">Cargando expediente…</p>';
      try {
        const { cluster, dossier } = await json(`/clusters/${encodeURIComponent(clusterId)}`, { signal: request.signal });
        if (request.signal.aborted) return;
        renderDossier(cluster, dossier);
      } catch {
        if (request.signal.aborted) return;
        panel.innerHTML = '<p role="alert">No se pudo cargar el expediente.</p><button type="button" class="cluster-link">Reintentar</button>';
        panel.querySelector('button').addEventListener('click', () => selectCluster(clusterId));
      } finally {
        if (!request.signal.aborted) panel.removeAttribute('aria-busy');
      }
    }

    function renderDossier(cluster, dossier = {}) {
      const reasons = list(dossier.reasons ?? cluster.reasons);
      const evidence = list(dossier.shared_attributes ?? cluster.top_evidence);
      const members = list(dossier.members ?? cluster.members);
      const decision = decisions.get(cluster.cluster_id);
      const attributes = evidence.map(item => `
        <div class="evidence-item">
          <div><strong>${escapeHtml(attributeLabels[item.type] ?? item.type)}</strong><br><code>${escapeHtml(item.value_hash)}</code></div>
          <span class="badge badge-neutral">Peso ${format(item.weight, decimal)}</span>
        </div>`).join('');
      const panel = byId('dossier-panel');
      panel.innerHTML = `
        <div class="dossier-overview">
          <p class="dossier-summary"><strong>${escapeHtml(dossier.summary ?? reasons[0] ?? 'Resumen no disponible')}</strong></p>
          <p class="dossier-facts">${scoreBadge(cluster.risk_score)} · ${format(cluster.size)} solicitudes · ${format(cluster.n_edges)} conexiones</p>
          <p class="dossier-facts">Ventana temporal · ${format(dossier.time_window?.span_hours ?? cluster.time_span_hours, decimal)} h</p>
        </div>
        <h3 class="section-title">Señales detectadas</h3>
        ${reasons.length ? `<ul class="signals">${reasons.map(reason => `<li>${escapeHtml(reason)}</li>`).join('')}</ul>` : '<p>No hay señales detalladas disponibles.</p>'}
        <h3 class="section-title">Atributos compartidos</h3>
        ${attributes || '<p>No hay atributos compartidos en el expediente.</p>'}
        ${members.length ? `<details class="members-list">
          <summary>Solicitudes vinculadas (${number.format(members.length)})</summary>
          <ul>${members.map(member => `<li><code>${escapeHtml(member.application_id ?? member)}</code></li>`).join('')}</ul>
        </details>` : ''}
        <form class="review-form">
          <h3 class="section-title">Decisión del analista</h3>
          <p class="review-hint">Estado registrado: <strong id="recorded-decision">${decisionLabels[decision] ?? 'Sin información'}</strong></p>
          <label for="rev-decision">Resultado de revisión</label>
          <select id="rev-decision" name="decision">
            ${Object.entries(decisionLabels).map(([value, label]) =>
              `<option value="${value}" ${value === decision ? 'selected' : ''}>${label}</option>`).join('')}
          </select>
          <label for="rev-name">Nombre del analista</label>
          <input id="rev-name" name="reviewer" type="text" required pattern=".*\S.*">
          <label for="rev-notes">Observaciones</label>
          <textarea id="rev-notes" name="notes" rows="2"></textarea>
          <button class="btn btn-primary" type="submit">Registrar decisión</button>
          <p class="status-msg" role="status"></p>
        </form>`;
      panel.querySelector('form').addEventListener('submit', event => submitDecision(event, cluster.cluster_id));
    }

    async function submitDecision(event, clusterId) {
      event.preventDefault();
      const form = event.currentTarget;
      const button = form.querySelector('button');
      const status = form.querySelector('[role="status"]');
      const fields = new FormData(form);
      button.disabled = true;
      status.textContent = 'Registrando…';
      try {
        const result = await json('/review/decision', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            cluster_id: clusterId,
            decision: fields.get('decision'),
            reviewer: fields.get('reviewer').trim(),
            notes: fields.get('notes').trim()
          })
        });
        decisions.set(clusterId, result.decision);
        renderClusters();
        if (form.isConnected) byId('recorded-decision').textContent = decisionLabels[result.decision];
        status.textContent = 'Decisión registrada.';
      } catch (error) {
        status.textContent = `No se pudo registrar la decisión. ${error.message}`;
      } finally {
        button.disabled = false;
      }
    }

    byId('clusters-body').addEventListener('click', event => {
      const row = event.target.closest('tr[data-cluster]');
      if (row) selectCluster(row.dataset.cluster);
    });
    byId('min-score').addEventListener('input', renderClusters);
    byId('search-box').addEventListener('input', renderClusters);
    loadDashboard();
  </script>
</body>
</html>
"""
