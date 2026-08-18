"""
Carregamento, numeração e segmentação da transcrição.

A numeração de linhas é a peça central da fiabilidade do pipeline: dá ao modelo
um sistema de coordenadas estável para localizar cada citação (`L0042`), e dá ao
validador uma forma determinística de confirmar que a citação existe mesmo no
texto — em vez de confiar na memória do modelo.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

EXTENSOES_ACEITES = {".txt", ".md", ".markdown", ".text"}

# Cabeçalhos de estrutura dramática (grafias setecentistas incluídas). Os autos
# de Natal raramente usam "Cena": organizam-se por "Passos" e por "Vistas"
# (mutações de cenário), pelo que ambos contam como marcos de segmentação.
RE_ESTRUTURA = re.compile(
    r"^\s*(?:"
    r"(?:CENA|SCENA|SENA)\b"
    r"|(?:ACTO|ATO|AUTO)\b"
    r"|(?:JORNADA)\b"
    r"|(?:ENTREMEZ|ENTREMÊS)\b"
    r"|(?:PROLOGO|PRÓLOGO|LOA)\b"
    r"|(?:PASSO|PERCEITO|PRECEITO)\s+(?:DE|DA|DO|DOS|DAS)\b"
    r"|(?:VISTA)\s+(?:DE|DA|DO|DOS|DAS)\b"
    r"|(?:FIM|FINIS)\b"
    r")",
    re.IGNORECASE,
)

# Rubricas de fala. As transcrições usam convenções muito diferentes entre si,
# pelo que se tentam várias, da mais fiável para a mais ambígua.
RE_FALAS = (
    # "Chantre: Pára, vamos…"  ·  "1.º Capitão: Com a espada…"
    re.compile(r"^\s*(?P<n>[0-9A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][^\n:;]{0,34}?)\s*:\s+\S"),
    # "Adão – A tua voz, senhor…"  ·  "Padre Eterno -  Este é o lugar…"
    re.compile(r"^\s*(?P<n>[0-9A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][^\n:;]{0,34}?)\s*[–—]\s+\S"),
    # "BRAZ. Ó compadre Gil…"  (maiúsculas com ponto)
    re.compile(r"^\s*(?P<n>[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][A-ZÁÀÂÃÉÊÍÓÔÕÚÇ\s'’\-]{1,34}?)\s*\.\s+\S"),
    # "\tAlceto\tQue escuto?"  (colunas separadas por tabulação)
    re.compile(r"^[ \t]*(?P<n>[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][^\t\n]{0,30}?)\t+\s*\S"),
)

# Forma invertida: "Fala Eva – De todas nos facultou…", "Fala Adão e diz:"
RE_FALA_INVERTIDA = re.compile(
    r"^\s*(?:Fala|Diz|Recita|Responde)\s+(?:o\s+|a\s+)?"
    r"(?P<n>[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][^\n:;–—\-]{1,28}?)"
    r"\s*(?:e\s+diz)?\s*[:\-–—]\s*",
    re.IGNORECASE,
)

# Verbos de dizer colados à rubrica: "Luzbel diz:", "Padre Eterno fala:"
RE_VERBO_DIZER = re.compile(
    r"[\s,]*(?:fala\s+e\s+diz|canta\s+e\s+diz|fala|diz|canta|reza|responde)\s*$",
    re.IGNORECASE,
)

# Rubricas que são didascália, não personagem.
NAO_PERSONAGENS = {
    "fala", "diz", "fala e diz", "canta", "canta e diz", "sai", "saem", "sahe",
    "sahem", "vai-se", "vao-se", "recolhem-se", "aparece", "aparecem", "vista",
    "pessoas", "interlocutores", "personagens", "figuras", "nota", "soneto",
    "glosa", "decima", "fim", "finis", "passo", "cena", "acto", "jornada",
    "senhora", "senhor", "reza", "rezd", "dentro", "e r", "e r m", "advertencia",
    "continua o coro", "bebe", "vai se", "sao as pensoes da vida",
}

RE_FOLIO = re.compile(
    r"(?:\[\s*f(?:l|ól|ol)?\.?\s*[0-9]{1,4}\s*[vr]?\s*\]"
    r"|^\s*f(?:l|ól|ol)?\.?\s*[0-9]{1,4}\s*[vr]?\s*$)",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass
class Peca:
    """Uma transcrição carregada, pronta para análise."""

    caminho: Path
    linhas: list[str]                       # linhas originais, sem numeração
    texto_bruto: str
    texto_numerado: str
    prefixo: str = "L"
    personagens_detectadas: list[str] = field(default_factory=list)
    marcos_estrutura: list[tuple[int, str]] = field(default_factory=list)
    folios: list[tuple[int, str]] = field(default_factory=list)

    # ------------------------------------------------------------------ meta
    @property
    def n_linhas(self) -> int:
        return len(self.linhas)

    @property
    def n_caracteres(self) -> int:
        return len(self.texto_bruto)

    def tokens_estimados(self) -> int:
        """Estimativa grosseira (~3,5 caracteres por token em português)."""
        return int(self.n_caracteres / 3.5) + 1

    def linha(self, n: int) -> str:
        """Devolve a linha `n` (1-indexada) ou string vazia se fora do intervalo."""
        return self.linhas[n - 1] if 1 <= n <= len(self.linhas) else ""

    def resumo(self) -> str:
        return (
            f"{self.caminho.name}: {self.n_linhas} linhas, "
            f"{self.n_caracteres:,} caracteres, ~{self.tokens_estimados():,} tokens; "
            f"{len(self.personagens_detectadas)} rubricas de fala distintas; "
            f"{len(self.marcos_estrutura)} marcos de estrutura."
        ).replace(",", " ")


# --------------------------------------------------------------------- leitura
def carregar_peca(caminho: str | Path, prefixo: str = "L", numerar: bool = True) -> Peca:
    """Lê a transcrição, valida-a e devolve um objecto `Peca`.

    Levanta erro (em vez de prosseguir em silêncio) se o ficheiro estiver
    ausente, vazio ou ilegível — cumprindo a restrição do protocolo de análise.
    """
    p = Path(caminho).expanduser()
    if not p.exists():
        raise FileNotFoundError(
            f"A transcrição não foi encontrada: {p}\n"
            "O protocolo exige interromper a análise quando o ficheiro está ausente."
        )
    if p.suffix.lower() not in EXTENSOES_ACEITES:
        raise ValueError(
            f"Extensão não suportada: {p.suffix}. "
            f"Formatos aceites: {', '.join(sorted(EXTENSOES_ACEITES))}. "
            "Converte a transcrição para texto simples antes de correr o pipeline."
        )

    dados = p.read_bytes()
    for codec in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            texto = dados.decode(codec)
            break
        except UnicodeDecodeError:
            continue
    else:  # pragma: no cover
        raise ValueError(f"Não foi possível descodificar {p} em nenhum codec conhecido.")

    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    linhas = texto.split("\n")
    while linhas and not linhas[-1].strip():
        linhas.pop()

    if not any(l.strip() for l in linhas):
        raise ValueError(f"A transcrição {p.name} está vazia — nada a analisar.")
    if len("".join(linhas).strip()) < 200:
        raise ValueError(
            f"A transcrição {p.name} tem menos de 200 caracteres úteis. "
            "Verifica se o ficheiro correcto foi indicado."
        )

    peca = Peca(
        caminho=p,
        linhas=linhas,
        texto_bruto="\n".join(linhas),
        texto_numerado="",
        prefixo=prefixo,
    )
    peca.texto_numerado = numerar_linhas(linhas, prefixo) if numerar else peca.texto_bruto
    peca.personagens_detectadas = detectar_personagens(linhas)
    peca.marcos_estrutura = detectar_estrutura(linhas)
    peca.folios = detectar_folios(linhas)
    return peca


def numerar_linhas(linhas: list[str], prefixo: str = "L") -> str:
    """Prefixa cada linha com `[L0001]`, preservando a ortografia original."""
    largura = max(4, len(str(len(linhas))))
    return "\n".join(
        f"[{prefixo}{str(i).zfill(largura)}] {linha}" for i, linha in enumerate(linhas, 1)
    )


# ------------------------------------------------------------------- detecção
def _limpar_rubrica(bruto: str) -> str | None:
    """Normaliza uma rubrica capturada; devolve None se for didascália."""
    nome = re.sub(r"\[[^\]]*\]", " ", bruto)          # "[o Padre Eterno]"
    nome = re.sub(r"\([^)]*\)", " ", nome)            # "(à parte)"
    nome = RE_VERBO_DIZER.sub("", nome)               # "Luzbel diz" → "Luzbel"
    nome = re.sub(r"\s+", " ", nome).strip(" .:,;—–-\t")
    if len(nome) < 2 or nome.isdigit() or len(nome.split()) > 4:
        return None
    if normalizar(nome) in NAO_PERSONAGENS:
        return None
    if not re.search(r"[A-Za-zÀ-ÿ]{2}", nome):
        return None
    return nome


def detectar_personagens(linhas: list[str]) -> list[str]:
    """Lista candidata de personagens a partir das rubricas de fala.

    Serve de contraprova ao elenco proposto pelo modelo: uma personagem presente
    aqui e ausente da análise é sinal de omissão; o inverso, de invenção. É
    deliberadamente indicativa — as convenções de rubrica variam de transcrição
    para transcrição e nenhum padrão as apanha a todas.
    """
    contagem: dict[str, int] = {}
    for linha in linhas:
        if not linha.strip() or RE_ESTRUTURA.match(linha):
            continue
        nome = None
        m = RE_FALA_INVERTIDA.match(linha)
        if m:
            nome = _limpar_rubrica(m.group("n"))
        if nome is None:
            for padrao in RE_FALAS:
                m = padrao.match(linha)
                if m:
                    nome = _limpar_rubrica(m.group("n"))
                    if nome:
                        break
        if nome:
            contagem[nome] = contagem.get(nome, 0) + 1
    # exige duas ocorrências: uma rubrica única é quase sempre ruído de pontuação
    return sorted((n for n, c in contagem.items() if c >= 2), key=lambda s: normalizar(s))


def detectar_estrutura(linhas: list[str]) -> list[tuple[int, str]]:
    """Marcos de estrutura (cenas, actos, jornadas) com a respectiva linha."""
    return [
        (i, linha.strip())
        for i, linha in enumerate(linhas, 1)
        if linha.strip() and RE_ESTRUTURA.match(linha)
    ]


def detectar_folios(linhas: list[str]) -> list[tuple[int, str]]:
    """Marcas de fólio na transcrição: `[fl. 12v]` ou `f. 12` em linha própria."""
    saida = []
    for i, linha in enumerate(linhas, 1):
        for m in RE_FOLIO.finditer(linha):
            saida.append((i, m.group(0).strip()))
    return saida


# ---------------------------------------------------------------- segmentação
@dataclass
class Segmento:
    indice: int
    linha_inicio: int
    linha_fim: int
    texto_numerado: str
    rotulo: str = ""

    @property
    def descricao(self) -> str:
        alcance = f"L{self.linha_inicio:04d}–L{self.linha_fim:04d}"
        return f"Segmento {self.indice} ({alcance}){' · ' + self.rotulo if self.rotulo else ''}"


def segmentar(peca: Peca, max_linhas: int = 900) -> list[Segmento]:
    """Divide a peça em segmentos, cortando preferencialmente em marcos de cena.

    Peças curtas devolvem um único segmento — o pipeline trata os dois casos da
    mesma maneira, pelo que não há caminho de código especial para peças longas.
    """
    total = peca.n_linhas
    if total <= max_linhas:
        return [
            Segmento(1, 1, total, peca.texto_numerado, "peça integral")
        ]

    cortes_possiveis = [n for n, _ in peca.marcos_estrutura]
    segmentos: list[Segmento] = []
    inicio = 1
    idx = 1
    while inicio <= total:
        alvo = inicio + max_linhas - 1
        if alvo >= total:
            fim = total
        else:
            # procura o marco de cena mais próximo do alvo (janela de ±25%)
            janela = max(60, max_linhas // 4)
            candidatos = [c for c in cortes_possiveis if alvo - janela <= c <= alvo + janela]
            fim = (min(candidatos, key=lambda c: abs(c - alvo)) - 1) if candidatos else alvo
            fim = max(fim, inicio + 50)
        rotulo = ""
        for n, texto in peca.marcos_estrutura:
            if inicio <= n <= fim:
                rotulo = texto[:60]
                break
        linhas_seg = peca.texto_numerado.split("\n")[inicio - 1 : fim]
        segmentos.append(Segmento(idx, inicio, fim, "\n".join(linhas_seg), rotulo))
        inicio = fim + 1
        idx += 1
    return segmentos


# ----------------------------------------------------- normalização p/ cotejo
_RE_NAO_ALFANUM = re.compile(r"[^0-9a-z]+")


def normalizar(texto: str) -> str:
    """Forma canónica usada **apenas** para cotejar citações com o original.

    Remove acentuação, pontuação e variação de espaçamento. Nunca é escrita para
    disco nem substitui a ortografia original nas citações — serve só para
    responder à pergunta «esta citação existe mesmo no texto?».
    """
    t = texto.lower()
    t = t.replace("ſ", "s").replace("ʃ", "s")   # s longo das fontes setecentistas
    t = t.replace("[sic]", " ").replace("[SIC]", " ")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = _RE_NAO_ALFANUM.sub(" ", t)
    return " ".join(t.split())


def compactar(texto: str) -> str:
    """`normalizar` sem espaço nenhum — a forma usada para cotejar citações.

    As transcrições diplomáticas conservam as quebras de linha do manuscrito,
    que partem palavras a meio (`a sua mes` / `ma cabeça`). Comparar sem
    espaços torna o cotejo imune a esse artefacto, e também a hifenização, a
    entrelinhas e a diferenças de espaçamento, sem custo prático de falsos
    positivos para fragmentos com mais de uma dúzia de caracteres.
    """
    return normalizar(texto).replace(" ", "")
