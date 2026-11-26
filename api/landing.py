"""Página web demostrativa de RedRiesgo servida en la raíz de FastAPI."""

LANDING_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RedRiesgo — Inteligencia de Grafos para Microfinanzas</title>
  <style>
    :root {
      --bg: #0b1120;
      --surface: #111827;
      --surface-2: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --muted: #94a3b8;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --danger: #ef4444;
      --warning: #f59e0b;
      --success: #10b981;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }
    .container { max-width: 1200px; margin: 0 auto; padding: 1.5rem; }
    header {
      display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;
      gap: 1rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--border);
    }
    .brand { display: flex; align-items: center; gap: 0.75rem; }
    .logo-badge {
      width: 40px; height: 40px; border-radius: 10px;
      background: linear-gradient(135deg, var(--primary), #1d4ed8);
      display: grid; place-items: center; font-weight: 800; font-size: 1.1rem;
      box-shadow: 0 0 20px rgba(59,130,246,0.35);
    }
    .brand h1 { font-size: 1.35rem; font-weight: 700; letter-spacing: -0.02em; }
    .brand p { font-size: 0.85rem; color: var(--muted); }
    .nav-links { display: flex; gap: 0.75rem; flex-wrap: wrap; }
    .btn {
      display: inline-flex; align-items: center; gap: 0.4rem;
      padding: 0.5rem 0.9rem; border-radius: 8px; font-size: 0.85rem; font-weight: 600;
      text-decoration: none; cursor: pointer; border: 1px solid var(--border);
      background: var(--surface-2); color: var(--text); transition: 0.15s;
    }
    .btn:hover { border-color: var(--primary); color: #fff; }
    .btn-primary { background: var(--primary); border-color: var(--primary); }
    .btn-primary:hover { background: var(--primary-hover); }

    .hero {
      margin: 1.5rem 0; padding: 1.5rem; border-radius: 14px;
      background: linear-gradient(135deg, rgba(37,99,235,0.14), rgba(15,23,42,0.9));
      border: 1px solid rgba(59,130,246,0.3);
    }
    .hero h2 { font-size: 1.25rem; margin-bottom: 0.4rem; }
    .hero p { color: var(--muted); font-size: 0.95rem; max-width: 820px; }

    .kpis {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem; margin: 1.5rem 0;
    }
    .kpi {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 12px; padding: 1rem 1.2rem;
    }
    .kpi .label { font-size: 0.78rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
    .kpi .value { font-size: 1.65rem; font-weight: 700; margin-top: 0.25rem; }
    .kpi .sub { font-size: 0.8rem; color: var(--muted); margin-top: 0.2rem; }

    .grid {
      display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 1.25rem;
      align-items: start;
    }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }

    .panel {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 12px; overflow: hidden;
    }
    .panel-header {
      padding: 0.9rem 1.2rem; border-bottom: 1px solid var(--border);
      display: flex; justify-content: space-between; align-items: center; gap: 0.75rem;
    }
    .panel-header h3 { font-size: 1rem; font-weight: 600; }
    .panel-body { padding: 1rem 1.2rem; }

    table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
    th, td { text-align: left; padding: 0.65rem 0.5rem; border-bottom: 1px solid var(--border); }
    th { color: var(--muted); font-weight: 600; font-size: 0.78rem; text-transform: uppercase; }
    tbody tr { cursor: pointer; transition: background 0.12s; }
    tbody tr:hover { background: rgba(59,130,246,0.08); }
    tbody tr.active { background: rgba(59,130,246,0.16); }

    .badge {
      display: inline-block; padding: 0.2rem 0.55rem; border-radius: 999px;
      font-size: 0.75rem; font-weight: 600;
    }
    .badge-high { background: rgba(239,68,68,0.18); color: #fca5a5; }
    .badge-med { background: rgba(245,158,11,0.18); color: #fcd34d; }
    .badge-low { background: rgba(16,185,129,0.18); color: #6ee7b7; }

    .dossier-box { font-size: 0.88rem; }
    .dossier-box h4 { margin: 0.9rem 0 0.35rem; font-size: 0.9rem; color: var(--primary); }
    .evidence-item {
      background: var(--surface-2); border: 1px solid var(--border);
      border-radius: 8px; padding: 0.55rem 0.75rem; margin-bottom: 0.45rem;
      font-size: 0.82rem;
    }
    .review-form {
      margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border);
      display: grid; gap: 0.65rem;
    }
    select, input, textarea {
      width: 100%; padding: 0.55rem 0.7rem; border-radius: 8px;
      border: 1px solid var(--border); background: var(--bg); color: var(--text);
      font-size: 0.85rem; font-family: inherit;
    }
    .status-msg { font-size: 0.82rem; margin-top: 0.35rem; color: var(--success); }
    footer {
      margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border);
      font-size: 0.8rem; color: var(--muted); display: flex; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <div class="logo-badge">RR</div>
        <div>
          <h1>RedRiesgo</h1>
          <p>Inteligencia de Grafos para Detección Temprana de Redes de Fraude · RIE-02</p>
        </div>
      </div>
      <div class="nav-links">
        <a class="btn" href="/docs">API Swagger</a>
        <a class="btn" href="/metrics">Métricas JSON</a>
        <a class="btn btn-primary" href="/clusters">Datos Crudos</a>
      </div>
    </header>

    <section class="hero">
      <h2>Priorización auditable de redes de riesgo en microfinanzas</h2>
      <p>
        Modela relaciones ocultas entre solicitudes, personas, negocios, teléfonos, dispositivos, direcciones y geoceldas.
        Filtra nodos legítimos de alta concurrencia (mercados) mediante ponderación IDF y entrega expedientes con evidencia
        verificable para revisión humana, sin decisiones crediticias automáticas.
      </p>
    </section>

    <section class="kpis" id="kpis">
      <div class="kpi"><div class="label">Solicitudes analizadas</div><div class="value" id="kpi-apps">—</div><div class="sub">Cartera sintética</div></div>
      <div class="kpi"><div class="label">Nodos en grafo</div><div class="value" id="kpi-nodes">—</div><div class="sub">Entidades + atributos</div></div>
      <div class="kpi"><div class="label">Clústeres priorizados</div><div class="value" id="kpi-clusters">—</div><div class="sub">Redes sospechosas</div></div>
      <div class="kpi"><div class="label">PR-AUC / F1</div><div class="value" id="kpi-metrics">—</div><div class="sub">Evaluación del modelo</div></div>
    </section>

    <section class="grid">
      <div class="panel">
        <div class="panel-header">
          <h3>Clústeres de Riesgo Detectados</h3>
          <div style="display:flex;align-items:center;gap:0.5rem;">
            <label for="min-score" style="font-size:0.8rem;color:var(--muted);">Score mín:</label>
            <input id="min-score" type="number" value="0" min="0" max="100" style="width:72px;padding:0.3rem 0.5rem;">
          </div>
        </div>
        <div class="panel-body" style="padding:0; overflow-x:auto;">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Score</th>
                <th>Tamaño</th>
                <th>Tipología / Señal</th>
              </tr>
            </thead>
            <tbody id="clusters-body">
              <tr><td colspan="4" style="text-align:center;color:var(--muted);padding:1.5rem;">Cargando clústeres...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <h3>Expediente y Revisión Humana</h3>
          <span id="selected-id" class="badge badge-low">Selecciona un clúster</span>
        </div>
        <div class="panel-body dossier-box" id="dossier-panel">
          <p style="color:var(--muted);">Haz clic en cualquier fila de la tabla para inspeccionar su expediente auditable, la evidencia exacta y registrar una decisión.</p>
        </div>
      </div>
    </section>

    <footer>
      <span>RedRiesgo · Prototipo CAJATHON 2026 (RIE-02)</span>
      <span>100% datos sintéticos ofuscados · Human-in-the-Loop</span>
    </footer>
  </div>

  <script>
    let allClusters = [];
    let activeClusterId = null;

    function scoreBadge(score) {
      const s = Number(score || 0);
      if (s >= 75) return `<span class="badge badge-high">${s.toFixed(1)}</span>`;
      if (s >= 45) return `<span class="badge badge-med">${s.toFixed(1)}</span>`;
      return `<span class="badge badge-low">${s.toFixed(1)}</span>`;
    }

    async function loadDashboard() {
      try {
        const [statsRes, metricsRes, clustersRes] = await Promise.all([
          fetch('/stats'), fetch('/metrics'), fetch('/clusters?limit=50')
        ]);
        const stats = await statsRes.json();
        const metrics = await metricsRes.json();
        allClusters = await clustersRes.json();

        document.getElementById('kpi-apps').textContent = stats?.graph?.n_applications ?? '—';
        const entities = stats?.graph?.n_entities ?? 0;
        const attrs = stats?.graph?.n_attributes ?? 0;
        document.getElementById('kpi-nodes').textContent = (entities + attrs) || '—';
        document.getElementById('kpi-clusters').textContent = allClusters.length;

        const prAuc = metrics?.pr_auc ?? metrics?.application_pr_auc;
        const f1 = metrics?.f1 ?? metrics?.application_f1;
        document.getElementById('kpi-metrics').textContent =
          (prAuc !== undefined) ? `${Number(prAuc).toFixed(2)} / ${Number(f1 || 0).toFixed(2)}` : 'Disponible en /metrics';

        renderClusters();
        if (allClusters.length > 0) {
          selectCluster(allClusters[0].cluster_id);
        }
      } catch (err) {
        console.error(err);
      }
    }

    function renderClusters() {
      const minScore = Number(document.getElementById('min-score').value || 0);
      const tbody = document.getElementById('clusters-body');
      const filtered = allClusters.filter(c => Number(c.risk_score || 0) >= minScore);
      if (!filtered.length) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:1.5rem;">Sin resultados para ese filtro.</td></tr>';
        return;
      }
      tbody.innerHTML = filtered.map(c => `
        <tr class="${c.cluster_id === activeClusterId ? 'active' : ''}" onclick="selectCluster('${c.cluster_id}')">
          <td><strong>${c.cluster_id}</strong></td>
          <td>${scoreBadge(c.risk_score)}</td>
          <td>${c.size || c.n_applications || '—'}</td>
          <td style="color:var(--muted);">${c.dominant_pattern || c.pattern || 'Red de atributos'}</td>
        </tr>
      `).join('');
    }

    async function selectCluster(clusterId) {
      activeClusterId = clusterId;
      renderClusters();
      document.getElementById('selected-id').textContent = clusterId;
      const panel = document.getElementById('dossier-panel');
      panel.innerHTML = '<p style="color:var(--muted);">Cargando expediente...</p>';

      try {
        const res = await fetch(`/clusters/${encodeURIComponent(clusterId)}`);
        const data = await res.json();
        const c = data.cluster || {};
        const d = data.dossier || {};
        const evidences = Array.isArray(d.evidence) ? d.evidence : (Array.isArray(d.top_attributes) ? d.top_attributes : []);

        const evHtml = evidences.length
          ? evidences.slice(0, 6).map(e => `
              <div class="evidence-item">
                <strong>${e.type || e.attribute_type || 'Atributo'}</strong>:
                <code>${e.value_hash || e.attribute || e.id || 'hash'}</code>
                ${e.weight ? ` · peso ${Number(e.weight).toFixed(2)}` : ''}
              </div>
            `).join('')
          : '<div class="evidence-item">Resumen de evidencia disponible en el dossier completo.</div>';

        panel.innerHTML = `
          <p><strong>Score de riesgo:</strong> ${Number(c.risk_score || 0).toFixed(2)} · <strong>Solicitudes:</strong> ${c.size || c.n_applications || '—'}</p>
          <h4>Evidencia principal</h4>
          ${evHtml}
          <form class="review-form" onsubmit="submitDecision(event, '${clusterId}')">
            <h4>Registrar decisión (Human-in-the-Loop)</h4>
            <select id="rev-decision">
              <option value="en_investigacion">En investigación</option>
              <option value="confirmado_riesgo">Confirmado riesgo</option>
              <option value="falso_positivo">Falso positivo</option>
            </select>
            <input id="rev-name" type="text" placeholder="Nombre del analista" value="analista_demo" required>
            <textarea id="rev-notes" rows="2" placeholder="Observaciones para auditoría..."></textarea>
            <button class="btn btn-primary" type="submit">Guardar decisión</button>
            <div id="rev-status" class="status-msg"></div>
          </form>
        `;
      } catch (err) {
        panel.innerHTML = '<p style="color:var(--danger);">No se pudo cargar el expediente.</p>';
      }
    }

    async function submitDecision(e, clusterId) {
      e.preventDefault();
      const status = document.getElementById('rev-status');
      status.textContent = 'Guardando...';
      try {
        const res = await fetch('/review/decision', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            cluster_id: clusterId,
            decision: document.getElementById('rev-decision').value,
            reviewer: document.getElementById('rev-name').value,
            notes: document.getElementById('rev-notes').value
          })
        });
        if (!res.ok) throw new Error('Error al guardar');
        status.textContent = 'Decisión registrada correctamente.';
      } catch (err) {
        status.style.color = 'var(--danger)';
        status.textContent = 'No se pudo registrar la decisión (entorno solo lectura o error).';
      }
    }

    document.getElementById('min-score').addEventListener('input', renderClusters);
    loadDashboard();
  </script>
</body>
</html>
"""
