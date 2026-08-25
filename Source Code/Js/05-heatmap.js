/* Mapa de calor personagem x tipo de recurso. */

/* ------------------------------------------------------------------ heatmap
   Escala sequencial de um só matiz, clara→escura (invertida em tema escuro);
   2px de folga da cor da superfície entre células.                          */
const RAMPA = () => [0,1,2,3,4,5,6].map(i => cssv("--seq-"+i));
function luminancia(hex){
  const m = /^#?([0-9a-f]{6})$/i.exec(String(hex).trim());
  if (!m) return 1;
  const n = parseInt(m[1], 16);
  const c = [(n>>16)&255, (n>>8)&255, n&255].map(v => {
    v /= 255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4);
  });
  return 0.2126*c[0] + 0.7152*c[1] + 0.0722*c[2];
}
function heatmap(){
  const svg = $("#svg-heat"); svg.textContent = "";
  const recs = recursosFiltrados();
  const pers = [...new Set(recs.map(r => r.personagem).filter(Boolean))]
    .sort((a,b) => recs.filter(r=>r.personagem===b).length - recs.filter(r=>r.personagem===a).length)
    .slice(0, 22);
  const tipos = [...new Set(recs.map(r => r.tipo_recurso).filter(Boolean))]
    .sort((a,b) => recs.filter(r=>r.tipo_recurso===b).length - recs.filter(r=>r.tipo_recurso===a).length)
    .slice(0, 18);
  $("#escala-heat").innerHTML = "";
  if (!pers.length || !tipos.length){
    svg.setAttribute("viewBox","0 0 600 60");
    const t = el("text",{x:12,y:34,class:"lbl-mark"});
    t.textContent = "Sem dados para os filtros activos."; svg.appendChild(t); return;
  }
  const ML = 150, MT = 78, cel = Math.max(26, Math.min(46, Math.floor(700/tipos.length)));
  const W = ML + tipos.length*cel + 16, H = MT + pers.length*cel + 10;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.style.maxHeight = (H*1.15) + "px";
  const conta = (p,t) => recs.filter(r => r.personagem===p && r.tipo_recurso===t).length;
  let max = 0; pers.forEach(p => tipos.forEach(t => { max = Math.max(max, conta(p,t)); }));
  const rampa = RAMPA();
  const cor = v => v === 0 ? "transparent" : rampa[Math.min(rampa.length-1,
      Math.floor((v-1)/Math.max(1,max) * (rampa.length-1) + 0.5))];

  tipos.forEach((t,j) => {
    const x = ML + j*cel + cel/2;
    const tx = el("text", {x:x, y:MT-10, class:"tick", "text-anchor":"start",
                           transform:`rotate(-42 ${x} ${MT-10})`});
    tx.textContent = truncar(t, 16); svg.appendChild(tx);
  });
  pers.forEach((p,i) => {
    const y = MT + i*cel;
    const lab = el("text", {x:ML-10, y:y+cel/2+4, class:"lbl-mark", "text-anchor":"end"});
    lab.textContent = truncar(p, 20); svg.appendChild(lab);
    tipos.forEach((t,j) => {
      const v = conta(p,t), x = ML + j*cel;
      const g = el("g", {tabindex: v ? "0" : "-1"});
      g.appendChild(el("rect", {x:x+1, y:y+1, width:cel-2, height:cel-2, rx:3,
        fill: cor(v), stroke: v ? "none" : cssv("--grid"), "stroke-width":1}));
      if (v && cel >= 28){
        // cor do rótulo escolhida pela luminância do próprio preenchimento
        const t2 = el("text", {x:x+cel/2, y:y+cel/2+4, "text-anchor":"middle",
          "font-size":"11.5", "font-weight":"600",
          fill: luminancia(cor(v)) < 0.5 ? "#ffffff" : "#0b0b0b"});
        t2.textContent = v; g.appendChild(t2);
      }
      if (v) ligarTip(g, `<b>${esc(p)} · ${esc(t)}</b>${v} ${v===1?"ocorrência":"ocorrências"}`);
      svg.appendChild(g);
    });
  });
  // legenda de escala
  const passos = rampa.map(c => `<i style="background:${c}"></i>`).join("");
  $("#escala-heat").innerHTML =
    `<span>menos</span><span class="steps">${passos}</span><span>mais (máx. ${max})</span>`;
}
