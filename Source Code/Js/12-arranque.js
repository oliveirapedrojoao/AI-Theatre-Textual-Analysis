/* Ordem de arranque. Tem de ser o último ficheiro. */

cabecalho(); tiles(); preencherFiltros(); ligarChrome(); prosa(); lerFiltros(); render();
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", render);
