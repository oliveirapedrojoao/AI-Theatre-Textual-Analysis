/* Estado dos filtros e selecção dos registos visíveis. */

/* --------------------------------------------------------------- filtragem */
function passaTexto(campos){
  if (!F.texto) return true;
  const q = F.texto.toLowerCase();
  return campos.some(c => String(c||"").toLowerCase().includes(q));
}
function recursosFiltrados(){
  return D.recursos.filter(r =>
    (!F.personagem || r.personagem === F.personagem) &&
    (!F.tipo || r.tipo_recurso === F.tipo) &&
    passaTexto([r.citacao, r.interpretacao, r.personagem, r.tipo_recurso, r.localizacao]));
}
function relacoesFiltradas(){
  return D.relacoes.filter(r =>
    (!F.relacao || r.tipo_relacao === F.relacao) &&
    (!F.personagem || r.origem === F.personagem || r.destino === F.personagem) &&
    passaTexto([r.origem, r.destino, r.tipo_relacao, r.descricao]));
}
function vernaculoFiltrado(){
  return D.vernaculo.filter(v =>
    (!F.certeza || v.grau_certeza === F.certeza) &&
    passaTexto([v.expressao, v.significado_epoca, v.localizacao]));
}
function personagensFiltradas(){
  return D.personagens.filter(p =>
    (!F.personagem || p.personagem === F.personagem) &&
    passaTexto([p.personagem, p.funcao_dramatica, p.simbologia]));
}
