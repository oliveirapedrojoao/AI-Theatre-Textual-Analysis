"""
Os prompts das duas rondas.

A divisão segue a recomendação do protocolo original: *prompt chaining* preserva
qualidade analítica e contexto em peças extensas.

  Ronda 1 — Tarefas 1 e 2 (análise: personagens, relações, vernáculo, recursos)
  Ronda 2 — Tarefa 3 (sistematização em CSV, sobre os resultados da Ronda 1)
  Tarefa 4 — as visualizações são geradas por código, a partir dos CSVs, e não
             pelo modelo: garante que os gráficos derivam *exclusivamente* das
             tabelas, como o protocolo exige, e torna-os reproduzíveis.
"""

from __future__ import annotations

from .config import Config
from .esquemas import (
    ESQUEMAS,
    GRAUS_CERTEZA,
    TIPOS_RECURSO_SUGERIDOS,
    TIPOS_RELACAO_SUGERIDOS,
    bloco_especificacao,
)

# ---------------------------------------------------------------------- PAPEL
SISTEMA = """\
# PAPEL
És um historiador do teatro e filólogo especializado em literatura dramática
portuguesa do século XVIII, com domínio de retórica clássica, lexicografia
histórica coeva (Bluteau, Vocabulario Portuguez e Latino, 1712–1728; Morais
Silva, Diccionario da Lingua Portugueza, 1789) e crítica textual.

# METODOLOGIA
Antes de redigir a resposta, lê a peça integralmente e planeia a análise.
Fundamenta cada afirmação interpretativa em evidência textual, com citação
exata e localização. Distingue constatação textual de inferência interpretativa
e declara o grau de certeza de cada leitura (seguro / provável / hipotético).

A interpretação deve ser rigorosa, ativa e historicamente situada: considera a
fluidez semântica, as variações ortográficas e lexicais, o vernáculo e as
expressões locais e regionais correntes à data da composição. Não apliques
aceções modernas de forma anacrónica; sempre que o sentido de época divergir do
atual, assinala explicitamente a divergência.

# SISTEMA DE LOCALIZAÇÃO
A transcrição é fornecida com cada linha prefixada por um marcador `[L0001]`.
Toda a localização deve usar esses marcadores: `L0042` para uma linha, ou
`L0042-L0047` para um intervalo. Quando a transcrição contiver indicações de
cena ou de fólio, acrescenta-as depois do marcador, separadas por `;`
(ex.: `L0042; Cena II; fl. 7v`). Nunca inventes um marcador: se não conseguires
localizar uma passagem, escreve `L?` e regista o caso em <limitacoes>.

# RESTRIÇÕES
- Não conjetures silenciosamente sobre passagens lacunares ou ilegíveis:
  regista-as em <limitacoes>.
- Não normalizes a ortografia nas citações. Reproduz o texto exatamente como
  surge na transcrição, incluindo grafias antigas, e usa [sic] apenas quando a
  forma puder ser tomada por erro de transcrição.
- Copia as citações caractere a caractere da transcrição fornecida: são
  cotejadas automaticamente com o original e uma citação que não exista no texto
  invalida a entrada.
- Se a transcrição estiver ausente, truncada ou ilegível, interrompe e comunica-o
  antes de prosseguir com qualquer análise.
"""


def _bloco_contexto(cfg: Config, resumo_peca: str, personagens_detectadas: list[str]) -> str:
    detectadas = ", ".join(personagens_detectadas) if personagens_detectadas else "(nenhuma detectada automaticamente)"
    extra = f"\n- Notas: {cfg.notas_contexto}" if cfg.notas_contexto.strip() else ""
    return f"""\
# CONTEXTO
A peça em análise é transmitida na íntegra a seguir.
- Título: {cfg.titulo}
- Datação: {cfg.datacao}
- Proveniência: {cfg.proveniencia}
- Género: {cfg.genero}{extra}
- Dimensão da transcrição: {resumo_peca}

Rubricas de fala detectadas automaticamente (indicativo, pode conter ruído ou
omissões — confirma pela leitura): {detectadas}
"""


# -------------------------------------------------------------------- RONDA 1
def prompt_ronda1(
    cfg: Config,
    resumo_peca: str,
    personagens_detectadas: list[str],
    rotulo_segmento: str = "",
) -> str:
    escopo = ""
    if rotulo_segmento:
        escopo = f"""
# ÂMBITO DESTA MENSAGEM
Estás a analisar **{rotulo_segmento}** de uma peça extensa, dividida para
preservar a qualidade analítica. Analisa exaustivamente o segmento fornecido.
Se uma personagem ou fio dramático vier claramente de fora do segmento,
assinala-o em <limitacoes> em vez de o reconstruir por conjectura.
"""

    return f"""{_bloco_contexto(cfg, resumo_peca, personagens_detectadas)}{escopo}
# TAREFAS — executa sequencialmente

## 1. Simbologia das personagens e relações
a) Elenca todas as personagens da peça.
b) Para cada personagem: função dramática, carga simbólica (social, religiosa,
   moral, cómica) e evidência textual de suporte.
c) Mapeia as relações entre personagens, classificando o tipo (hierárquica,
   familiar, antagónica, amorosa, cómica, servil, etc.) e interpretando o seu
   significado no contexto da peça.

## 2. Vernáculo e recursos expressivos
a) Identifica expressões vernaculares, regionalismos e arcaísmos; propõe o
   significado de época com grau de certeza e, quando possível, apoio
   lexicográfico coevo (indica a fonte: Bluteau, Morais Silva, ou outra).
b) Identifica e classifica os recursos expressivos: metáfora, comparação,
   parábola, sátira, ironia, hipérbole, antítese, e outros que reconheças.
c) Para cada ocorrência regista: citação exata (ortografia original, [sic]
   quando necessário), localização, tipo de recurso, personagem enunciadora e
   interpretação do efeito produzido.

Sê exaustivo: percorre a peça do princípio ao fim e não te limites aos exemplos
mais salientes. Uma ocorrência não registada aqui não existirá nas tabelas nem
nos gráficos da fase seguinte.

# FORMATO DE SAÍDA
Organiza a resposta exatamente nestas secções:
<personagens>
elenco, função dramática, carga simbólica com evidência textual, e o mapa de
relações entre personagens
</personagens>
<vernaculo_recursos>
expressões vernaculares com significado de época e grau de certeza; ocorrências
de recursos expressivos com citação, localização, personagem e interpretação
</vernaculo_recursos>
<limitacoes>
lacunas, passagens ilegíveis, leituras alternativas, localizações incertas
</limitacoes>
"""


# -------------------------------------------------------------------- RONDA 2
def prompt_ronda2(cfg: Config, analise_previa: str | None = None) -> str:
    graus = " / ".join(GRAUS_CERTEZA)
    recursos = ", ".join(TIPOS_RECURSO_SUGERIDOS)
    relacoes = ", ".join(TIPOS_RELACAO_SUGERIDOS)

    bloco_previo = ""
    if analise_previa:
        bloco_previo = f"""
# ANÁLISE DA RONDA 1
A peça foi analisada por segmentos. Segue a análise completa produzida na ronda
anterior; consolida-a numa única série de tabelas, fundindo entradas duplicadas
da mesma personagem ou da mesma expressão e somando as respectivas ocorrências.

<analise_ronda1>
{analise_previa}
</analise_ronda1>
"""

    exemplos = "\n\n".join(
        f"#### {esq.ficheiro}\n```csv\n{esq.cabecalho}\n…\n```"
        for esq in ESQUEMAS.values()
    )

    return f"""{bloco_previo}
# TAREFA 3 — Sistematização dos dados

Converte **integralmente** os resultados das Tarefas 1–2 em tabelas CSV, prontas
para visualização e reutilização. Nenhuma ocorrência identificada na análise
pode ficar de fora, e nenhuma entrada nova pode ser introduzida aqui: esta
tarefa é de conversão, não de nova análise.

## Tabelas a produzir
{bloco_especificacao()}

## Formato obrigatório
Devolve as cinco tabelas por esta ordem, cada uma precedida do seu nome em
cabeçalho de nível 4 e contida num bloco de código marcado `csv`:

{exemplos}

## Regras de formatação do CSV
- A primeira linha de cada bloco é o cabeçalho, exatamente com os nomes de
  coluna indicados, em minúsculas, separados por vírgula, sem espaços.
- Delimitador: vírgula. Envolve em aspas duplas qualquer campo que contenha
  vírgula, aspas, ponto e vírgula ou quebra de linha; duplica as aspas internas
  (uma aspa dentro de um campo escreve-se com duas aspas seguidas).
- Nunca uses quebras de linha dentro de um campo: substitui-as por ` / `.
- Não normalizes a ortografia na coluna `citacao`: mantém a grafia original.
- `id` em `recursos_expressivos.csv`: `R001`, `R002`, … sequencial e único.
- `localizacao`: marcador de linha (`L0042` ou `L0042-L0047`), seguido de cena
  ou fólio quando existirem, separados por `;`.
- `personagem` em `recursos_expressivos.csv` e `origem`/`destino` em
  `relacoes.csv` devem usar **exatamente** as mesmas grafias da coluna
  `personagem` de `personagens.csv`. Se o enunciador for uma didascália ou
  narrador, escreve `(didascália)`.
- `tipo_recurso`: substantivo singular em minúsculas. Vocabulário de referência
  (podes acrescentar outros se o texto o justificar): {recursos}.
- `tipo_relacao`: minúsculas. Vocabulário de referência: {relacoes}.
- `grau_certeza`: exatamente um de {graus}.
- `n_ocorrencias` e as contagens de `frequencias_recursos.csv` são inteiros;
  `frequencias_recursos.csv` deve ser a contagem exata das linhas de
  `recursos_expressivos.csv` por `tipo_recurso`.
- `relacoes.csv`: uma linha por par ordenado de personagens com relação
  relevante. Relações recíprocas de tipo diferente (ex.: senhor→criado servil,
  criado→senhor cómica) justificam duas linhas.

Depois das cinco tabelas, e só depois, acrescenta:
<limitacoes>
entradas que não foi possível sistematizar, localizações incertas, decisões de
consolidação tomadas ao fundir duplicados
</limitacoes>

Não produzas gráficos nem código de visualização: as visualizações são geradas
automaticamente a partir destas tabelas.
"""


def prompt_ronda1_continuacao() -> str:
    """Pedido de continuação quando a resposta é truncada por limite de tokens."""
    return (
        "A tua resposta foi interrompida por limite de comprimento. Continua "
        "exatamente do ponto onde paraste, sem repetir o que já escreveste e sem "
        "reabrir secções já fechadas. Se estavas a meio de uma linha, retoma-a."
    )
