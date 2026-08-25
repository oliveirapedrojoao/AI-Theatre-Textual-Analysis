/* Controlos: filtros, tema, impressão e exportações. */

/* ------------------------------------------------------------------ chrome */
function preencherFiltros(){
  const add = (sel, vals) => {
    const s = $(sel);
    vals.filter(Boolean).sort((a,b) => String(a).localeCompare(String(b), "pt"))
        .forEach(v => { const o = document.createElement("option"); o.value = v; o.textContent = v; s.appendChild(o); });
  };
  add("#f-personagem", [...new Set(D.personagens.map(p => p.personagem))]);
  add("#f-tipo", [...new Set(D.recursos.map(r => r.tipo_recurso))]);
  add("#f-relacao", [...new Set(D.relacoes.map(r => r.tipo_relacao))]);
  add("#f-certeza", [...new Set(D.vernaculo.map(v => v.grau_certeza))]);
}
function lerFiltros(){
  F.personagem = $("#f-personagem").value;
  F.tipo = $("#f-tipo").value;
  F.relacao = $("#f-relacao").value;
  F.certeza = $("#f-certeza").value;
  F.texto = $("#f-texto").value.trim();
}
function descarregar(nome, conteudo, tipo){
  const b = new Blob([conteudo], {type: tipo});
  const u = URL.createObjectURL(b);
  const a = document.createElement("a");
  a.href = u; a.download = nome; document.body.appendChild(a); a.click();
  a.remove(); setTimeout(() => URL.revokeObjectURL(u), 1000);
}
function paraCSV(linhas, colunas){
  const q = v => { v = String(v==null?"":v); return /[",\n;]/.test(v) ? '"'+v.replace(/"/g,'""')+'"' : v; };
  return "﻿" + [colunas.join(",")].concat(
    linhas.map(l => colunas.map(c => q(l[c])).join(","))).join("\n");
}

function ligarChrome(){
  $$(".card header .acts button[data-view]").forEach(b => b.addEventListener("click", () => {
    const card = b.closest(".card");
    card.querySelectorAll("button[data-view]").forEach(x =>
      x.setAttribute("aria-pressed", String(x === b)));
    card.querySelector(".view-chart").classList.toggle("hidden", b.dataset.view !== "chart");
    card.querySelector(".view-table").classList.toggle("hidden", b.dataset.view !== "table");
  }));
  $$("button[data-svg]").forEach(b => b.addEventListener("click", () => {
    const svg = $("#svg-" + b.dataset.svg).cloneNode(true);
    svg.setAttribute("xmlns", NS);
    svg.setAttribute("style", `background:${cssv("--surface-1")};font-family:${cssv("--sans")}`);
    // fixa as cores dos textos (as variáveis CSS não sobrevivem à exportação)
    svg.querySelectorAll("text").forEach(t => {
      const c = t.getAttribute("class")||"";
      t.setAttribute("fill", t.getAttribute("fill") ||
        (c.includes("tick") ? cssv("--text-muted") : cssv("--text-secondary")));
      t.setAttribute("font-size", c.includes("tick") ? "11" : "11.5");
    });
    svg.querySelectorAll(".gridline").forEach(l => l.setAttribute("stroke", cssv("--grid")));
    svg.querySelectorAll(".axisline").forEach(l => l.setAttribute("stroke", cssv("--axis")));
    descarregar(`${D.meta.slug||"peca"}-${b.dataset.svg}.svg`,
      new XMLSerializer().serializeToString(svg), "image/svg+xml");
  }));
  const mapaCSV = {
    recursos: [D.recursos, ["id","tipo_recurso","citacao","localizacao","personagem","interpretacao","verificacao"]],
    personagens: [D.personagens, ["personagem","funcao_dramatica","simbologia"]],
    vernaculo: [D.vernaculo, ["expressao","significado_epoca","grau_certeza","localizacao","n_ocorrencias"]]
  };
  $$("button[data-csv]").forEach(b => b.addEventListener("click", () => {
    const [linhas, cols] = mapaCSV[b.dataset.csv];
    descarregar(`${D.meta.slug||"peca"}-${b.dataset.csv}.csv`, paraCSV(linhas, cols), "text/csv");
  }));
  ["#f-personagem","#f-tipo","#f-relacao","#f-certeza"].forEach(s =>
    $(s).addEventListener("change", () => { lerFiltros(); render(); }));
  let t; $("#f-texto").addEventListener("input", () => {
    clearTimeout(t); t = setTimeout(() => { lerFiltros(); render(); }, 180); });
  $("#limpar").addEventListener("click", () => {
    ["#f-personagem","#f-tipo","#f-relacao","#f-certeza"].forEach(s => $(s).value = "");
    $("#f-texto").value = ""; selNo = null; lerFiltros(); render();
  });
  $("#tema").addEventListener("click", () => {
    const actual = document.documentElement.getAttribute("data-theme");
    const escuroSO = matchMedia("(prefers-color-scheme: dark)").matches;
    const proximo = actual ? (actual === "dark" ? "light" : "dark") : (escuroSO ? "light" : "dark");
    document.documentElement.setAttribute("data-theme", proximo);
    render();
  });
  $("#imprimir").addEventListener("click", () => window.print());
}
