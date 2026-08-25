# web

As fontes do dashboard, separadas por linguagem. **Não são servidas como estão:**
`src/presepios/visualizacao/dashboard.py` junta-as num único ficheiro HTML
autocontido, com os dados da peça embutidos, que é o que o pipeline entrega.

```
web/
├── dashboard.html        esqueleto e marcação; contém os marcadores de injecção
├── estilos/
│   └── dashboard.css     paleta (nos dois temas), componentes, impressão
└── scripts/
    ├── 01-base.js        dados, utilitários, estado
    ├── 02-filtros.js     que registos estão visíveis
    ├── 03-tooltip.js     camada de passagem do cursor
    ├── 04-barras.js      gráfico de barras horizontais
    ├── 05-heatmap.js     mapa de calor personagem × recurso
    ├── 06-rede.js        grafo de relações
    ├── 07-tabelas.js     tabelas ordenáveis e marca de cotejo
    ├── 08-render.js      redesenho de tudo o que depende dos filtros
    ├── 09-relatorio.js   cartões de topo, prosa e validação
    ├── 10-interface.js   controlos, tema, impressão, exportações
    ├── 11-cabecalho.js   título, metadados, rodapé
    └── 12-arranque.js    ordem de arranque
```

## Regras

- **Os scripts são concatenados por ordem alfabética**, dentro de um único
  invólucro `(function(){ "use strict"; … })()`. Partilham portanto um escopo:
  não há `import`/`export`, e uma função definida num ficheiro é visível em
  todos os outros. O prefixo numérico é o que fixa a ordem — mantém-no ao
  acrescentar ficheiros, e mantém `12-arranque.js` em último.
- **Só `12-arranque.js` executa alguma coisa ao carregar.** Todos os outros
  ficheiros apenas definem. É essa disciplina que permite concatená-los por
  qualquer ordem de escrita sem partir nada.
- **Sem dependências externas.** Nada de CDN, nada de `fetch`, nada de
  `localStorage` ou `sessionStorage`. O ficheiro tem de funcionar offline e sem
  estado guardado no navegador.
- **As cores vivem no CSS, não no JavaScript.** Os scripts leem-nas com
  `cssv("--series-1")`, o que faz a troca de tema acontecer num só sítio e
  garante que a exportação SVG sai com as cores do tema activo.

## Marcadores de injecção

`dashboard.html` contém quatro marcadores que o gerador substitui:

| Marcador | Substituído por |
|---|---|
| `<!--__ESTILOS__-->` | `<style>` com `estilos/dashboard.css` |
| `<!--__SCRIPTS__-->` | `<script>` com todos os `scripts/*.js` |
| `__TITULO__` | o título da peça |
| `__DADOS_JSON__` | o JSON com tabelas, métricas, validação e prosa |

## Trabalhar nas fontes

Não há passo de compilação. Edita o que precisas e regera um dashboard a partir
de dados já existentes, sem chamar a API:

```bash
presepios reprocessar corpus/respostas/<peça> -c corpus/pecas/<peça>.yaml
```

ou, sem corpus nenhum, sobre a amostra sintética:

```bash
presepios reprocessar exemplos/respostas_exemplo -c exemplos/entremez_exemplo.yaml
```
