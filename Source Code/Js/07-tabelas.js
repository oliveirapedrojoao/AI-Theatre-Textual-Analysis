/* Tabelas ordenáveis e marca de cotejo das citações. */

/* ------------------------------------------------------------------ tabelas */
function tabela(alvo, colunas, linhas, opts){
  opts = opts || {};
  const cab = colunas.map(c => `<th data-k="${c.k}">${esc(c.t)}</th>`).join("");
  const corpo = linhas.map(l => "<tr>" + colunas.map(c => {
    const v = c.render ? c.render(l) : esc(l[c.k]);
    return `<td class="${c.cls||""}">${v}</td>`;
  }).join("") + "</tr>").join("");
  $(alvo).innerHTML = linhas.length
    ? `<div class="tbl-wrap"><table><thead><tr>${cab}</tr></thead><tbody>${corpo}</tbody></table></div>`
    : `<p class="muted" style="font-size:13px">Sem registos para os filtros activos.</p>`;
  // ordenação por clique no cabeçalho
  $$(alvo + " th").forEach(th => th.addEventListener("click", () => {
    const k = th.dataset.k;
    opts.estado = opts.estado || {};
    const asc = opts.estado.k === k ? !opts.estado.asc : true;
    opts.estado = {k, asc};
    linhas.sort((a,b) => {
      const va = a[k], vb = b[k];
      const na = parseFloat(va), nb = parseFloat(vb);
      const cmp = (!isNaN(na) && !isNaN(nb)) ? na-nb : String(va||"").localeCompare(String(vb||""), "pt");
      return asc ? cmp : -cmp;
    });
    tabela(alvo, colunas, linhas, opts);
  }));
}

const SIMBOLO_VERIF = {
  "verificada":  ["●", "--good", "citação localizada na transcrição, na posição indicada"],
  "deslocada":   ["◐", "--warning", "citação existe no texto, mas fora da localização declarada"],
  "não encontrada": ["✕", "--critical", "citação não encontrada na transcrição — rever manualmente"],
  "sem localização": ["○", "--text-muted", "sem marcador de linha utilizável"]
};
function marcaVerificacao(v){
  const s = SIMBOLO_VERIF[v]; if (!s) return "";
  return `<span class="badge" title="${esc(s[2])}"><span style="color:${cssv(s[1])}">${s[0]}</span>${esc(v)}</span>`;
}
