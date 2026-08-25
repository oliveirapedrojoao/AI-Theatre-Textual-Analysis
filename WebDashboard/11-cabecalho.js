/* Título, metadados da peça e rodapé. */

function cabecalho(){
  const m = D.meta || {};
  document.title = (m.titulo || "Peça") + " — análise";
  $("#titulo").textContent = m.titulo || "Peça sem título";
  $("#subtitulo").textContent = [m.genero, m.datacao].filter(Boolean).join(" · ");
  const campos = [
    ["Proveniência", m.proveniencia], ["Transcrição", m.ficheiro],
    ["Linhas", m.n_linhas], ["Modelo", m.modelo], ["Análise", m.data_execucao]
  ].filter(c => c[1]);
  $("#meta").innerHTML = campos.map(c => `<span><b>${esc(c[0])}:</b> ${esc(c[1])}</span>`).join("");
  $("#rodape").innerHTML =
    `Gerado por <b>presepios</b> a partir de ${esc(m.ficheiro||"")}. ` +
    `As tabelas e os gráficos derivam exclusivamente dos CSVs validados; ` +
    `as citações foram cotejadas automaticamente com a transcrição. ` +
    `Toda a leitura interpretativa carece de confirmação por especialista.`;
}
