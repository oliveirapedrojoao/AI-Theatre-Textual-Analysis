/* Redesenho de tudo o que depende dos filtros. */

/* -------------------------------------------------------------------- render */
function render(){
  const recs = recursosFiltrados();
  const vern = vernaculoFiltrado();
  const rels = relacoesFiltradas();

  // contador do filtro
  $("#contador").textContent =
    `${recs.length} ocorrências · ${rels.length} relações · ${vern.length} termos`;

  // barras de frequência
  const freq = {};
  recs.forEach(r => { if (r.tipo_recurso) freq[r.tipo_recurso] = (freq[r.tipo_recurso]||0)+1; });
  const dadosFreq = Object.entries(freq).sort((a,b) => b[1]-a[1])
    .map(([t,n]) => ({rotulo:t, valor:n}));
  barras("#svg-freq", dadosFreq, {aoClicar: d => {
    $("#f-tipo").value = (F.tipo === d.rotulo) ? "" : d.rotulo; lerFiltros(); render();
  }});
  tabela("#tbl-freq", [{k:"tipo_recurso",t:"Tipo de recurso"},{k:"n_ocorrencias",t:"Ocorrências",cls:"num"}],
    dadosFreq.map(d => ({tipo_recurso:d.rotulo, n_ocorrencias:d.valor})));

  // barras de vernáculo
  const dadosVern = vern.map(v => ({rotulo:v.expressao, valor:+v.n_ocorrencias||1, extra:v.significado_epoca}))
    .sort((a,b) => b.valor-a.valor).slice(0,15);
  barras("#svg-vern", dadosVern, {margemEsq:180, maxRotulo:26});
  tabela("#tbl-vern", [{k:"expressao",t:"Expressão"},{k:"n_ocorrencias",t:"Ocorrências",cls:"num"}],
    dadosVern.map(d => ({expressao:d.rotulo, n_ocorrencias:d.valor})));

  heatmap();
  // tabela-gémea do mapa de calor
  const parPers = {};
  recs.forEach(r => { const k = (r.personagem||"—") + "\u0001" + (r.tipo_recurso||"—");
    parPers[k] = (parPers[k]||0)+1; });
  tabela("#tbl-heat",
    [{k:"personagem",t:"Personagem"},{k:"tipo_recurso",t:"Tipo de recurso"},{k:"n",t:"Ocorrências",cls:"num"}],
    Object.entries(parPers).map(([k,n]) => {
      const [p,t] = k.split("\u0001"); return {personagem:p, tipo_recurso:t, n:n};
    }).sort((a,b) => b.n-a.n));

  rede();
  tabela("#tbl-rede",
    [{k:"origem",t:"Origem"},{k:"destino",t:"Destino"},{k:"tipo_relacao",t:"Tipo"},{k:"descricao",t:"Interpretação"}],
    rels.slice());

  tabela("#tbl-recursos", [
    {k:"id", t:"Id"},
    {k:"tipo_recurso", t:"Recurso"},
    {k:"personagem", t:"Personagem"},
    {k:"localizacao", t:"Local", cls:"loc"},
    {k:"citacao", t:"Citação", render: r => `<span class="cit">${esc(r.citacao)}</span>`},
    {k:"interpretacao", t:"Interpretação"},
    {k:"verificacao", t:"Cotejo", render: r => marcaVerificacao(r.verificacao)}
  ], recs.slice());

  tabela("#tbl-pers", [
    {k:"personagem", t:"Personagem"},
    {k:"funcao_dramatica", t:"Função dramática"},
    {k:"simbologia", t:"Carga simbólica"}
  ], personagensFiltradas().slice());

  tabela("#tbl-vernaculo", [
    {k:"expressao", t:"Expressão"},
    {k:"significado_epoca", t:"Significado de época"},
    {k:"grau_certeza", t:"Certeza"},
    {k:"localizacao", t:"Local", cls:"loc"},
    {k:"n_ocorrencias", t:"N.º", cls:"num"}
  ], vern.slice());
}
