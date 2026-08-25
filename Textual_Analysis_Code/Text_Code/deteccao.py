"""Leitura da estrutura da peça: rubricas de fala, marcos de cena e fólios.

O resultado é sempre indicativo — as convenções variam de transcrição para
transcrição e nenhum padrão as apanha todas. Serve de contraprova ao elenco
proposto pela análise, não de verdade sobre o texto."""

from __future__ import annotations

import re

from .normalizacao import normalizar
from .padroes import (
    NAO_PERSONAGENS,
    RE_ESTRUTURA,
    RE_FALAS,
    RE_FALA_INVERTIDA,
    RE_FOLIO,
    RE_VERBO_DIZER,
)


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
