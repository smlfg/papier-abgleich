(() => {
  "use strict";

  const data = JSON.parse(document.getElementById("flow").textContent);
  const meta = JSON.parse(document.getElementById("meta").textContent);
  const grillRows = JSON.parse(document.getElementById("grill-table").textContent);
  const pointLabel = meta.point_label || "Skizzen-Punkt";
  const markerNames = { BELEGT: "belegt", GERAET: "am Gerät", OFFLINE: "offline", HYPOTHESE: "Hypothese" };
  data.nodes.forEach((node) => ["zahlen", "regeln", "offen", "verlauf", "snippets", "commits", "docs", "next", "belege"].forEach((key) => { if (!Array.isArray(node[key])) node[key] = []; }));
  data.offen = data.offen || []; data.commits = data.commits || []; data.sessions = data.sessions || {}; data.regeln = data.regeln || {};
  const byId = new Map(data.nodes.map((node) => [node.id, node]));
  const openById = new Map(data.offen.map((item) => [item.id, item]));
  const stageIndex = new Map(data.stages.map((stage, index) => [stage.id, index]));
  const statusNames = {
    "stimmt-noch": "stimmt noch",
    "geaendert": "geändert",
    "anders": "anders",
    "teilweise": "teilweise",
    "unklar": "unklar"
  };
  const statusColors = {
    "stimmt-noch": "var(--ok)",
    "geaendert": "var(--changed)",
    "anders": "var(--different)",
    "teilweise": "var(--partial)",
    "unklar": "var(--unclear)"
  };
  const statusOrder = ["stimmt-noch", "geaendert", "anders", "teilweise", "unklar"];
  const tabNames = { fakt: "Fakt", code: "Code", verlauf: "Verlauf" };
  const query = new URLSearchParams(location.search);
  const requestedStatus = query.get("status");
  const requestedQuery = query.get("q") || "";
  const requestedOriginal = query.get("original") === "1";
  const requestedTheme = query.get("theme");
  let activeNodeId = null;
  let activeTab = "fakt";
  let selectedStatus = statusOrder.includes(requestedStatus) ? requestedStatus : null;
  let searchTerm = requestedQuery.toLocaleLowerCase("de");

  const grid = document.getElementById("flow-grid");
  const svg = document.getElementById("arrows");
  const panel = document.getElementById("panel");
  const panelBody = document.getElementById("panel-body");
  const flowFrame = document.querySelector(".flow-frame");
  const searchInput = document.getElementById("search");
  const overlay = document.getElementById("original-overlay");
  const originalOpen = document.getElementById("open-original");
  const originalClose = document.getElementById("original-close");
  const themeToggle = document.getElementById("theme-toggle");

  const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  })[character]);

  const commitUrl = (short) => {
    const commit = data.commits.find((item) => item.short === short);
    return commit && commit.url ? commit.url : null;
  };

  function setTheme(theme, persist = true) {
    const next = theme === "dark" ? "dark" : "light";
    document.documentElement.dataset.theme = next;
    themeToggle.setAttribute("aria-pressed", String(next === "dark"));
    themeToggle.setAttribute("aria-label", next === "dark" ? "Hellmodus umschalten" : "Dunkelmodus umschalten");
    if (persist) localStorage.setItem(meta.theme_key || "papier-abgleich-theme", next);
    requestAnimationFrame(drawArrows);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => requestAnimationFrame(drawArrows));
    setTimeout(drawArrows, 300);
  }

  function statusBadge(status) {
    return `<span class="badge" style="--status-color:${statusColors[status] || "var(--accent)"}">${escapeHtml(statusNames[status] || status)}</span>`;
  }

  function renderMetrics() {
    const stats = data.stats;
    const metrics = document.querySelector(".metrics");
    const values = [stats.sessions, `${stats.commits_auf_github} + ${stats.commits_lokal}`, stats.offene_punkte, stats.skizzen_punkte ?? stats.grillme_punkte];
    const labels = ["Sessions", "Commits", "offene Punkte", meta.points_label || "Skizzen-Punkte"];
    const subs = [stats.subagent ? `+${stats.subagent} Subagent` : "ausgewertet", "auf GitHub + lokal", "noch zu klären", "gegen den Code geprüft"];
    [...metrics.querySelectorAll(".metric:not(.metric-wide)")].forEach((card, index) => {
      card.querySelector(".metric-number").textContent = values[index];
      card.querySelector("span:not(.metric-number)").textContent = labels[index];
      card.querySelector("small").textContent = subs[index];
    });
    const bar = document.getElementById("status-bar");
    const legend = document.getElementById("status-legend");
    bar.innerHTML = "";
    legend.innerHTML = "";
    const total = Object.values(stats.status_count).reduce((sum, count) => sum + count, 0);
    statusOrder.forEach((status) => {
      const count = stats.status_count[status] || 0;
      const segment = document.createElement("span");
      segment.style.width = `${(count / total) * 100}%`;
      segment.style.background = statusColors[status];
      segment.title = `${statusNames[status]}: ${count}`;
      bar.appendChild(segment);
      const item = document.createElement("span");
      item.innerHTML = `<i style="background:${statusColors[status]}"></i>${escapeHtml(statusNames[status])} ${count}`;
      legend.appendChild(item);
    });
  }

  function renderFilters() {
    const container = document.getElementById("status-filters");
    container.innerHTML = "";
    statusOrder.forEach((status) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "filter-chip";
      button.dataset.status = status;
      button.style.setProperty("--chip-color", statusColors[status]);
      button.textContent = statusNames[status];
      button.setAttribute("aria-pressed", String(selectedStatus === status));
      button.addEventListener("click", () => {
        selectedStatus = selectedStatus === status ? null : status;
        container.querySelectorAll("button").forEach((item) => item.setAttribute("aria-pressed", String(item.dataset.status === selectedStatus)));
        updateFilters();
      });
      container.appendChild(button);
    });
  }

  function renderStageNav() {
    const nav = document.getElementById("stage-nav");
    nav.innerHTML = "";
    data.stages.forEach((stage, index) => {
      const count = data.nodes.filter((node) => node.stage === stage.id).length;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "stage-chip";
      button.dataset.stage = stage.id;
      button.innerHTML = `${index + 1}. ${escapeHtml(stage.name)} <span>${count}</span>`;
      button.addEventListener("click", () => {
        const band = document.getElementById(`lane-${stage.id}`);
        if (band) band.scrollIntoView({ behavior: "smooth", block: "start" });
      });
      nav.appendChild(button);
    });
  }

  function searchableText(node) {
    return [node.label, node.was, node.warum, node.fakt, ...node.snippets.map((snippet) => snippet.code)].join(" ").toLocaleLowerCase("de");
  }

  const laneLayout = (() => {
    const layout = new Map();
    let offset = 0;
    data.stages.forEach((stage, index) => {
      const nodes = data.nodes.filter((node) => node.stage === stage.id);
      if (!nodes.length) return;
      const minRow = Math.min(...nodes.map((node) => node.row));
      const rows = Math.max(...nodes.map((node) => node.row)) - minRow + 1;
      layout.set(stage.id, { index, minRow, rows, offset, count: nodes.length, name: stage.name });
      offset += rows;
    });
    return layout;
  })();

  function createLanes() {
    data.stages.forEach((stage) => {
      const lane = laneLayout.get(stage.id);
      if (!lane) return;
      const rowSpan = `${lane.offset + 1} / span ${lane.rows}`;
      const band = document.createElement("div");
      band.className = `lane-band ${lane.index % 2 ? "odd" : "even"}`;
      band.id = `lane-${stage.id}`;
      band.style.gridColumn = "1 / -1";
      band.style.gridRow = rowSpan;
      grid.appendChild(band);
      const head = document.createElement("div");
      head.className = "lane-head";
      head.style.gridColumn = "1";
      head.style.gridRow = rowSpan;
      head.innerHTML = `<span class="lane-num">${String(lane.index + 1).padStart(2, "0")}</span><span class="lane-name">${escapeHtml(stage.name)}</span><span class="lane-count">${lane.count} ${lane.count === 1 ? "Knoten" : "Knoten"}</span>`;
      grid.appendChild(head);
    });
  }

  function createNode(node) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "node";
    button.dataset.node = node.id;
    const lane = laneLayout.get(node.stage);
    button.style.gridColumn = String(node.col + 2);
    button.style.gridRow = String(lane.offset + node.row - lane.minRow + 1);
    button.style.setProperty("--status-color", statusColors[node.status]);
    button.setAttribute("aria-label", `${node.label}, ${pointLabel} ${node.punkt}, ${statusNames[node.status]}`);
    button.innerHTML = `
      <span class="node-status" aria-hidden="true"></span>
      <span class="node-label">${escapeHtml(node.label)}</span>
      <span class="node-was">${escapeHtml(node.was)}</span>
      <span class="node-point">Punkt ${escapeHtml(node.punkt)} · ${escapeHtml(statusNames[node.status])}</span>
    `;
    if (node.shape === "raute" || node.id === "raute") button.classList.add("node-diamond");
    if (node.shape === "notiz" || node.id === "user") button.classList.add("node-user");
    button.addEventListener("click", () => openNode(node.id, true));
    grid.appendChild(button);
  }

  function updateFilters() {
    data.nodes.forEach((node) => {
      const element = grid.querySelector(`[data-node="${CSS.escape(node.id)}"]`);
      const statusMatch = !selectedStatus || node.status === selectedStatus;
      const searchMatch = !searchTerm || searchableText(node).includes(searchTerm);
      element.classList.toggle("dimmed", !(statusMatch && searchMatch));
    });
    drawArrows();
  }

  function tokenizePython(code) {
    const keywords = new Set(["and", "as", "assert", "async", "await", "break", "class", "continue", "def", "del", "elif", "else", "except", "False", "finally", "for", "from", "global", "if", "import", "in", "is", "lambda", "None", "nonlocal", "not", "or", "pass", "raise", "return", "True", "try", "while", "with", "yield"]);
    const pattern = /(?<!\w)(@[\w.]+)|(def|class)\s+([A-Za-z_]\w*)|("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')|(#.*$)|\b(\d+(?:\.\d+)?)\b|\b([A-Za-z_]\w*)\b/gm;
    let output = "";
    let last = 0;
    for (const match of code.matchAll(pattern)) {
      output += escapeHtml(code.slice(last, match.index));
      const [whole, decorator, definition, defName, string, comment, number, word] = match;
      let css = "";
      if (decorator) css = "tok-decorator";
      else if (definition) css = "tok-keyword";
      else if (defName) css = "tok-name";
      else if (string) css = "tok-string";
      else if (comment) css = "tok-comment";
      else if (number) css = "tok-number";
      else if (keywords.has(word)) css = "tok-keyword";
      output += css ? `<span class="${css}">${escapeHtml(whole)}</span>` : escapeHtml(whole);
      last = match.index + whole.length;
    }
    output += escapeHtml(code.slice(last));
    return output;
  }

  function snippetMarkup(snippet) {
    const lines = snippet.code.split("\n");
    const code = lines.map((line, index) => `<span class="code-line"><span class="line-number">${Number(snippet.start) + index}</span><span class="line-code">${tokenizePython(line) || " "}</span></span>`).join("");
    const label = `${snippet.file}:${snippet.start}–${snippet.end}`;
    const link = snippet.url
      ? `<a class="snippet-link" href="${escapeHtml(snippet.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`
      : `<span class="snippet-link">${escapeHtml(label)}</span>`;
    return `<section class="snippet">${link}<pre class="code"><code>${code}</code></pre></section>`;
  }

  function ruleMarkup(code) {
    const text = data.regeln[code];
    if (!text) return "";
    const source = code.startsWith("R-") ? data.regeln_quelle["R-"] : data.regeln_quelle["R"];
    return `<article class="rule-item"><strong>${escapeHtml(code)}</strong><p>${escapeHtml(text)}</p><span class="rule-source">Quelle: ${escapeHtml(source)}</span></article>`;
  }

  function belegMarkup(beleg) {
    const marker = String(beleg.marker || "HYPOTHESE").toUpperCase();
    const source = beleg.url ? `<a href="${escapeHtml(beleg.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(beleg.quelle || beleg.url)}</a>` : escapeHtml(beleg.quelle || "");
    return `<figure class="beleg beleg-${marker.toLowerCase()}"><span class="marker">${escapeHtml(markerNames[marker] || marker)}</span><blockquote>${escapeHtml(beleg.quote || "")}</blockquote>${source ? `<figcaption>${source}</figcaption>` : ""}</figure>`;
  }

  function renderFakt(node) {
    const openLinks = node.offen.map((id) => {
      const item = openById.get(id);
      return item ? `<button class="open-link" type="button" data-open-id="${escapeHtml(id)}"><span>${escapeHtml(item.titel)}</span><span>${escapeHtml(item.quelle)}</span></button>` : "";
    }).join("");
    return `
      <section class="panel-section"><h3>Was</h3><p class="was">${escapeHtml(node.was)}</p></section>
      <section class="panel-section"><h3>Warum / Status</h3><p class="why">${escapeHtml(node.warum)}</p></section>
      ${node.belege.length ? `<section class="panel-section"><h3>Belege</h3>${node.belege.map(belegMarkup).join("")}</section>` : ""}
      ${node.zahlen.length ? `<section class="panel-section"><h3>Zahlen</h3><div class="chips">${node.zahlen.map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join("")}</div></section>` : ""}
      ${node.regeln.length ? `<section class="panel-section"><h3>Regeln</h3>${node.regeln.map(ruleMarkup).join("")}</section>` : ""}
      ${node.offen.length ? `<section class="panel-section"><h3>Offene Punkte</h3>${openLinks}</section>` : ""}
    `;
  }

  function renderCode(node) {
    return `<section class="panel-section"><h3>Codeausschnitte</h3>${node.snippets.map(snippetMarkup).join("") || "<p>Kein Snippet hinterlegt.</p>"}</section>`;
  }

  function historyEntry(entry) {
    const session = data.sessions[entry.ref];
    let meta = "";
    if (session) {
      meta = `<strong>${escapeHtml(entry.ref)}</strong> · ${escapeHtml(session.zeit)} · ${escapeHtml(session.titel)} <span class="hash">${escapeHtml(session.id)}</span>`;
    } else {
      const url = entry.url || commitUrl(entry.ref);
      meta = url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(entry.ref)}</a>` : escapeHtml(entry.ref);
    }
    const link = entry.url ? `<p><a href="${escapeHtml(entry.url)}" target="_blank" rel="noopener noreferrer">Link öffnen</a></p>` : "";
    return `<li><div class="timeline-meta">${meta}</div><p>${escapeHtml(entry.text)}</p>${link}</li>`;
  }

  function renderVerlauf(node) {
    const history = node.verlauf.length ? `<ul class="timeline">${node.verlauf.map(historyEntry).join("")}</ul>` : "<p>Keine Verlaufseinträge.</p>";
    const commits = node.commits.map((ref) => {
      const short = typeof ref === "string" ? ref : ref.short;
      const commit = data.commits.find((item) => item.short === short) || (typeof ref === "object" ? ref : { short });
      const head = commit.url ? `<a class="pill-link" href="${escapeHtml(commit.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(commit.short)}</a>` : `<span class="pill-link local">${escapeHtml(commit.short)} · nur lokal, nicht auf GitHub</span>`;
      return `<li><div class="timeline-meta">${head}</div><p>${escapeHtml(commit.msg || "")}</p>${commit.wo ? `<p class="muted">${escapeHtml(commit.wo)}</p>` : ""}</li>`;
    }).join("");
    const docs = node.docs.length ? node.docs.map((doc) => `<li><div class="timeline-meta">Dokument</div><p><a href="${escapeHtml(doc.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(doc.name)}</a></p></li>`).join("") : "";
    return `
      <section class="panel-section"><h3>Verlauf</h3>${history}</section>
      ${node.commits.length ? `<section class="panel-section"><h3>Commits</h3><ul class="timeline">${commits}</ul></section>` : ""}
      ${node.docs.length ? `<section class="panel-section"><h3>Dokumente</h3><ul class="timeline">${docs}</ul></section>` : ""}
    `;
  }

  function renderPanel(node) {
    panelBody.innerHTML = activeTab === "fakt" ? renderFakt(node) : activeTab === "code" ? renderCode(node) : renderVerlauf(node);
    panelBody.querySelectorAll("[data-open-id]").forEach((button) => {
      button.addEventListener("click", () => {
        const item = openById.get(button.dataset.openId);
        if (item) document.getElementById("offen").scrollIntoView({ behavior: "smooth" });
      });
    });
  }

  function openNode(id, updateHash = false, tab = null) {
    const node = byId.get(id);
    if (!node) return;
    activeNodeId = id;
    if (tab) activeTab = tab;
    grid.querySelectorAll(".node.active").forEach((item) => item.classList.remove("active"));
    const active = grid.querySelector(`[data-node="${CSS.escape(id)}"]`);
    if (active) active.classList.add("active");
    const stage = data.stages.find((item) => item.id === node.stage);
    document.getElementById("panel-eyebrow").textContent = `Stufe ${stageIndex.get(node.stage) + 1} · ${stage.name}`;
    document.getElementById("panel-title").textContent = node.label;
    document.getElementById("panel-meta").innerHTML = `<span>${escapeHtml(pointLabel)} ${escapeHtml(node.punkt)}</span>${statusBadge(node.status)}`;
    document.querySelectorAll(".tabs button").forEach((button) => button.setAttribute("aria-selected", String(button.dataset.tab === activeTab)));
    renderPanel(node);
    panel.classList.add("open");
    panel.setAttribute("aria-hidden", "false");
    flowFrame.classList.add("panel-active");
    if (updateHash) history.replaceState(null, "", `#${encodeURIComponent(id)}${activeTab === "fakt" ? "" : `/${activeTab}`}`);
    requestAnimationFrame(drawArrows);
  }

  function closePanel(updateHash = true) {
    panel.classList.remove("open");
    panel.setAttribute("aria-hidden", "true");
    flowFrame.classList.remove("panel-active");
    grid.querySelectorAll(".node.active").forEach((item) => item.classList.remove("active"));
    activeNodeId = null;
    if (updateHash && location.hash) history.replaceState(null, "", location.pathname + location.search);
    requestAnimationFrame(drawArrows);
  }

  function setTab(tab) {
    activeTab = tab;
    document.querySelectorAll(".tabs button").forEach((button) => button.setAttribute("aria-selected", String(button.dataset.tab === tab)));
    if (activeNodeId) {
      renderPanel(byId.get(activeNodeId));
      history.replaceState(null, "", `#${encodeURIComponent(activeNodeId)}${tab === "fakt" ? "" : `/${tab}`}`);
    }
  }

  function orthogonalPath(from, to) {
    const base = grid.getBoundingClientRect();
    const a = from.getBoundingClientRect();
    const b = to.getBoundingClientRect();
    const A = { l: a.left - base.left, r: a.right - base.left, t: a.top - base.top, b: a.bottom - base.top };
    const B = { l: b.left - base.left, r: b.right - base.left, t: b.top - base.top, b: b.bottom - base.top };
    const radius = 8;
    let points;
    const sameRow = Math.abs((A.t + A.b) / 2 - (B.t + B.b) / 2) < 6;
    if (sameRow) {
      const y = (A.t + A.b) / 2;
      points = B.l >= A.r ? [{ x: A.r, y }, { x: B.l - 2, y }] : [{ x: A.l, y }, { x: B.r + 2, y }];
    } else {
      const sx = (A.l + A.r) / 2;
      const ex = (B.l + B.r) / 2;
      const midY = (A.b + B.t) / 2;
      points = Math.abs(sx - ex) < 2
        ? [{ x: sx, y: A.b }, { x: ex, y: B.t - 2 }]
        : [{ x: sx, y: A.b }, { x: sx, y: midY }, { x: ex, y: midY }, { x: ex, y: B.t - 2 }];
    }
    let d = `M ${points[0].x} ${points[0].y}`;
    for (let index = 1; index < points.length - 1; index += 1) {
      const previous = points[index - 1];
      const current = points[index];
      const next = points[index + 1];
      const incoming = Math.hypot(current.x - previous.x, current.y - previous.y);
      const outgoing = Math.hypot(next.x - current.x, next.y - current.y);
      const r = Math.min(radius, incoming / 2, outgoing / 2);
      const before = { x: current.x + (previous.x - current.x) * (r / incoming), y: current.y + (previous.y - current.y) * (r / incoming) };
      const after = { x: current.x + (next.x - current.x) * (r / outgoing), y: current.y + (next.y - current.y) * (r / outgoing) };
      d += ` L ${before.x} ${before.y} Q ${current.x} ${current.y} ${after.x} ${after.y}`;
    }
    const last = points[points.length - 1];
    d += ` L ${last.x} ${last.y}`;
    return { d, end: last, mid: points[Math.floor(points.length / 2)] };
  }

  function drawArrows() {
    const base = grid.getBoundingClientRect();
    if (!base.width || !base.height) return;
    svg.setAttribute("width", String(base.width));
    svg.setAttribute("height", String(base.height));
    svg.setAttribute("viewBox", `0 0 ${base.width} ${base.height}`);
    svg.innerHTML = "";
    const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    defs.innerHTML = `<marker id="arrowhead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/></marker>`;
    svg.appendChild(defs);
    data.nodes.forEach((node) => {
      node.next.forEach((targetId, edgeIndex) => {
        const from = grid.querySelector(`[data-node="${CSS.escape(node.id)}"]`);
        const to = grid.querySelector(`[data-node="${CSS.escape(targetId)}"]`);
        if (!from || !to) return;
        const geometry = orthogonalPath(from, to);
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", geometry.d);
        path.setAttribute("class", "arrow");
        path.setAttribute("marker-end", "url(#arrowhead)");
        path.dataset.from = node.id;
        path.dataset.to = targetId;
        if (activeNodeId === node.id || activeNodeId === targetId) path.classList.add("active");
        if (from.classList.contains("dimmed") && to.classList.contains("dimmed")) path.classList.add("dimmed");
        svg.appendChild(path);
        const edgeLabel = (node.edge_labels || {})[targetId] ?? ((node.shape === "raute" || node.id === "raute") ? (edgeIndex === 0 ? "yes" : "no") : null);
        if (edgeLabel) {
          const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
          text.setAttribute("x", String(geometry.end.x + 16));
          text.setAttribute("y", String(geometry.end.y - 10));
          text.setAttribute("class", "edge-label");
          text.setAttribute("text-anchor", "middle");
          text.textContent = edgeLabel;
          svg.appendChild(text);
        }
      });
    });
  }

  function renderOpenPoints() {
    const container = document.getElementById("open-grid");
    container.innerHTML = "";
    document.getElementById("open-count").textContent = `${data.offen.length} Punkte`;
    data.offen.forEach((item) => {
      const affected = data.nodes.filter((node) => node.offen.includes(item.id));
      const card = document.createElement("article");
      card.className = "open-card";
      card.id = `offen-${item.id}`;
      const snippet = item.snippet ? `<pre class="open-snippet">${escapeHtml(item.snippet.code)}</pre>${item.snippet.url ? `<a href="${escapeHtml(item.snippet.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.snippet.file)}:${item.snippet.start}–${item.snippet.end}</a>` : ""}` : "";
      card.innerHTML = `
        <span class="open-source">Quelle: ${escapeHtml(item.quelle)}</span>
        <h3>${escapeHtml(item.titel)}</h3>
        <p>${escapeHtml(item.text)}</p>
        ${snippet}
        <div class="node-links">${affected.map((node) => `<button type="button" data-open-node="${escapeHtml(node.id)}">${escapeHtml(node.label)}</button>`).join("") || "<span class='chip'>kein Knoten zugeordnet</span>"}</div>
      `;
      card.querySelectorAll("[data-open-node]").forEach((button) => button.addEventListener("click", () => openNode(button.dataset.openNode, true)));
      container.appendChild(card);
    });
  }

  function renderArchive() {
    const commitsBody = document.getElementById("commits-body");
    commitsBody.innerHTML = data.commits.map((commit) => `<tr><td>${commit.url ? `<a href="${escapeHtml(commit.url)}" target="_blank" rel="noopener noreferrer"><code>${escapeHtml(commit.short)}</code></a>` : `<code>${escapeHtml(commit.short)}</code>`}</td><td>${escapeHtml(commit.msg)}</td><td>${escapeHtml(commit.wo)}</td></tr>`).join("");
    const sessionsBody = document.getElementById("sessions-body");
    sessionsBody.innerHTML = Object.entries(data.sessions).map(([key, session]) => `<tr><td>${escapeHtml(key)} · ${escapeHtml(session.id)}</td><td>${escapeHtml(session.zeit)}</td><td>${escapeHtml(session.titel)}</td></tr>`).join("");
    document.getElementById("rules-count").textContent = `${Object.keys(data.regeln).length} Regeln`;
    document.getElementById("rules-body").innerHTML = Object.entries(data.regeln).map(([code, text]) => `<article><code>${escapeHtml(code)}</code><p>${escapeHtml(text)}</p></article>`).join("");
    document.getElementById("grill-body").innerHTML = grillRows.map((row) => `<tr><td>${escapeHtml(row[0])}</td><td>${escapeHtml(row[1])}</td><td>${escapeHtml(row[2])}</td><td>${escapeHtml(row[3])}</td></tr>`).join("");
  }

  function openOriginal() {
    overlay.classList.add("open");
    overlay.setAttribute("aria-hidden", "false");
    originalClose.focus();
  }

  function closeOriginal() {
    overlay.classList.remove("open");
    overlay.setAttribute("aria-hidden", "true");
    originalOpen.focus();
  }

  function readHash() {
    const raw = location.hash.replace(/^#/, "");
    const parts = raw.split("/");
    const id = decodeURIComponent(parts[0] || "");
    const tab = parts[1] && tabNames[parts[1]] ? parts[1] : "fakt";
    if (byId.has(id)) {
      openNode(id, false, tab);
      requestAnimationFrame(() => {
        const el = grid.querySelector(`[data-node="${CSS.escape(id)}"]`);
        if (el) el.scrollIntoView({ block: "center" });
      });
    }
  }

  function navigateNode(direction) {
    const index = data.nodes.findIndex((node) => node.id === activeNodeId);
    if (index < 0) {
      openNode(data.nodes[0].id, true);
      return;
    }
    const nextIndex = Math.min(data.nodes.length - 1, Math.max(0, index + direction));
    openNode(data.nodes[nextIndex].id, true);
    const el = grid.querySelector(`[data-node="${CSS.escape(data.nodes[nextIndex].id)}"]`);
    if (el) el.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  function renderVerdict() {
    const list = (statuses) => data.nodes.filter((node) => statuses.includes(node.status))
      .map((node) => `<li><button type="button" class="link-btn" data-goto="${escapeHtml(node.id)}">${escapeHtml(node.label)}</button> <span class="pill pill-${node.status}">${escapeHtml(statusNames[node.status])}</span></li>`).join("");
    const c = data.stats.status_count;
    document.getElementById("verdict-ok").innerHTML = `<h3>Was die Skizze noch trifft</h3><p class="muted">${c["stimmt-noch"]} von ${data.nodes.length} Knoten stimmen mit dem Code auf ${escapeHtml(meta.code_ref || "dem Code-Stand")} überein, ${c["teilweise"]} teilweise.</p><ul class="verdict-list">${list(["stimmt-noch", "teilweise"])}</ul>`;
    document.getElementById("verdict-diff").innerHTML = `<h3>Wo der Code inzwischen anders ist</h3><p class="muted">${c["geaendert"]} geändert, ${c["anders"]} anders gelöst, ${c["unklar"]} unklar.</p><ul class="verdict-list">${list(["geaendert", "anders", "unklar"])}</ul>`;
    const drift = openById.get(meta.callout_offen_id || "");
    if (drift) document.getElementById("callout").innerHTML = `<strong>${escapeHtml(drift.titel)}.</strong> ${escapeHtml(drift.text)} <span class="muted">(Quelle: ${escapeHtml(drift.quelle)})</span>`;
    document.querySelectorAll("[data-goto]").forEach((button) => button.addEventListener("click", () => {
      openNode(button.dataset.goto, true);
      document.getElementById("flow-grid").scrollIntoView({ behavior: "smooth", block: "start" });
    }));
  }

  function init() {
    renderVerdict();
    renderMetrics();
    renderFilters();
    renderStageNav();
    createLanes();
    data.nodes.forEach(createNode);
    renderOpenPoints();
    renderArchive();
    searchInput.value = requestedQuery;
    searchInput.addEventListener("input", () => {
      searchTerm = searchInput.value.trim().toLocaleLowerCase("de");
      updateFilters();
    });
    document.querySelectorAll(".tabs button").forEach((button) => {
      button.dataset.tab = button.id.replace("tab-", "");
      button.addEventListener("click", () => setTab(button.dataset.tab));
    });
    document.getElementById("close-panel").addEventListener("click", () => closePanel());
    document.getElementById("prev-node").addEventListener("click", () => navigateNode(-1));
    document.getElementById("next-node").addEventListener("click", () => navigateNode(1));
    originalOpen.addEventListener("click", openOriginal);
    originalClose.addEventListener("click", closeOriginal);
    themeToggle.addEventListener("click", () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
    document.addEventListener("keydown", (event) => {
      const target = event.target;
      const editing = target && (target.matches("input, textarea") || target.isContentEditable);
      if (event.key === "Escape") {
        if (overlay.classList.contains("open")) closeOriginal();
        else if (panel.classList.contains("open")) closePanel();
        return;
      }
      if (editing) return;
      if (event.key === "/") {
        event.preventDefault();
        searchInput.focus();
      } else if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) {
        event.preventDefault();
        navigateNode(["ArrowLeft", "ArrowUp"].includes(event.key) ? -1 : 1);
      } else if (["1", "2", "3"].includes(event.key)) {
        setTab(["fakt", "code", "verlauf"][Number(event.key) - 1]);
      }
    });
    window.addEventListener("hashchange", readHash);
    window.addEventListener("resize", drawArrows);
    if ("ResizeObserver" in window) new ResizeObserver(drawArrows).observe(grid);
    const savedTheme = localStorage.getItem(meta.theme_key || "papier-abgleich-theme");
    setTheme(requestedTheme === "dark" ? "dark" : requestedTheme === "light" ? "light" : savedTheme === "dark" ? "dark" : "light", false);
    updateFilters();
    readHash();
    if (requestedOriginal) openOriginal();
    requestAnimationFrame(drawArrows);
  }

  init();
})();
