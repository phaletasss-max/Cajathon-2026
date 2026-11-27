"""Interfaz web de la plataforma RedRiesgo."""

PLATFORM_HTML = r"""<!doctype html>
<html lang="es" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Plataforma · RedRiesgo</title>
<link rel="icon" href="/logo.jpg">
<style>
:root{color-scheme:light;--bg:#f1f6f3;--paper:#fff;--ink:#142d24;--muted:#48635a;--line:#d3e1da;--brand:#175d46;--on:#fff;--soft:#e4f2e9}
[data-theme=dark]{color-scheme:dark;--bg:#111b17;--paper:#192822;--ink:#effaf3;--muted:#bad0c3;--line:#395147;--brand:#a6e9bb;--on:#11281e;--soft:#233d31}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,sans-serif}
a{color:var(--brand)} button,select,input,textarea{font:inherit;color:inherit}
:focus-visible{outline:3px solid var(--brand);outline-offset:2px}
header{background:var(--paper);border-bottom:1px solid var(--line)}
nav,main,footer{width:min(1450px,calc(100% - 40px));margin:auto}
nav{display:flex;flex-wrap:wrap;align-items:center;gap:.8rem;padding:.7rem 0}
nav img{display:block;width:88px;border-radius:8px}
nav a{font-size:.9rem;font-weight:650;text-decoration:none}
nav a[aria-current]{text-decoration:underline;text-underline-offset:5px}
nav button{margin-left:auto}
main{padding:clamp(24px,5vw,54px) 0}
h1{font-size:clamp(2rem,5vw,3.7rem);letter-spacing:-.055em;line-height:1.05;margin:.25rem 0 1rem}
h2,h3{line-height:1.2}
p,ul{margin:.5rem 0 1rem}
.kicker{text-transform:uppercase;letter-spacing:.13em;font-weight:750;font-size:.78rem;color:var(--brand)}
.muted{color:var(--muted)} .small{font-size:.87rem}
.panel{min-width:0;border:1px solid var(--line);background:var(--paper);border-radius:16px;padding:clamp(14px,2vw,23px);margin-bottom:16px}
.panel h2,.panel h3{margin-top:0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,225px),1fr));gap:14px}
.kpi strong{display:block;font-size:1.65rem;color:var(--brand)}
.case-grid{display:grid;grid-template-columns:minmax(190px,.8fr) minmax(340px,1.65fr) minmax(230px,1fr);gap:13px}
.filters{display:flex;flex-wrap:wrap;align-items:end;gap:12px}
label{display:grid;gap:3px;font-size:.87rem;font-weight:650}
button,.button,input,select,textarea{padding:.52rem .7rem;border:1px solid var(--line);border-radius:8px;background:var(--paper)}
button,.button{cursor:pointer;font-weight:700;text-decoration:none}
.primary{color:var(--on);background:var(--brand);border-color:var(--brand)}
button:disabled{opacity:.6;cursor:default}
table{width:100%;border-collapse:collapse;font-size:.92rem}
th,td{padding:.65rem .6rem;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th button{white-space:nowrap;padding:.2rem .4rem}
.scroll{overflow:auto}
.form{display:grid;gap:9px}
.form textarea{width:100%}
.badge{display:inline-block;background:var(--soft);border-radius:999px;padding:.12rem .55rem}
.bar-row{display:grid;grid-template-columns:minmax(84px,1fr) 2fr auto;gap:9px;align-items:center;margin:.4rem 0;font-size:.84rem}
.bar{height:10px;background:var(--soft);border-radius:9px}
.bar i{display:block;height:100%;background:var(--brand);border-radius:9px}
canvas{display:block;width:100%;min-height:360px;background:var(--bg);border:1px solid var(--line);border-radius:12px}
.graph-options{margin:12px 0}
code,td,.node-detail{overflow-wrap:anywhere}
details{margin:12px 0}
summary{cursor:pointer;color:var(--brand);font-weight:700}
figure{margin:0} figure img{max-width:100%;border-radius:12px}
footer{padding:0 0 28px;color:var(--muted);font-size:.87rem}
@media(max-width:1020px){.case-grid{grid-template-columns:1fr 1fr}.graph-panel{grid-column:1 / -1;grid-row:1}}
@media(max-width:680px){nav,main,footer{width:calc(100% - 24px)}.case-grid{grid-template-columns:minmax(0,1fr)}nav button{margin-left:0}}
@media print{nav,footer,.graph-options,.form,.button{display:none}.case-grid{display:block}.panel{break-inside:avoid}body{background:white;color:black}}
</style>
</head>
<body>
<header><nav aria-label="Navegación principal">
<a href="/"><img src="/logo.jpg" alt="RedRiesgo"></a>
<a href="/app/panel">Panel</a><a href="/app/alertas">Alertas</a><a href="/app/bitacora">Bitácora</a>
<a href="/validacion">Validación</a><a href="/metodologia">Metodología</a><a href="/privacidad">Privacidad</a>
<button id="theme" type="button">Modo oscuro</button>
</nav></header>
<main id="main" aria-busy="true"><p role="status">Cargando plataforma…</p></main>
<footer>Cartera sintética · Expediente RIE-02 · <a href="/docs">API</a></footer>
<script>
const main = document.getElementById('main');
const theme = document.getElementById('theme');
const root = document.documentElement;
const byId = id => document.getElementById(id);
const route = location.pathname.replace(/\/$/, '') || '/app';
const formats = new Intl.NumberFormat('es-PE', {maximumFractionDigits:2});
const currency = new Intl.NumberFormat('es-PE',{style:'currency',currency:'PEN',maximumFractionDigits:2});
const fmt = value => value == null || value === '' ? '—' : formats.format(value);
const pen = value => value == null ? '—' : currency.format(value);
const pct = value => value == null ? '—' : fmt(value * 100) + ' %';
const special = {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'};
const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => special[ch]);
const states = {pendiente:'Pendiente',confirmado:'Confirmado',falso_positivo:'Falso positivo',descartado:'Descartado',en_seguimiento:'En seguimiento',escalado:'Escalado'};
const types = {application:'Solicitud',person:'Persona',business:'Negocio',phone:'Teléfono',device:'Dispositivo',address:'Dirección',geocell:'Zona',reference:'Referencia'};
const heading = (tag,title,description) => `<p class="kicker">${tag}</p><h1>${title}</h1><p class="muted">${description}</p>`;
const link = row => '/app/caso/' + encodeURIComponent(row.cluster_id);
const status = (row, latest) => latest.get(row.cluster_id)?.decision ?? 'pendiente';
const latestDecisions = events => new Map(events.map(event => [event.cluster_id,event]));
const priority = row => (row.exposure_pen ?? 0) * row.evidence_count;
function type(row) {
  const signal = (Array.isArray(row.reasons) ? row.reasons[0] : JSON.parse(row.reasons || '[]')[0]) || '';
  if (row.source === 'ref_scc') return 'Ciclo de referencias';
  if (signal.startsWith('Ráfaga')) return 'Ráfaga temporal';
  if (signal.startsWith('Teléfono')) return 'Teléfono compartido';
  if (signal.startsWith('Dispositivo')) return 'Dispositivo compartido';
  return 'Red de atributos';
}
async function api(url,options) {
  const response = await fetch(url,options);
  const result = await response.json();
  if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'No se pudo completar la consulta.');
  return result;
}
let redrawGraph = () => {};
function setTheme(value) {
  root.dataset.theme = value;
  theme.textContent = value === 'dark' ? 'Modo claro' : 'Modo oscuro';
  redrawGraph();
}
try { setTheme(localStorage.getItem('redriesgo-theme') ?? (matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light')); } catch {}
theme.addEventListener('click',()=>{
  setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark');
  try {localStorage.setItem('redriesgo-theme',root.dataset.theme);} catch {}
});
for (const item of document.querySelectorAll('nav a')) if (item.getAttribute('href') === route) item.setAttribute('aria-current','page');

function alertTable(rows, latest, experimentK = null) {
  return rows.length ? rows.map(row => `<tr><td><a href="${link(row)}${experimentK===null ? "" : "?k="+encodeURIComponent(experimentK)}">${esc(row.cluster_id)}</a></td><td>${type(row)}</td><td>${fmt(row.risk_score)}</td><td>${fmt(row.size)}</td><td>${pen(row.exposure_pen)}</td><td>${fmt(row.evidence_count)}</td><td><span class="badge">${experimentK!==null ? 'Simulación' : states[status(row,latest)]}</span></td></tr>`).join('') : '<tr><td colspan="7">Sin resultados.</td></tr>';
}
function table(allowSort) {
  const cols = [['cluster_id','Caso'],['type','Tipología'],['risk_score','Score'],['size','Solicitudes'],['exposure_pen','Exposición'],['evidence_count','Evidencias'],['state','Estado']];
  return `<div class="scroll"><table><thead><tr>${cols.map(([key,label])=>`<th scope="col">${allowSort ? `<button type="button" data-sort="${key}">${label}</button>` : label}</th>`).join('')}</tr></thead><tbody id="alert-rows"></tbody></table></div>`;
}
function bars(items) {
  const peak = Math.max(1,...items.map(([,value])=>value));
  return items.map(([label,value])=>`<div class="bar-row"><span>${esc(label)}</span><span class="bar" aria-hidden="true"><i style="width:${value/peak*100}%"></i></span><strong>${fmt(value)}</strong></div>`).join('');
}
function panel(rows,latest) {
  const totals = new Map();
  const months = new Map();
  for (const row of rows) {
    totals.set(type(row),(totals.get(type(row)) ?? 0)+1);
    const month = row.date_end?.slice(0,7);
    if(month) months.set(month,(months.get(month) ?? 0)+1);
  }
  const pending=rows.filter(row=>status(row,latest)==='pendiente').length;
  const confirmed=rows.filter(row=>status(row,latest)==='confirmado').length;
  const discarded=rows.filter(row=>['descartado','falso_positivo'].includes(status(row,latest))).length;
  const amount=rows.reduce((sum,row)=>sum+(row.exposure_pen ?? 0),0);
  const cases=[[rows.length,'Clústeres detectados'],[new Set(rows.flatMap(row=>JSON.parse(row.members))).size,'Solicitudes únicas alertadas'],[rows.some(row=>row.exposure_pen!=null)?pen(amount):'—','Exposición bruta de los casos'],[`${pending} / ${confirmed} / ${discarded}`,'Pendientes / confirmados / descartados']];
  main.innerHTML = heading('Panel ejecutivo','Prioridades de investigación','Montos solicitados por clúster. Una solicitud vinculada a varios casos puede aparecer en más de un subtotal.') +
    `<div class="grid">${cases.map(([value,label])=>`<div class="panel kpi"><strong>${esc(value)}</strong>${label}</div>`).join('')}</div>
    <div class="grid"><section class="panel"><h2>Alertas por tipología</h2>${bars([...totals])}</section>
    <section class="panel"><h2>Alertas por mes de cierre</h2>${bars([...months].sort())}</section>
    <section class="panel"><h2>Distribución del score</h2>${bars([[0,59],[60,69],[70,79],[80,89],[90,100]].map(([start,end])=>[start+'–'+end,rows.filter(row=>row.risk_score>=start&&row.risk_score<end+1).length]))}</section></div>
    <section class="panel"><h2>Top 5 por exposición × evidencia</h2>${table(false)}</section><a class="button primary" href="/app/alertas">Revisar alertas</a>`;
  byId('alert-rows').innerHTML=alertTable([...rows].sort((a,b)=>priority(b)-priority(a)).slice(0,5),latest);
}
function alerts(original,latest) {
  main.innerHTML=heading('Bandeja','Alertas priorizadas','Filtra las alertas de la cartera y abre sus expedientes.')+
    `<section class="panel"><div class="filters">
    <label>Tipología<select id="type"><option value="">Todas</option>${[...new Set(original.map(type))].map(value=>`<option>${value}</option>`).join('')}</select></label>
    <label>Score mínimo<input id="min" type="number" min="0" max="100" value="0"></label>
    <label>Score máximo<input id="max" type="number" min="0" max="100" value="100"></label>
    <label>Estado<select id="state"><option value="">Todos</option>${Object.entries(states).map(([key,value])=>`<option value="${key}">${value}</option>`).join('')}</select></label>
    <label>Canal<select id="channel"><option value="">Todos</option>${[...new Set(original.flatMap(row=>row.channels))].sort().map(value=>`<option>${esc(value)}</option>`).join('')}</select></label><label>Desde<input id="date" type="date"></label></div><p class="muted small">La muestra separa canales de atención y carece de identificadores de agencia.</p>${table(true)}</section>
    <section class="panel"><h2>Ejecutar análisis</h2><p class="muted">Recalcula la muestra sintética y compara los resultados con el umbral de la cartera de referencia. Los experimentos se muestran aquí con identificadores de esa ejecución.</p>
    <form id="run" class="filters"><label>Umbral k de hubs<input id="k" type="number" min="2" max="50" value="25" required></label><button class="primary">Ejecutar análisis</button></form>
    <p id="run-status" role="status"></p><div id="experiment"></div></section>`;
  let sort='exposure_pen', direction=-1;
  const field = (row,key) => key==='type' ? type(row) : key==='state' ? states[status(row,latest)] : ['risk_score','size','exposure_pen','evidence_count'].includes(key) ? Number(row[key] ?? -1) : row[key];
  function render() {
    const list=original.filter(row=>(!byId('type').value||type(row)===byId('type').value)&& row.risk_score>=Number(byId('min').value||0) && row.risk_score<=Number(byId('max').value||100) && (!byId('state').value||status(row,latest)===byId('state').value) && (!byId('channel').value || row.channels.includes(byId('channel').value)) && (!byId('date').value||(row.date_end??'')>=byId('date').value));
    list.sort((a,b)=>{const x=field(a,sort),y=field(b,sort);return direction*(typeof x==='number'?x-y:String(x).localeCompare(String(y)));});
    byId('alert-rows').innerHTML=alertTable(list,latest);
    for(const button of main.querySelectorAll('[data-sort]')) {
      if(button.dataset.sort===sort) button.parentElement.setAttribute('aria-sort',direction<0?'descending':'ascending');
      else button.parentElement.removeAttribute('aria-sort');
    }
  }
  for(const input of main.querySelectorAll('.panel:first-of-type :is(input,select)')) input.addEventListener('input',render);
  for(const button of main.querySelectorAll('[data-sort]')) button.addEventListener('click',()=>{direction=sort===button.dataset.sort ? -direction : -1;sort=button.dataset.sort;render();});
  render();
  byId('run').addEventListener('submit',async event=>{
    event.preventDefault();
    const button=event.currentTarget.querySelector('button');
    button.disabled=true;
    byId('run-status').textContent='Construyendo el grafo y ejecutando el detector…';
    byId('experiment').replaceChildren();
    try {
      const result=await api('/platform/analyze?k='+encodeURIComponent(byId('k').value),{method:'POST'});
      byId('run-status').textContent=`k=${result.k} · ${result.applications} solicitudes · ${result.hubs} atributos hub · ${result.clusters.length} alertas · ${fmt(result.elapsed_seconds)} s`;
      byId('experiment').innerHTML=`<div class="scroll"><table><thead><tr><th>Caso</th><th>Tipología</th><th>Score</th><th>Solicitudes</th><th>Exposición</th><th>Evidencias</th><th>Estado</th></tr></thead><tbody>${alertTable(result.clusters,latest,result.k)}</tbody></table></div>`;
    } catch(error) {byId('run-status').textContent=error.message;} finally {button.disabled=false;}
  });
}
function graphView(graph,dossier) {
  const canvas=byId('network');
  const container=canvas.parentElement;
  const ctx=canvas.getContext('2d');
  const nodes=new Map(graph.nodes.map(node=>[node.node_id,node]));
  const isHub=node=>String(node.high_multiplicity).toLowerCase()==='true';
  const dates=new Map((dossier.members??[]).map(member=>[member.application_id,member.created_at]));
  const positions=new Map();
  const palette={application:'#23825f',person:'#477fc4',business:'#885abd',attribute:'#ae7330'};
  const describe=node=>`${types[node.attribute_type||node.node_type]??node.node_type} · ${node.node_id}`;
  const inspect=id=>{
    const node=nodes.get(id);
    byId('node-detail').textContent=node ? describe(node)+(isHub(node)?' · Hub':'')+(node.multiplicity?' · Multiplicidad '+node.multiplicity:'')+(node.created_at?' · '+node.created_at:'') : 'Selecciona un nodo para ver su identificador tokenizado.';
  };
  const date=byId('until');
  const hub=byId('hubs');
  function draw() {
    if (!ctx) return;
    const active=new Set([...nodes.values()].filter(node=>node.node_type==='application'&&(!date.value||!(dates.get(node.node_id)||node.created_at)||(dates.get(node.node_id)||node.created_at).slice(0,10)<=date.value)).map(node=>node.node_id));
    const parties=new Set(graph.edges.filter(edge=>edge.weight==null&&active.has(edge.source)).map(edge=>edge.target));
    const connected=new Set([...active,...parties]);
    const edges=graph.edges.filter(edge=>connected.has(edge.source)&&nodes.has(edge.target)&&(hub.checked||!isHub(nodes.get(edge.target))));
    const visible=[...new Set([...connected,...edges.map(edge=>edge.target)])].map(id=>nodes.get(id)).filter(Boolean);
    const groups=[visible.filter(node=>node.node_type==='application'),visible.filter(node=>['person','business'].includes(node.node_type)),visible.filter(node=>node.node_type==='attribute')];
    const width=Math.max(240,container.clientWidth), height=Math.max(390,Math.max(...groups.map(group=>group.length))*19+28);
    const scale=Math.min(devicePixelRatio||1,2);
    canvas.style.height=height+'px';
    canvas.width=width*scale; canvas.height=height*scale; ctx.scale(scale,scale);
    positions.clear();
    const style=getComputedStyle(canvas);
    ctx.font='11px system-ui';
    groups.forEach((group,col)=>group.forEach((node,index)=>positions.set(node.node_id,{
      x:width*[.15,.47,.77][col],y:(height-40)*(index+1)/(group.length+1)+18,node
    })));
    for(const edge of edges){
      const a=positions.get(edge.source),b=positions.get(edge.target);
      if(!a||!b)continue;
      ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);
      ctx.lineWidth=edge.weight==null?1:Math.max(1,Math.min(5,Number(edge.weight)/1.6));
      ctx.strokeStyle=style.getPropertyValue('--muted');ctx.globalAlpha=.38;ctx.stroke();
    }
    ctx.globalAlpha=1;
    for(const {x,y,node} of positions.values()){
      ctx.fillStyle=palette[node.node_type]??palette.attribute;
      ctx.beginPath();ctx.arc(x,y,isHub(node)?7:5,0,Math.PI*2);ctx.fill();
      ctx.fillStyle=style.getPropertyValue('--ink');
      ctx.fillText((types[node.attribute_type||node.node_type]??node.node_type)+' '+node.node_id.slice(-4),x+8,y+4,width*.21);
    }
    const selector=byId('node');
    const selected=selector.value;
    selector.replaceChildren(new Option('Selecciona un nodo',''),...visible.map(node=>new Option(describe(node),node.node_id)));
    if(positions.has(selected))selector.value=selected;
    inspect(selector.value);
    byId('node-count').textContent=`${visible.length} nodos · ${edges.length} enlaces`;
  }
  canvas.addEventListener('click',event=>{
    const hit=[...positions.values()].find(({x,y})=>Math.abs(x-event.offsetX)<18 && Math.abs(y-event.offsetY)<9);
    if(hit){byId('node').value=hit.node.node_id;inspect(hit.node.node_id);}
  });
  byId('node').addEventListener('change',event=>inspect(event.target.value));
  hub.addEventListener('change',draw);
  date.addEventListener('change',draw);
  new ResizeObserver(draw).observe(canvas);
  redrawGraph=draw;draw();
}
function casePage(data,audit) {
  const {cluster,dossier,graph,components}=data;
  const id=cluster.cluster_id;
  const exp=dossier.members?.map(row=>Number(row.amount_pen)).filter(n=>Number.isFinite(n)&&n>0)??[];
  const reasons=dossier.reasons??JSON.parse(cluster.reasons);
  const current=data.experimental ? null : latestDecisions(audit.events).get(id);
  main.innerHTML=heading('Expediente sintético',esc(id),esc(dossier.summary??reasons[0]??'Caso priorizado'))+
    `<p><a href="/app/alertas">← Volver a alertas</a> · <button class="button" id="pdf">Imprimir / guardar PDF</button></p>
    <div class="case-grid"><section class="panel"><h2>Diagnóstico</h2><p class="kpi"><strong>${fmt(cluster.risk_score)} / 100</strong>${type(cluster)}</p>
    <p><strong>${exp.length?pen(exp.reduce((a,b)=>a+b,0)):'—'}</strong> · monto solicitado</p>
    <ul>${Object.entries(components).map(([label,value])=>`<li>${label} · ${fmt(value)} pts</li>`).join('')}</ul>
    <h3>Pregunta de revisión</h3><p>¿Hay una actividad comercial u operativa que explique las coincidencias y qué señal independiente respalda la alerta?</p>
    <p class="muted small">Estado · <strong id="case-state">${states[current?.decision??'pendiente']}</strong></p></section>
    <section class="panel graph-panel"><h2>Subgrafo del caso</h2><p class="muted small">Relaciones del grafo guardado. El grosor indica el peso IDF cuando corresponde.</p>
    <div class="filters graph-options"><label><span>Mostrar hubs <input id="hubs" type="checkbox"></span></label><label>Solicitudes hasta<input id="until" type="date" value="${esc(dossier.time_window?.max?.slice(0,10)??'')}"></label><label>Nodo<select id="node"></select></label></div>
    <p class="muted small" id="node-count"></p><div><canvas id="network" aria-label="Subgrafo de solicitudes y atributos. Usa el selector para inspeccionar cada nodo." role="img"></canvas></div><p class="node-detail" id="node-detail" role="status"></p></section>
    <section class="panel"><h2>Evidencia</h2><p>Ventana observada · ${fmt(dossier.time_window?.span_hours??cluster.time_span_hours)} h</p>
    <ul>${reasons.map(value=>`<li>${esc(value)}</li>`).join('')}</ul>
    <ul>${(dossier.shared_attributes??[]).map(item=>`<li>${esc(types[item.type]??item.type)} · <code>${esc(item.value_hash)}</code> · peso ${fmt(item.weight)}</li>`).join('')}</ul>
    <p class="muted small">La combinación de señales elevó el score. El motor excluye los atributos hub de las conexiones directas entre solicitudes; el analista debe verificar el contexto comercial.</p>
    <h3>Decisión del analista</h3>${data.experimental ? '<p class="muted small">Expediente experimental. La bitácora registra decisiones de los casos de referencia.</p>' : audit.writable?`<form class="form" id="decision"><label>Analista<input name="reviewer" required maxlength="80"></label><label for="decision-result">Resultado</label><select id="decision-result" name="decision" required><option value="">Selecciona</option>${['confirmado','falso_positivo','en_seguimiento','escalado'].map(key=>`<option value="${key}">${states[key]}</option>`).join('')}</select><label>Observaciones<textarea name="notes" required maxlength="2000" rows="3"></textarea></label><button class="primary">Guardar en bitácora</button><p id="decision-status" role="status"></p></form>`:'<p class="muted small">La bitácora del despliegue requiere almacenamiento persistente.</p>'}</section></div>`;
  byId('pdf').addEventListener('click',()=>window.print());
  graphView(graph,dossier);
  byId('decision')?.addEventListener('submit',async event=>{
    event.preventDefault();const form=event.currentTarget;const button=form.querySelector('button');button.disabled=true;
    const body={...Object.fromEntries(new FormData(form)),cluster_id:id};
    try {
      const saved=await api('/platform/audit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      byId('case-state').textContent=states[saved.decision];
      byId('decision-status').textContent='Guardado · '+new Date(saved.reviewed_at).toLocaleString('es-PE');form.reset();
    } catch(error){byId('decision-status').textContent=error.message;} finally {button.disabled=false;}
  });
}
function auditPage(audit) {
  const events=[...audit.events].reverse();
  const discarded=events.filter(row=>['descartado','falso_positivo'].includes(row.decision)).length;
  main.innerHTML=heading('Revisión humana','Bitácora de decisiones','Historial de resultados del analista. La última decisión de cada caso actualiza su estado en el panel y en la bandeja.')+
  `<section class="panel"><p>${fmt(events.length)} decisiones · ${fmt(discarded)} descartes o falsos positivos</p>${audit.writable?'':'<p class="muted">Escritura pendiente de almacenamiento persistente en este despliegue.</p>'}
  <div class="scroll"><table><thead><tr><th>Caso</th><th>Analista</th><th>Fecha y hora</th><th>Resultado</th><th>Motivo</th></tr></thead><tbody>
  ${events.map(row=>`<tr><td><a href="${link(row)}">${esc(row.cluster_id)}</a></td><td>${esc(row.reviewer)}</td><td>${esc(new Date(row.reviewed_at).toLocaleString('es-PE'))}</td><td>${esc(states[row.decision]??row.decision)}</td><td>${esc(row.notes)}</td></tr>`).join('')||'<tr><td colspan="5">Aún no hay decisiones.</td></tr>'}</tbody></table></div></section>`;
}
function benchmark(results) {
  main.innerHTML=heading('Evaluación reproducible','Benchmark de detección','Carteras sintéticas con semilla 42. La calibración institucional requiere datos reales y validación de Caja Trujillo.')+
    `<section class="panel"><label>Escenario<select id="scenario"><option value="easy">Fácil</option><option value="medium">Medio</option><option value="hard">Difícil</option><option value="low">Baja prevalencia de anillos (~0,1 %)</option></select></label>
    <p class="muted" id="scenario-summary"></p><div id="benchmark-table"></div></section>
    <section class="panel"><h2>Curva precisión–recall</h2><p class="muted">Eje horizontal: recall. Eje vertical: precisión. Verde: RedRiesgo. Azul: regla base de dos valores.</p><canvas id="pr-curve" role="img" aria-label="Curvas de precisión y recall de los dos modelos"></canvas></section>
    <section class="panel"><h2>Ablación en la muestra pública</h2><p class="muted">346 solicitudes. Se cambia un componente cada vez y se conserva el umbral 60.</p>
    <div class="scroll"><table><thead><tr><th>Variante</th><th>Precisión</th><th>Recall</th><th>Falsos positivos</th></tr></thead><tbody>${Object.entries(results.ablation).map(([name,value])=>`<tr><th scope="row">${esc(name)}</th><td>${pct(value.precision)}</td><td>${pct(value.recall)}</td><td>${fmt(value.fp)}</td></tr>`).join('')}</tbody></table></div></section>
    <section class="panel"><h2>Reproducir las cuatro pruebas</h2><p>Ejecuta el generador, el grafo y el detector con el comando del repositorio.</p><code>python -m eval.platform_benchmark</code> <button id="copy" type="button">Copiar comando</button><p id="copy-status" role="status"></p></section>`;
  function render() {
    const row=results[byId('scenario').value];
    byId('scenario-summary').textContent=`${fmt(row.n_applications)} solicitudes · ${fmt(row.n_rings)} anillos simulados · ${fmt(row.elapsed_seconds)} s de ejecución medida`;
    const canvas=byId('pr-curve'), ctx=canvas.getContext('2d');
    if(ctx && row.pr) {
      const width=canvas.clientWidth, height=360, ratio=Math.min(devicePixelRatio||1,2);
      canvas.width=width*ratio;canvas.height=height*ratio;canvas.style.height=height+'px';
      ctx.scale(ratio,ratio);
      const axes=getComputedStyle(canvas).getPropertyValue('--muted');
      for(let i=0;i<=4;i++){
        const x=40+(width-55)*i/4,y=height-30-(height-50)*i/4;
        ctx.strokeStyle=axes;ctx.globalAlpha=.2;
        ctx.beginPath();ctx.moveTo(x,20);ctx.lineTo(x,height-30);ctx.moveTo(40,y);ctx.lineTo(width-15,y);ctx.stroke();
        ctx.globalAlpha=1;ctx.fillStyle=axes;ctx.font='11px system-ui';
        ctx.fillText(i*25+'%',x-10,height-12);ctx.fillText(i*25+'%',3,y+4);
      }
      for(const [key,color] of [['baseline','#598ce3'],['redriesgo','#25aa71']]){
        ctx.beginPath();ctx.lineWidth=2;ctx.strokeStyle=color;
        row.pr[key].forEach(([recall,precision],index)=>{
          const x=40+(width-55)*recall,y=height-30-(height-50)*precision;
          if(index===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);
        });
        ctx.stroke();
      }
    }
    const props=[['precision','Precisión',pct],['recall','Recall',pct],['fpr','Tasa de falsos positivos',pct],['review_minutes','Tiempo de revisión estimado (min)',fmt],['tp','Verdaderos positivos',fmt],['fp','Falsos positivos',fmt],['tn','Verdaderos negativos',fmt],['fn','Falsos negativos',fmt]];
    byId('benchmark-table').innerHTML=`<div class="scroll"><table><thead><tr><th>Métrica</th><th>Modelo base</th><th>RedRiesgo</th></tr></thead><tbody>${props.map(([key,label,format])=>`<tr><th scope="row">${label}</th><td>${format(row.baseline[key])}</td><td>${format(row.redriesgo[key])}</td></tr>`).join('')}</tbody></table></div><p class="muted small">La regla base alerta si se comparte teléfono o dispositivo. RedRiesgo alerta con score ≥ 60. Estimación de revisión: 2 minutos por solicitud alertada.</p>`;
  }
  byId('scenario').addEventListener('change',render); window.addEventListener('resize',render); redrawGraph=render; render();
  byId('copy').addEventListener('click',async()=>{
    try{await navigator.clipboard.writeText('python -m eval.platform_benchmark');byId('copy-status').textContent='Comando copiado.';}
    catch{byId('copy-status').textContent='Selecciona el comando para copiarlo.';}
  });
}
function methodology() {
  main.innerHTML=heading('Metodología','Del dato a la investigación','Grafo heterogéneo, señales combinadas y evidencia trazable.')+
  `<div class="grid"><figure class="panel"><img src="/assets/arquitectura.jpg" alt="Arquitectura RedRiesgo"><figcaption>Arquitectura del prototipo</figcaption></figure><figure class="panel"><img src="/assets/patrones-grafos.jpg" alt="Diferencias entre hubs y redes de riesgo"><figcaption>Patrones de microfinanzas</figcaption></figure></div>
  <section class="panel"><h2>Pipeline</h2><ol><li>Normaliza y tokeniza identificadores.</li><li>Vincula entidades con atributos en un grafo bipartito.</li><li>Calcula IDF suavizado por atributo y aplica el tope de su tipo.</li><li>Si la multiplicidad supera k, conserva un hub y evita generar conexiones directas entre todos sus miembros.</li><li>Combina comunidades, ciclos de referencias, ráfagas y señales geográficas.</li><li>Asigna un score y genera el expediente para revisión humana.</li></ol></section>
  <section class="panel"><h2>Cómo se calcula el score</h2><p><code>IDF = min(tope del tipo, ln((N + 1)/(df + 1)))</code></p><p>Para 100 entidades y 4 apariciones, un teléfono tiene peso ln(101/5) ≈ 3,01. Con 50 apariciones su peso cae a 0,68 y, con k = 25, se representa como hub.</p><p><code>Score = estructura (24·tamaño + 19·densidad + 14·evidencia) + tiempo (14·ráfaga + 9·ventana) + 9·multisolicitud + 6·distancia + 5·peso + 1·referencias + ajustes</code></p><p>Las señales se normalizan. Los ciclos de referencia aplican un mínimo de 75; el tamaño y el rango final limitan la puntuación. Los valores de cada caso aparecen en su expediente.</p></section>`;
}
function privacy() {
  main.innerHTML=heading('Uso responsable','Privacidad y límites','La herramienta prioriza investigaciones. La entidad conserva la decisión crediticia.')+
  `<div class="grid"><section class="panel"><h2>Qué muestra</h2><p>Identificadores tokenizados, hashes de atributos, fechas y montos de la cartera sintética. El expediente de la muestra enmascara los datos de contacto.</p></section><section class="panel"><h2>Cómo se revisa una alerta</h2><p>El analista compara las señales con explicaciones legítimas, documenta su razonamiento y puede descartar falsos positivos. El score expresa prioridad de análisis y requiere corroboración humana.</p></section><section class="panel"><h2>Alcance de la demo</h2><p>Los datos son sintéticos. Integración al core, SSO y calibración con datos reales quedan fuera del alcance de esta versión.</p></section></div>`;
}
async function start(){
  if(route==='/metodologia'){methodology();return;}
  if(route==='/privacidad'){privacy();return;}
  if(route==='/validacion'){benchmark(await api('/platform/benchmark'));return;}
  const audit=await api('/platform/audit');
  if(route==='/app/bitacora'){auditPage(audit);return;}
  if(route.startsWith('/app/caso/')){casePage(await api('/platform/cases/'+route.split('/').at(-1)+location.search),audit);return;}
  const data=await api('/platform/alerts');
  if(route==='/app/alertas')alerts(data.alerts,latestDecisions(audit.events));
  else panel(data.alerts,latestDecisions(audit.events));
}
start().catch(error=>{
  main.innerHTML='<h1>No se pudo cargar la vista</h1><p role="alert">'+esc(error.message)+'</p><a class="button" href="/app/alertas">Abrir alertas</a>';
}).finally(()=>main.removeAttribute('aria-busy'));
</script>
</body>
</html>
"""
