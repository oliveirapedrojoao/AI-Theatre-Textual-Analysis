/* Arranque dos dados e utilitários partilhados. */

const D = JSON.parse(document.getElementById("dados").textContent);
const $ = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));
const esc = s => String(s==null?"":s).replace(/[&<>"']/g, c =>
  ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const NS = "http://www.w3.org/2000/svg";
const el = (n, a) => { const e = document.createElementNS(NS, n);
  for (const k in (a||{})) e.setAttribute(k, a[k]); return e; };
const cssv = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

/* ------------------------------------------------------------------ estado */
const F = {personagem:"", tipo:"", relacao:"", certeza:"", texto:""};
let selNo = null;
