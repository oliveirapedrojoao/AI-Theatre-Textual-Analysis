"""Carregamento e numeração da transcrição.

A numeração de linhas é a peça central da fiabilidade do pipeline: dá ao
modelo um sistema de coordenadas estável para localizar cada citação
(`L0042`), e dá ao validador uma forma determinística de confirmar que a
citação existe mesmo no texto — em vez de confiar na memória do modelo."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .deteccao import detectar_estrutura, detectar_folios, detectar_personagens
from .padroes import EXTENSOES_ACEITES


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
