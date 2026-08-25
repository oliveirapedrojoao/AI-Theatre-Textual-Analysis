/* Gráfico de barras horizontais e escala de eixo. */

/* ------------------------------------------------------- barras horizontais
   Marca: ≤24px de espessura, extremidade arredondada a 4px do lado do valor,
   assente numa única linha de base; rótulo do valor na ponta.              */
function barras(svgSel, dados, opts){
  opts = opts || {};
  const svg = $(svgSel);
  svg.textContent = "";
  if (!dados.length){
    svg.setAttribute("viewBox", "0 0 600 60");
    const t = el("text", {x:12, y:34, class:"lbl-mark"});
    t.textContent = "Sem dados para os filtros activos.";
    svg.appendChild(t); return;
  }
  const W = 600, ML = opts.margemEsq || 150, MR = 54, MT = 8, MB = 26;
  const passo = 30, esp = Math.min(24, passo - 10);
  const H = MT + dados.length * passo + MB;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.style.maxHeight = (H * 1.25) + "px";
  const max = Math.max.apply(null, dados.map(d => d.valor)) || 1;
  const x = v => ML + (v / max) * (W - ML - MR);

  // grelha: hairline sólida, recessiva
  const ticks = escalaBonita(max, 4);
  ticks.forEach(t => {
    svg.appendChild(el("line", {x1:x(t), x2:x(t), y1:MT, y2:MT + dados.length*passo, class:"gridline"}));
    const tx = el("text", {x:x(t), y:H - 8, class:"tick", "text-anchor":"middle"});
    tx.textContent = t; svg.appendChild(tx);
  });
  svg.appendChild(el("line", {x1:ML, x2:ML, y1:MT, y2:MT + dados.length*passo, class:"axisline"}));

  dados.forEach((d, i) => {
    const y = MT + i*passo + (passo - esp)/2;
    const larg = Math.max(2, x(d.valor) - ML);
    const g = el("g", {tabindex:"0", role:"listitem"});
    // extremidade do valor arredondada (4px), base quadrada
    const r = Math.min(4, larg);
    g.appendChild(el("path", {
      d:`M${ML},${y} H${ML+larg-r} a${r},${r} 0 0 1 ${r},${r} V${y+esp-r} a${r},${r} 0 0 1 ${-r},${r} H${ML} Z`,
      fill: opts.cor || cssv("--series-1")
    }));
    const lab = el("text", {x:ML-10, y:y+esp/2+4, class:"lbl-mark", "text-anchor":"end"});
    lab.textContent = truncar(d.rotulo, opts.maxRotulo || 22);
    g.appendChild(lab);
    const val = el("text", {x:ML+larg+8, y:y+esp/2+4, class:"val-mark"});
    val.textContent = d.valor; g.appendChild(val);
    ligarTip(g, `<b>${esc(d.rotulo)}</b>${d.valor} ${d.valor===1?"ocorrência":"ocorrências"}` +
      (d.extra ? `<div class="q">${esc(d.extra)}</div>` : ""));
    if (opts.aoClicar) { g.style.cursor = "pointer"; g.addEventListener("click", () => opts.aoClicar(d)); }
    svg.appendChild(g);
  });
}
function escalaBonita(max, n){
  // contagens são inteiras: nunca produzir marcas fraccionárias (0,5 / 1,5 …)
  const bruto = Math.max(1, max / n), mag = Math.pow(10, Math.floor(Math.log10(bruto)));
  let passo = [1,2,2.5,5,10].map(m => m*mag).find(p => p >= bruto) || mag*10;
  passo = Math.max(1, Math.round(passo));
  const out = []; for (let v = 0; v <= max + 1e-9; v += passo) out.push(v);
  return out;
}
function truncar(s, n){ s = String(s||""); return s.length > n ? s.slice(0, n-1) + "…" : s; }
