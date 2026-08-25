**Análise assistida de literatura dramática portuguesa setecentista — com cada citação verificada contra o original.**

Este projecto nasceu do estudo dos presépios teatrais representados em Évora e
em Lisboa no século XVIII: autos de Natal compostos por passos autónomos, que
alternam o registo bíblico em verso com entremezes cómicos em prosa, e que
sobreviveram em cópias manuscritas cheias de grafias instáveis, lacunas e mãos
sucessivas. São textos que resistem à leitura rápida e que, por isso mesmo,
raramente são estudados na sua totalidade.

O `presepios` pega numa transcrição em texto simples e devolve uma primeira
sistematização completa da peça — personagens, relações, vernáculo, recursos
expressivos — em tabelas prontas para reutilizar e num dashboard interactivo.
Faz esse trabalho recorrendo a um modelo de linguagem, mas **nunca lhe pede que
seja acreditado**: cada citação que a análise produz é depois procurada no texto
original e marcada como confirmada ou suspeita, antes de chegar a qualquer
gráfico.

---

## O problema

Um modelo de linguagem lê uma peça de mil linhas em segundos e produz uma
análise plausível. É precisamente aí que está o perigo: *plausível* não é
*verdadeiro*. Uma citação ligeiramente reescrita, uma localização inventada, uma
personagem que não existe — nada disso salta à vista num relatório bem escrito,
e todo o trabalho posterior fica contaminado. Para investigação filológica, uma
ferramenta que não deixe verificar o que afirma não é uma ferramenta: é um risco.

Acresce um segundo problema, específico destes textos. A ortografia setecentista
não é ruído a limpar — é evidência. Uma metátese como *perceito* por preceito,
ou a forma *molher*, dizem alguma coisa sobre o copista e sobre a fala da época.
Qualquer sistema que normalize a grafia «para facilitar» destrói o objecto que
devia estudar.

Este projecto foi construído à volta destes dois problemas.

## O que faz

O pipeline executa um protocolo de análise filológica em quatro tarefas —
personagens e relações, vernáculo e recursos expressivos, sistematização em
tabelas, visualizações — e acrescenta-lhe uma camada de verificação que o
protocolo original não previa.

```
transcrição .txt  →  Ronda 1        →  Ronda 2       →  validação  →  dashboard
   numerada          Tarefas 1–2       Tarefa 3          cotejo        Tarefa 4
                     análise em        tabelas CSV       de cada       HTML
                     prosa                               citação       autocontido
```

Uma peça de cada vez, num único comando.

## Objectivos

**Tornar exaustiva uma leitura que hoje é forçosamente selectiva.** Percorrer
mil linhas registando cada metáfora, cada regionalismo e cada relação de
personagem é trabalho que, feito à mão, se limita aos exemplos mais salientes.
O objectivo não é substituir essa leitura, é dar-lhe uma base sistemática sobre
a qual decidir.

**Produzir dados reutilizáveis, e não apenas prosa.** As cinco tabelas CSV são o
verdadeiro produto: alimentam os gráficos, entram numa base de dados, cruzam-se
com outras peças e citam-se num artigo. O relatório em prosa é a justificação
delas, não o contrário.

**Garantir rastreabilidade até à linha.** Qualquer afirmação da análise tem de
poder ser seguida até ao lugar exacto do manuscrito que a sustenta — e esse
lugar tem de poder ser conferido automaticamente, não por confiança.

**Ser reproduzível.** A mesma peça, com as mesmas respostas, produz sempre
exactamente as mesmas tabelas e exactamente a mesma figura — incluindo a
disposição do grafo de relações. Uma figura de artigo não pode mudar de aspecto
entre execuções.

**Permitir a comparação entre peças.** As tabelas têm esquema fixo, igual para
todas as peças. É o que torna possível, mais tarde, perguntar em que difere o
presépio de Évora do da Graça.

## Princípios

Estes são os compromissos que governam as decisões técnicas do projecto. Estão
aqui porque explicam por que razão o código faz o que faz — e por que razão, em
vários pontos, faz menos do que poderia.

### A citação é verificada, ou é assinalada

Toda a citação produzida pela análise é procurada no texto da transcrição:
primeiro à volta da localização declarada, depois na peça inteira. Fica marcada
como **verificada** (está onde diz estar), **deslocada** (existe, mas noutro
sítio) ou **não encontrada**. A última é tratada como erro de execução, não como
aviso — o pipeline termina com código de saída diferente de zero.

O cotejo compara formas reduzidas — sem acentos, sem pontuação, sem espaços — o
que o torna imune às quebras de linha que as transcrições diplomáticas conservam
do manuscrito e que partem palavras a meio (`a sua mes` / `ma cabeça`). Essa
redução existe apenas em memória e nunca toca no que é gravado.

### Nada é corrigido em silêncio

Quando a validação encontra um problema — uma personagem que aparece nas
relações mas não no elenco, um grau de certeza fora do vocabulário, uma
frequência mal contada — regista-o em `validacao.md` com o detalhe do que fez.
As frequências são recalculadas a partir das ocorrências reais e a divergência
é declarada. As citações suspeitas ficam suspeitas: não são emendadas nem
apagadas. O relatório existe para dizer ao investigador **onde olhar primeiro**.

### A ortografia original não se normaliza

O que é escrito em disco conserva sempre a grafia da fonte, com `[sic]` apenas
onde a forma pudesse ser tomada por erro de transcrição. As variantes gráficas
são tratadas como dado lexical, não como sujidade.

### Constatação e inferência não se confundem

O protocolo obriga a distinguir o que o texto diz do que o intérprete deduz, e a
declarar o grau de certeza de cada leitura — **seguro**, **provável** ou
**hipotético**. É vocabulário controlado, normalizado na validação, e viaja com
os dados.

### O sentido é o da época, não o de hoje

A interpretação é historicamente situada, com apoio na lexicografia coeva
(Bluteau, 1712–1728; Morais Silva, 1789). Onde o sentido setecentista diverge do
actual, a divergência é assinalada explicitamente — *clausurar* aplicado à arca
de Noé tem o valor da clausura monástica; *pensões da vida* significa encargos,
não rendimentos.

### Os gráficos não sabem nada que as tabelas não digam

As três primeiras tarefas são feitas pelo modelo; a quarta, as visualizações, é
feita por código, a partir dos CSVs já validados. Nenhum gráfico pode mostrar
algo que não esteja nas tabelas, e nenhuma figura depende de o modelo ter
acertado no desenho. É também o que garante a reprodutibilidade.

### As lacunas ficam lacunas

Passagens ilegíveis, leituras alternativas do transcritor e localizações
incertas são registadas numa secção própria em vez de preenchidas por
conjectura. Um texto com buracos deve continuar a mostrá-los.

### O código não substitui a leitura

Este ponto é o mais importante. O que sai daqui é uma primeira sistematização
verificável — não uma interpretação acabada. As leituras interpretativas
carecem de confirmação por especialista, e o dashboard di-lo no seu próprio
rodapé. A ferramenta serve para libertar tempo de inventariação e devolvê-lo à
decisão crítica; não para a tomar.

## Como funciona

**Preparação.** A transcrição é lida, validada e numerada linha a linha
(`[L0042]`). Essa numeração é o sistema de coordenadas de que tudo o resto
depende: sem ela não há localização estável nem cotejo possível. Ao mesmo tempo,
são detectadas as rubricas de fala, os marcos de estrutura (`Cena`, `Passo de…`,
`Vista de…`) e os fólios — que servirão de contraprova ao elenco proposto pela
análise.

**Ronda 1 — Tarefas 1 e 2.** O modelo recebe a peça inteira e produz a análise
em prosa: elenco, função dramática e carga simbólica de cada personagem, mapa de
relações, expressões vernaculares com significado de época, e as ocorrências de
recursos expressivos com citação, localização e interpretação. Peças extensas
podem ser divididas por passos ou cenas.

**Ronda 2 — Tarefa 3.** Numa segunda mensagem, sobre o resultado da primeira, a
análise é convertida em cinco tabelas CSV. Separar *analisar* de *tabelar*
reduz omissões e erros de formato; o texto da peça viaja em cache, pelo que a
segunda leitura é barata.

**Validação.** Cada citação é cotejada com o original; personagens e relações
são confrontadas com o mesmo elenco; o vocabulário de certeza é normalizado; as
frequências são recalculadas. Tudo o que diverge vai para o relatório.

**Tarefa 4 — visualizações.** As tabelas validadas são montadas num único
ficheiro HTML autocontido, sem pedidos de rede: abre offline, viaja por email e
arquiva-se ao lado dos CSVs que o originaram.

## O que sai

```
saidas/<peça>/
├── <peça>-dashboard.html                 abre isto primeiro
├── recursos_expressivos.csv              as cinco tabelas do protocolo
├── frequencias_recursos.csv
├── personagens.csv
├── relacoes.csv
├── vernaculo.csv
├── recursos_expressivos_verificado.csv   + linha e resultado do cotejo
├── validacao.md / validacao.json         erros, avisos e normalizações
├── ronda1.md / ronda2.md                 respostas integrais do modelo
└── execucao.json                         configuração, modelo, tokens, métricas
```

O dashboard traz cartões com os totais e a percentagem de citações verificadas,
uma barra de filtros que actua sobre tudo em simultâneo, a frequência dos
recursos e o vernáculo mais recorrente em barras, um mapa de calor
personagem × tipo de recurso, o grafo de relações e as tabelas integrais com a
coluna de cotejo. Cada gráfico tem vista de tabela equivalente e exportação SVG
para figuras de artigo, e a página respeita o tema claro/escuro e a impressão.

## Começar

```bash
git clone <url> && cd presepios
pip install -r requirements.txt
export ANTHROPIC_API_KEY='sk-ant-...'
```

Antes de gastar um único token, corre o pipeline sobre a amostra sintética que
vem incluída — um entremez fictício com duas citações erradas de propósito, para
veres o cotejo a apanhá-las:

```bash
PYTHONPATH=src python -m presepios reprocessar \
    exemplos/respostas_exemplo -c exemplos/entremez_exemplo.yaml
```

Depois, para uma peça a sério: põe a transcrição em `corpus/transcricoes/`,
copia `config.exemplo.yaml` para `corpus/pecas/<peça>.yaml`, preenche os
metadados — título, datação, proveniência, género — e corre:

```bash
presepios analisar --config corpus/pecas/<peça>.yaml
```

Há mais três comandos: `reprocessar`, que regera tabelas e dashboard a partir de
respostas já gravadas sem voltar a chamar a API; `prompts`, que escreve os
prompts e a transcrição numerada para quem preferir correr o protocolo à mão
numa conversa; e `modelos`, que lista os modelos disponíveis na conta. O guia
completo está em [`docs/utilizacao.md`](docs/utilizacao.md).

## Organização

O repositório divide-se por linguagem e por função.

```
src/presepios/     PYTHON — o pipeline
├── nucleo/            configuração, esquemas das tabelas, orquestração
├── texto/             ler, numerar, detectar, segmentar, normalizar
├── modelo/            os prompts e o cliente da API ← única fronteira com a rede
├── dados/             extrair as tabelas das respostas e validá-las
├── visualizacao/      montar o dashboard a partir de web/
└── cli.py             interface de linha de comandos

web/               NAVEGADOR — o dashboard, separado por linguagem
├── dashboard.html     esqueleto e marcação
├── estilos/           CSS
└── scripts/           JavaScript, um ficheiro por responsabilidade

corpus/            transcrições, configurações e respostas (fora do git)
exemplos/          amostra sintética, para correr o pipeline sem API
testes/            19 testes, sem rede
ferramentas/       scripts de empacotamento
docs/              protocolo, arquitectura e guia de utilização
```

Duas notas sobre esta divisão. A pasta `modelo/` é a **única** parte do pacote
que fala com a rede — tudo o resto trabalha sobre texto e tabelas e pode ser
corrido, testado e depurado sem API. E as fontes de `web/`, embora separadas por
linguagem para serem legíveis e versionáveis, são juntas na geração num **único**
ficheiro HTML: é isso que faz o dashboard abrir offline e arquivar-se com os
dados.

O material de arquivo — transcrições, respostas do modelo, resultados — fica
fora do repositório por omissão. Ver [`corpus/README.md`](corpus/README.md).

## Estado

O pipeline está completo e em uso. A primeira peça analisada foi o **Presépio da
Graça** (Teatro da Calçada da Graça, Lisboa; licenças de 27 de Janeiro de 1779;
transcrição diplomática de 1188 linhas):

| | |
|---|---|
| Ocorrências de recursos expressivos | 145 |
| Personagens | 35 |
| Relações mapeadas | 63 |
| Entradas de vernáculo | 45 |
| **Citações confirmadas no original** | **145 / 145** |

O passo seguinte previsto é a camada comparativa entre peças: o esquema de dados
já é uniforme, falta o agregador e as visualizações que ponham dois presépios
lado a lado.

## O que isto não é

Não é um editor de texto crítico, nem um sistema de transcrição: parte de
transcrições já feitas. Não resolve leituras duvidosas — assinala-as. Não produz
interpretação publicável sem revisão humana, e o cotejo automático confirma que
uma citação existe, não que a leitura que dela se faz esteja certa. E não é
neutro quanto ao custo: cada análise consome tokens de API, ainda que o comando
`reprocessar` permita afinar tudo o resto sem gastar mais nenhum.

## Documentação

- [`docs/protocolo.md`](docs/protocolo.md) — o protocolo de análise, e o que a
  implementação lhe acrescenta. É o que deve ser citado ao descrever o método.
- [`docs/arquitectura.md`](docs/arquitectura.md) — como o código está organizado
  e onde mexer para cada tipo de alteração.
- [`docs/utilizacao.md`](docs/utilizacao.md) — guia completo: convenções de
  transcrição reconhecidas, configuração, comandos, custos.
- [`web/README.md`](web/README.md) — as fontes do dashboard e as regras a que
  obedecem.

## Licença e citação

Distribuído sob a **GPL-3.0-or-later** — ver [`LICENSE`](LICENSE). Qualquer
versão derivada que seja distribuída tem de continuar aberta nas mesmas
condições.

Se este código for usado em trabalho publicado, cita o repositório e indica a
versão utilizada; os ficheiros `execucao.json` gerados registam o modelo, a
configuração e as métricas de cada execução, precisamente para tornar essa
indicação possível.
