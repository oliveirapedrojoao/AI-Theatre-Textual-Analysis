# O protocolo de análise

Este é o protocolo que o pipeline executa. Está aqui em texto corrido, e não só
disperso pelo código, por duas razões: é a especificação a que o código
responde, e é o que deve ser citado quando se descreve o método num artigo.

A implementação encontra-se em `src/presepios/modelo/prompts.py` (as duas
rondas), `src/presepios/nucleo/esquemas.py` (as tabelas) e
`src/presepios/dados/validacao.py` (as verificações).

## Papel

Historiador do teatro e filólogo especializado em literatura dramática
portuguesa do século XVIII, com domínio de retórica clássica, lexicografia
histórica coeva (Bluteau, *Vocabulario Portuguez e Latino*, 1712–1728; Morais
Silva, *Diccionario da Lingua Portugueza*, 1789) e crítica textual.

## Contexto

A peça é transmitida na íntegra, acompanhada dos metadados que a situam:
título, datação, proveniência (fundo e cota) e género. A interpretação deve ser
rigorosa, activa e historicamente situada: considerar a fluidez semântica, as
variações ortográficas e lexicais, o vernáculo e as expressões locais e
regionais correntes à data da composição. Não aplicar acepções modernas de forma
anacrónica; sempre que o sentido de época divergir do actual, assinalar
explicitamente a divergência.

## Metodologia

Ler a peça integralmente e planear a análise antes de redigir. Fundamentar cada
afirmação interpretativa em evidência textual, com citação exacta e localização.
Distinguir constatação textual de inferência interpretativa e declarar o grau de
certeza de cada leitura: **seguro / provável / hipotético**.

## Tarefas

### 1. Simbologia das personagens e relações

a) Elencar todas as personagens da peça.
b) Para cada uma: função dramática, carga simbólica (social, religiosa, moral,
cómica) e evidência textual de suporte.
c) Mapear as relações entre personagens, classificando o tipo (hierárquica,
familiar, antagónica, amorosa, cómica, servil, etc.) e interpretando o seu
significado no contexto da peça.

### 2. Vernáculo e recursos expressivos

a) Identificar expressões vernaculares, regionalismos e arcaísmos; propor o
significado de época com grau de certeza e, quando possível, apoio
lexicográfico coevo.
b) Identificar e classificar os recursos expressivos: metáfora, comparação,
parábola, sátira, ironia, hipérbole, antítese, e outros que se reconheçam.
c) Para cada ocorrência registar: citação exacta (ortografia original, `[sic]`
quando necessário), localização, tipo de recurso, personagem enunciadora e
interpretação do efeito produzido.

### 3. Sistematização dos dados

Converter os resultados das Tarefas 1–2 em cinco tabelas CSV:

| Ficheiro | Colunas |
|---|---|
| `recursos_expressivos.csv` | id, tipo_recurso, citacao, localizacao, personagem, interpretacao |
| `frequencias_recursos.csv` | tipo_recurso, n_ocorrencias |
| `personagens.csv` | personagem, funcao_dramatica, simbologia |
| `relacoes.csv` | origem, destino, tipo_relacao, descricao |
| `vernaculo.csv` | expressao, significado_epoca, grau_certeza, localizacao, n_ocorrencias |

### 4. Visualizações

Com base **exclusivamente** nas tabelas da Tarefa 3:

a) Gráfico de barras — frequência de cada tipo de recurso expressivo.
b) Mapa de calor — distribuição dos recursos expressivos por personagem.
c) Grafo de rede — personagens como nós, relações como arestas rotuladas pelo tipo.

## Formato de saída

```
<personagens>…</personagens>
<vernaculo_recursos>…</vernaculo_recursos>
<dados>…</dados>
<visualizacoes>…</visualizacoes>
<limitacoes>lacunas, passagens ilegíveis, leituras alternativas</limitacoes>
```

## Restrições

- Não conjecturar em silêncio sobre passagens lacunares ou ilegíveis: registá-las
  em `<limitacoes>`.
- Não normalizar a ortografia nas citações.
- Se o ficheiro estiver ausente ou ilegível, interromper e comunicá-lo antes de
  prosseguir com qualquer análise.

---

## O que a implementação acrescenta ao protocolo

O código não se limita a enviar este texto. Quatro decisões de execução afastam-no
do protocolo tal como foi formulado, e todas se justificam por fiabilidade.

**Encadeamento em duas rondas.** As Tarefas 1–2 correm numa mensagem e a Tarefa 3
noutra, sobre o resultado da primeira. A recomendação já estava no protocolo para
peças extensas; o pipeline aplica-a sempre, porque separar *analisar* de *tabelar*
reduz omissões e erros de formato. O texto da peça segue em bloco com
`cache_control`, pelo que a segunda ronda o relê a preço de cache.

**Numeração de linhas.** A transcrição é enviada com cada linha prefixada por
`[L0042]`, e a coluna `localizacao` passa a exigir esses marcadores. É o que
torna cada citação verificável — sem um sistema de coordenadas estável não há
cotejo possível.

**A Tarefa 4 é feita por código, não pelo modelo.** As visualizações são geradas
a partir dos CSVs já validados. Assim, nenhum gráfico pode mostrar algo que não
esteja nas tabelas — que é a condição que o próprio protocolo impõe — e o
resultado é reproduzível: a disposição do grafo usa semente fixa.

**Uma camada de validação que o protocolo não previa.** Antes de qualquer
visualização, o pipeline coteja cada citação com a transcrição (verificada /
deslocada / não encontrada), confirma que personagens e relações se referem ao
mesmo elenco, normaliza o vocabulário de grau de certeza e recalcula as
frequências a partir das ocorrências reais. Nada é corrigido em silêncio: as
divergências vão para `validacao.md`.

## Utilização manual

O protocolo continua a poder ser corrido à mão, numa conversa. O comando

```bash
presepios prompts corpus/transcricoes/peça.txt -c corpus/pecas/peça.yaml
```

escreve `sistema.txt`, `ronda1.txt`, `ronda2.txt` e `peca_numerada.txt`. Guardando
as respostas como `ronda1.md` e `ronda2.md` numa pasta, `presepios reprocessar`
faz o resto — validação, tabelas e dashboard — sem chamar a API.
