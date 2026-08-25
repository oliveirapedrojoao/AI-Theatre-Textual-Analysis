/* Grafo de relações: componentes, disposição e desenho. */

/* --------------------------------------------------------------------- rede
   Layout determinístico (semente fixa): a mesma peça produz sempre o mesmo
   grafo, condição para o usar como figura reproduzível.                     */
function prng(semente){ let s = semente >>> 0;
  return () => { s = (s*1664525 + 1013904223) >>> 0; return s / 4294967296; }; }

function rede(){
  const svg = $("#svg-rede"); svg.textContent = "";
  const arestas = relacoesFiltradas().filter(r => r.origem && r.destino && r.origem !== r.destino);
  const nomes = [...new Set(arestas.flatMap(r => [r.origem, r.destino]))];
  $("#leg-rede").innerHTML = "";
  if (nomes.length < 2){
    svg.setAttribute("viewBox","0 0 600 60");
    const t = el("text",{x:12,y:34,class:"lbl-mark"});
    t.textContent = "Sem relações suficientes para os filtros activos."; svg.appendChild(t); return;
  }
  const W = 820;
  let H = 400;                       // altura definida pela disposição, adiante
  const grau = {}; nomes.forEach(n => grau[n] = 0);
  arestas.forEach(a => { grau[a.origem]++; grau[a.destino]++; });
  const rnd = prng(20260818);
  const nos = nomes.map(n => ({id:n, x:0, y:0, grau:grau[n]}));
  const idx = {}; nos.forEach((n,i) => idx[n.id] = i);

  const PADX = 96, PADY = 46, ITS = 420;
  const peso = {};   // arestas paralelas contam uma vez para a força
  arestas.forEach(e => { const c = e.origem < e.destino ? e.origem+"|"+e.destino : e.destino+"|"+e.origem;
    peso[c] = (peso[c]||0)+1; });

  // Uma peça por passos produz um grafo com vários componentes desligados —
  // as personagens do Passo da Freira não têm relação com as do de Noé. Uma
  // simulação global empurra-os para as margens e degenera; por isso cada
  // componente é disposto por si e os componentes são depois arrumados lado a
  // lado. O agrupamento visual passa a corresponder à estrutura da peça.
  const adj = {}; nomes.forEach(n => adj[n] = []);
  arestas.forEach(a => { adj[a.origem].push(a.destino); adj[a.destino].push(a.origem); });
  const compDe = {}, comps = [];
  nomes.forEach(n => {
    if (compDe[n] !== undefined) return;
    const id = comps.length, fila = [n], membros = [];
    compDe[n] = id;
    while (fila.length){
      const u = fila.pop(); membros.push(u);
      adj[u].forEach(v => { if (compDe[v] === undefined){ compDe[v] = id; fila.push(v); } });
    }
    comps.push(membros);
  });
  comps.sort((a,b) => b.length - a.length);

  // Fruchterman–Reingold por componente, com comprimento de aresta ideal = 1
  const caixas = comps.map(membros => {
    const sub = membros.map(id => nos[idx[id]]);
    const raio = Math.sqrt(sub.length) * 0.6;
    sub.forEach((n,i) => {
      const ang = (i/sub.length)*Math.PI*2 + rnd()*0.2;
      n.x = Math.cos(ang)*raio; n.y = Math.sin(ang)*raio;
    });
    const dentro = new Set(membros);
    const pares = Object.keys(peso).map(c => c.split("|"))
                        .filter(([o,d]) => dentro.has(o) && dentro.has(d));
    if (sub.length > 1){
      let t = Math.sqrt(sub.length) * 0.35;
      for (let it = 0; it < ITS; it++){
        sub.forEach(a => { a.dx = 0; a.dy = 0; });
        for (let i=0;i<sub.length;i++) for (let j=i+1;j<sub.length;j++){
          const a=sub[i], b=sub[j];
          let dx=a.x-b.x, dy=a.y-b.y, d=Math.hypot(dx,dy)||0.01;
          const f = 1/(d*d);                      // repulsão k²/d, com k=1
          dx*=f; dy*=f; a.dx+=dx; a.dy+=dy; b.dx-=dx; b.dy-=dy;
        }
        pares.forEach(([o,de]) => {
          const a=nos[idx[o]], b=nos[idx[de]];
          let dx=a.x-b.x, dy=a.y-b.y, d=Math.hypot(dx,dy)||0.01;
          dx=dx/d*d*d; dy=dy/d*d*d;               // atracção d²/k
          a.dx-=dx; a.dy-=dy; b.dx+=dx; b.dy+=dy;
        });
        sub.forEach(n => {
          const m = Math.hypot(n.dx, n.dy) || 1;
          n.x += n.dx/m * Math.min(m, t);
          n.y += n.dy/m * Math.min(m, t);
        });
        t *= 0.992;
      }
    }
    const xs = sub.map(n=>n.x), ys = sub.map(n=>n.y);
    const x0 = Math.min(...xs), y0 = Math.min(...ys);
    sub.forEach(n => { n.x -= x0; n.y -= y0; });   // origem na própria caixa
    return {membros,
            larg: Math.max(...xs) - x0 + 1.4,
            alt:  Math.max(...ys) - y0 + 1.4};
  });

  // arrumação em prateleiras, do maior componente para o menor
  const alvo = Math.sqrt(caixas.reduce((s,c) => s + c.larg*c.alt, 0)) * 1.7;
  let cx = 0, cy = 0, alturaLinha = 0;
  caixas.forEach(c => {
    if (cx > 0 && cx + c.larg > alvo){ cx = 0; cy += alturaLinha + 1.0; alturaLinha = 0; }
    c.membros.forEach(id => { const n = nos[idx[id]]; n.x += cx; n.y += cy; });
    cx += c.larg + 1.0;
    alturaLinha = Math.max(alturaLinha, c.alt);
  });

  // A altura do cartão sai da disposição, e não do número de nós: assim o
  // grafo ocupa o espaço que tem e não sobra faixa vazia por baixo.
  (function ajustar(){
    const xs = nos.map(n => n.x), ys = nos.map(n => n.y);
    const x0 = Math.min(...xs), x1 = Math.max(...xs);
    const y0 = Math.min(...ys), y1 = Math.max(...ys);
    const largura = Math.max(0.5, x1-x0), altura = Math.max(0.5, y1-y0);
    const e = (W - 2*PADX) / largura;
    H = Math.max(300, Math.min(820, Math.round(altura*e) + 2*PADY));
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.style.maxHeight = (H*1.05) + "px";
    const ef = Math.min(e, (H - 2*PADY)/altura);
    nos.forEach(n => {
      n.x = W/2 + (n.x - (x0+x1)/2) * ef;
      n.y = H/2 + (n.y - (y0+y1)/2) * ef;
    });
  })();

  const gArestas = el("g", {}), gNos = el("g", {});
  const destacado = a => F.relacao && a.tipo_relacao === F.relacao;
  arestas.forEach(a => {
    const s = nos[idx[a.origem]], d = nos[idx[a.destino]];
    if (!s || !d) return;
    const linha = el("line", {x1:s.x, y1:s.y, x2:d.x, y2:d.y,
      stroke: destacado(a) ? cssv("--series-1") : cssv("--axis"),
      "stroke-width": destacado(a) ? 2 : 1.25, "stroke-linecap":"round"});
    const alvo = el("line", {x1:s.x, y1:s.y, x2:d.x, y2:d.y,
      stroke:"transparent", "stroke-width":14, tabindex:"0"});
    ligarTip(alvo, `<b>${esc(a.origem)} → ${esc(a.destino)}</b>` +
      `<div>${esc(a.tipo_relacao)}</div>` +
      (a.descricao ? `<div class="q">${esc(a.descricao)}</div>` : ""));
    gArestas.appendChild(linha); gArestas.appendChild(alvo);
  });
  const rmax = Math.max.apply(null, nos.map(n => n.grau)) || 1;
  // Coloca cada rótulo acima ou abaixo do nó, o que colidir menos com os já
  // colocados; as personagens com mais relações escolhem primeiro.
  const posRotulo = {}, colocados = [];
  [...nos].sort((a,b) => b.grau - a.grau).forEach(n => {
    const r = 6 + 10*Math.sqrt(n.grau/rmax);
    const meia = (truncar(n.id,16).length * 6.0 + 4) / 2;
    let melhor = n.y - r - 6, menor = Infinity;
    [n.y - r - 6, n.y + r + 14].forEach(y => {
      const c = {x0:n.x-meia, x1:n.x+meia, y0:y-10, y1:y+3};
      let area = 0;
      colocados.forEach(p => {
        const ox = Math.min(c.x1,p.x1) - Math.max(c.x0,p.x0);
        const oy = Math.min(c.y1,p.y1) - Math.max(c.y0,p.y0);
        if (ox > 0 && oy > 0) area += ox*oy;
      });
      if (area < menor){ menor = area; melhor = y; }
    });
    colocados.push({x0:n.x-meia, x1:n.x+meia, y0:melhor-10, y1:melhor+3});
    posRotulo[n.id] = melhor;
  });
  nos.forEach(n => {
    const r = 6 + 10 * Math.sqrt(n.grau / rmax);
    const sel = selNo === n.id || F.personagem === n.id;
    const g = el("g", {tabindex:"0", role:"listitem"});
    g.appendChild(el("circle", {cx:n.x, cy:n.y, r:r,
      fill: sel ? cssv("--series-2") : cssv("--series-1"),
      stroke: cssv("--surface-1"), "stroke-width":2}));
    // o mesmo princípio do anel de superfície, aplicado ao rótulo: um contorno
    // da cor do fundo mantém o nome legível quando cruza arestas ou vizinhos
    const t = el("text", {x:n.x, y:posRotulo[n.id], "text-anchor":"middle", class:"lbl-mark",
      "paint-order":"stroke", stroke:cssv("--surface-1"), "stroke-width":"3.5",
      "stroke-linejoin":"round"});
    t.textContent = truncar(n.id, 16); g.appendChild(t);
    ligarTip(g, `<b>${esc(n.id)}</b>${n.grau} ${n.grau===1?"relação":"relações"}` +
      `<div class="q">clique para filtrar por esta personagem</div>`);
    g.style.cursor = "pointer";
    g.addEventListener("click", () => {
      $("#f-personagem").value = (F.personagem === n.id) ? "" : n.id;
      lerFiltros(); render();
    });
    gNos.appendChild(g);
  });
  svg.appendChild(gArestas); svg.appendChild(gNos);

  // O tipo de relação não é codificado por cor (todas as arestas são hairlines
  // neutras): estes são botões de filtro que destacam o tipo escolhido.
  const tipos = {};
  arestas.forEach(a => tipos[a.tipo_relacao] = (tipos[a.tipo_relacao]||0)+1);
  const leg = $("#leg-rede");
  leg.innerHTML = "";
  Object.entries(tipos).sort((a,b) => b[1]-a[1]).forEach(([t,n]) => {
    const b = document.createElement("button");
    b.className = "chip"; b.type = "button";
    b.setAttribute("aria-pressed", String(F.relacao === t));
    b.textContent = `${t} · ${n}`;
    b.addEventListener("click", () => {
      $("#f-relacao").value = (F.relacao === t) ? "" : t; lerFiltros(); render();
    });
    leg.appendChild(b);
  });
  const nota = document.createElement("span");
  nota.className = "key muted";
  nota.textContent = "escolhe um tipo para o destacar no grafo";
  leg.appendChild(nota);
}
