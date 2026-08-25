/* Camada de passagem do cursor, comum a todos os gráficos. */

/* ---------------------------------------------------------------- tooltip */
const tip = $("#tip");
function mostrarTip(ev, html){
  tip.innerHTML = html; tip.style.opacity = 1;
  const r = tip.getBoundingClientRect();
  let x = ev.clientX + 14, y = ev.clientY + 14;
  if (x + r.width > innerWidth - 8) x = ev.clientX - r.width - 14;
  if (y + r.height > innerHeight - 8) y = ev.clientY - r.height - 14;
  tip.style.left = x + "px"; tip.style.top = y + "px";
}
function esconderTip(){ tip.style.opacity = 0; }
function ligarTip(node, html){
  node.addEventListener("mousemove", e => mostrarTip(e, html));
  node.addEventListener("mouseleave", esconderTip);
  node.addEventListener("focus", e => {
    const b = node.getBoundingClientRect();
    mostrarTip({clientX:b.left+b.width/2, clientY:b.top+b.height/2}, html);
  });
  node.addEventListener("blur", esconderTip);
}
