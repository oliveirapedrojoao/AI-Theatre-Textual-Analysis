# Arquitectura

O repositório está dividido segundo dois critérios que se cruzam: **por
linguagem** (o que corre em Python e o que corre no navegador vivem separados) e
**por função** (cada pasta responde por uma etapa do fluxo de trabalho).

```
presepios/
├── src/presepios/     PYTHON — o pipeline
│   ├── nucleo/            configuração, esquemas das tabelas, orquestração
│   ├── texto/             ler, numerar, detectar, segmentar, normalizar
│   ├── modelo/            os prompts e o cliente da API  ← única fronteira com a rede
│   ├── dados/             extrair as tabelas das respostas e validá-las
│   ├── visualizacao/      montar o dashboard a partir de web/
│   └── cli.py             interface de linha de comandos
│
├── web/               NAVEGADOR — o dashboard, separado por linguagem
│   ├── dashboard.html     esqueleto e marcação
│   ├── estilos/           CSS
│   └── scripts/           JavaScript, um ficheiro por responsabilidade
│
├── corpus/            DADOS — transcrições, configurações, respostas (fora do git)
├── exemplos/          amostra sintética, para correr o pipeline sem API
├── testes/            suite que corre sem rede
├── ferramentas/       scripts auxiliares de empacotamento
└── docs/              este ficheiro e o protocolo de análise
```

## O fluxo, de ponta a ponta

```
corpus/transcricoes/peça.txt
        │
        ▼  texto/          carrega, valida, numera cada linha [L0042],
        │                  detecta rubricas, cenas e fólios
        ▼  modelo/         Ronda 1 (Tarefas 1–2) → análise em prosa
        │                  Ronda 2 (Tarefa 3)    → cinco tabelas CSV
        ▼  dados/          extrai as tabelas, coteja cada citação com o
        │                  original, verifica integridade, recalcula frequências
        ▼  visualizacao/   junta web/ num único HTML com os dados embutidos
        │
        ▼  saidas/<peça>/  CSVs + relatório de validação + dashboard
```

## Porque é que cada grupo existe

**`nucleo/`** guarda o que todos os outros precisam de conhecer.
`esquemas.py` é a fonte única de verdade sobre as colunas das cinco tabelas: é
importado pelos prompts (para as pedir ao modelo), pelo extractor (para as
reconhecer numa resposta) e pelo validador (para as verificar). Alterar uma
coluna aí propaga-se a todo o pipeline de uma só vez.

**`texto/`** isola tudo o que depende das convenções de transcrição, que variam
de fonte para fonte. `padroes.py` concentra os regex — é o ficheiro a estender
quando uma transcrição nova usar uma convenção desconhecida; tudo o resto
passa a reconhecê-la sem alteração. `normalizacao.py` produz as formas
canónicas usadas no cotejo e nunca escritas em disco: a ortografia original é
sempre preservada no que é gravado.

**`modelo/`** é a única parte do pacote que fala com a rede. Manter esta
fronteira estreita é deliberado: todo o resto trabalha sobre texto e tabelas e
pode ser corrido, testado e depurado sem API e sem gastar tokens — que é o que
o comando `reprocessar` faz.

**`dados/`** é a camada de desconfiança. Extrai o que o modelo devolveu e
verifica-o contra o original. Nada é corrigido em silêncio: uma citação que não
exista no texto é assinalada como erro, não emendada.

**`visualizacao/`** não contém código de navegador — apenas o monta. As Tarefas
1 a 3 são feitas pelo modelo; a Tarefa 4, as visualizações, é feita por código a
partir das tabelas já validadas. É isso que garante que nenhum gráfico mostra
algo que não esteja nos CSVs, e que o resultado é reproduzível: a disposição do
grafo usa semente fixa, pelo que a mesma peça produz sempre a mesma figura.

## `web/` — fontes separadas, ficheiro único

O dashboard entregue tem de ser **um só ficheiro** HTML, sem pedidos de rede:
abre offline, viaja por email e pode ser arquivado ao lado dos CSVs que o
originaram. Mas um ficheiro único de mil linhas com HTML, CSS e JavaScript
misturados não se lê nem se versiona.

A solução é separar as fontes e juntá-las na geração.
`visualizacao/dashboard.py` lê `web/dashboard.html`, injecta o CSS dentro de um
`<style>`, concatena os scripts por ordem alfabética dentro de um único
invólucro `(function(){ … })()` e embute os dados da peça num
`<script type="application/json">`.

Duas consequências práticas:

- **Os scripts partilham um escopo.** Não são módulos ES e não precisam de
  importações entre si; por isso levam prefixo numérico, que fixa a ordem de
  concatenação. `12-arranque.js` é o último e é o único que executa alguma
  coisa no carregamento.
- **Para instalar como pacote**, corre `python ferramentas/sincronizar_web.py`
  antes de `pip install .`: um *wheel* não pode levar ficheiros de fora do
  pacote, e o script copia `web/` para dentro dele. Em desenvolvimento não é
  preciso — o gerador encontra `web/` na raiz do repositório.

## Onde mexer, consoante o que queres mudar

| Quero… | Ficheiro |
|---|---|
| ajustar o que se pede ao modelo | `src/presepios/modelo/prompts.py` |
| acrescentar ou mudar uma coluna das tabelas | `src/presepios/nucleo/esquemas.py` |
| reconhecer uma convenção nova de transcrição | `src/presepios/texto/padroes.py` |
| endurecer ou afrouxar a validação | `src/presepios/dados/validacao.py` |
| mudar cores, tipos ou espaçamentos | `web/estilos/dashboard.css` |
| mudar um gráfico | `web/scripts/04-barras.js`, `05-heatmap.js`, `06-rede.js` |
| acrescentar um cartão ou secção | `web/dashboard.html` + `web/scripts/09-relatorio.js` |
| acrescentar um comando | `src/presepios/cli.py` |
