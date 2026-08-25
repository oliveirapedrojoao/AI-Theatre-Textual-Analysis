/* Cartões de topo, prosa da análise e relatório de validação. */

/* -------------------------------------------------------------------- topo */
function tiles(){
  const m = D.metricas || {}, v = D.validacao && D.validacao.metricas || {};
  const pct = v.citacoes_verificadas_pct;
  let estado = ["--text-muted", "○", "cotejo não executado"];
  if (typeof pct === "number")
    estado = pct >= 95 ? ["--good","●","citações confirmadas no original"]
           : pct >= 80 ? ["--warning","◐","rever as citações assinaladas"]
                       : ["--critical","✕","revisão manual necessária"];
  const cards = [
    {cls:"hero", lbl:"Ocorrências de recursos expressivos", val:m.n_recursos||0,
     note:(m.densidade_recursos_por_100_linhas!=null ? m.densidade_recursos_por_100_linhas+" por 100 linhas" : "")},
    {lbl:"Tipos de recurso", val:m.n_tipos_recurso||0},
    {lbl:"Personagens", val:m.n_personagens||0},
    {lbl:"Relações mapeadas", val:m.n_relacoes||0, note:(m.n_tipos_relacao||0)+" tipos"},
    {lbl:"Entradas de vernáculo", val:m.n_vernaculo||0},
    {lbl:"Citações verificadas", val:(typeof pct==="number" ? pct+"%" : "—"),
     note:`<span class="badge"><span style="color:${cssv(estado[0])}">${estado[1]}</span>${estado[2]}</span>`}
  ];
  $("#tiles").innerHTML = cards.map(c =>
    `<div class="tile ${c.cls||""}"><div class="lbl">${c.lbl}</div>` +
    `<div class="val">${c.val}</div>${c.note?`<div class="note">${c.note}</div>`:""}</div>`).join("");
}

function markdownLeve(txt){
  if (!txt) return "";
  // A análise vem com mudança de linha fixa; junta-se cada parágrafo numa só
  // linha para o texto refluir com a largura da coluna em vez de herdar as
  // quebras do ficheiro.
  const linhas = esc(txt).split("\n");
  let out = "", lista = false, buf = [];
  const despejar = () => { if (buf.length){ out += `<p>${inline(buf.join(" "))}</p>`; buf = []; } };
  for (let l of linhas){
    const h = l.match(/^(#{1,6})\s+(.*)$/);
    const li = l.match(/^\s*[-*•]\s+(.*)$/);
    if (li){
      despejar();
      if (!lista){ out += "<ul>"; lista = true; }
      out += "<li>" + inline(li[1]) + "</li>"; continue;
    }
    if (lista && l.trim() && /^\s{2,}\S/.test(l)){        // continuação do item
      out = out.replace(/<\/li>$/, " " + inline(l.trim()) + "</li>"); continue;
    }
    if (lista){ out += "</ul>"; lista = false; }
    if (h){ despejar(); out += `<h4>${inline(h[2])}</h4>`; continue; }
    if (!l.trim()){ despejar(); continue; }
    buf.push(l.trim());
  }
  despejar();
  if (lista) out += "</ul>";
  return out;
  function inline(s){
    return s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
            .replace(/(^|[\s(])\*([^*\n]+)\*/g, "$1<em>$2</em>")
            .replace(/`([^`]+)`/g, "<code>$1</code>");
  }
}

function prosa(){
  const a = D.analise || {};
  const blocos = [
    ["Personagens, simbologia e relações", a.personagens],
    ["Vernáculo e recursos expressivos", a.vernaculo_recursos]
  ].filter(b => b[1]);
  $("#prosa").innerHTML = blocos.map((b,i) =>
    `<details ${i===0?"open":""}><summary>${esc(b[0])}</summary>` +
    `<div class="prosa">${markdownLeve(b[1])}</div></details>`).join("")
    || `<p class="muted">Sem prosa registada.</p>`;

  $("#limitacoes").innerHTML = markdownLeve(a.limitacoes) ||
    `<p class="muted">Nenhuma limitação assinalada pela análise.</p>`;

  const val = D.validacao || {};
  const bloco = (t, arr, marca) => (arr && arr.length)
    ? `<details><summary>${t} (${arr.length})</summary><ul class="aviso-list">` +
      arr.map(x => `<li>${marca} ${esc(x)}</li>`).join("") + "</ul></details>" : "";
  $("#validacao").innerHTML =
    bloco("Erros de validação", val.erros, "✗") +
    bloco("Avisos", val.avisos, "!") +
    bloco("Normalizações aplicadas", val.notas, "·");
}
