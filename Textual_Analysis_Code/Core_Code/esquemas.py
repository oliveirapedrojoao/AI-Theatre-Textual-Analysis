"""Esquemas das tabelas produzidas pela Tarefa 3 — fonte única de verdade.

Este módulo é importado pelos prompts (para pedir as colunas), pelo extractor
(para identificar cada bloco pelo cabeçalho) e pelo validador (para verificar a
conformidade). Alterar um esquema aqui propaga-se a todo o pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Esquema:
    ficheiro: str
    colunas: tuple[str, ...]
    chave: str
    descricao: str
    obrigatorias: tuple[str, ...] = field(default_factory=tuple)

    @property
    def cabecalho(self) -> str:
        return ",".join(self.colunas)


ESQUEMAS: dict[str, Esquema] = {
    "recursos_expressivos": Esquema(
        ficheiro="recursos_expressivos.csv",
        colunas=("id", "tipo_recurso", "citacao", "localizacao", "personagem", "interpretacao"),
        chave="id",
        descricao="uma linha por ocorrência de recurso expressivo",
        obrigatorias=("id", "tipo_recurso", "citacao", "localizacao"),
    ),
    "frequencias_recursos": Esquema(
        ficheiro="frequencias_recursos.csv",
        colunas=("tipo_recurso", "n_ocorrencias"),
        chave="tipo_recurso",
        descricao="contagem por tipo de recurso expressivo",
        obrigatorias=("tipo_recurso", "n_ocorrencias"),
    ),
    "personagens": Esquema(
        ficheiro="personagens.csv",
        colunas=("personagem", "funcao_dramatica", "simbologia"),
        chave="personagem",
        descricao="elenco com função dramática e carga simbólica",
        obrigatorias=("personagem",),
    ),
    "relacoes": Esquema(
        ficheiro="relacoes.csv",
        colunas=("origem", "destino", "tipo_relacao", "descricao"),
        chave="origem",
        descricao="arestas do grafo de relações entre personagens",
        obrigatorias=("origem", "destino", "tipo_relacao"),
    ),
    "vernaculo": Esquema(
        ficheiro="vernaculo.csv",
        colunas=(
            "expressao",
            "significado_epoca",
            "grau_certeza",
            "localizacao",
            "n_ocorrencias",
        ),
        chave="expressao",
        descricao="expressões vernaculares, regionalismos e arcaísmos",
        obrigatorias=("expressao", "significado_epoca", "grau_certeza"),
    ),
}

# Vocabulário controlado ------------------------------------------------------

GRAUS_CERTEZA = ("seguro", "provável", "hipotético")

TIPOS_RECURSO_SUGERIDOS = (
    "metáfora",
    "comparação",
    "parábola",
    "sátira",
    "ironia",
    "hipérbole",
    "antítese",
    "personificação",
    "apóstrofe",
    "anáfora",
    "trocadilho",
    "eufemismo",
    "provérbio",
    "alegoria",
    "aliteração",
    "enumeração",
)

TIPOS_RELACAO_SUGERIDOS = (
    "hierárquica",
    "familiar",
    "antagónica",
    "amorosa",
    "cómica",
    "servil",
    "devocional",
    "aliança",
)


def esquema_por_cabecalho(cabecalho: list[str]) -> str | None:
    """Identifica a tabela a que pertence um cabeçalho CSV lido de uma resposta."""
    normal = [c.strip().lower().lstrip("﻿") for c in cabecalho]
    for nome, esq in ESQUEMAS.items():
        alvo = [c.lower() for c in esq.colunas]
        if normal == alvo:
            return nome
    # tolerância: mesma chave e maioria das colunas presentes
    for nome, esq in ESQUEMAS.items():
        alvo = {c.lower() for c in esq.colunas}
        comuns = alvo & set(normal)
        if esq.chave.lower() in normal and len(comuns) >= max(2, len(alvo) - 1):
            return nome
    return None


def bloco_especificacao() -> str:
    """Descrição das tabelas para embutir no prompt da Tarefa 3."""
    linhas = []
    for nome, esq in ESQUEMAS.items():
        linhas.append(f"- `{esq.ficheiro}` — {esq.descricao}\n  colunas: {esq.cabecalho}")
    return "\n".join(linhas)
