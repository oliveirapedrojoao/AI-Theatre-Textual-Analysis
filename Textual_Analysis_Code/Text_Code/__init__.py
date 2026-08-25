"""
Tudo o que diz respeito à transcrição antes de a análise começar.

    padroes.py        as convenções de transcrição reconhecidas (regex)
    normalizacao.py   formas canónicas para o cotejo de citações
    deteccao.py       rubricas de fala, marcos de estrutura, fólios
    carregamento.py   leitura, validação e numeração das linhas
    segmentacao.py    divisão de peças extensas por marcos de cena

Nenhum destes módulos altera a ortografia do que é escrito em disco: a
normalização existe apenas em memória, para o cotejo.
"""

from .carregamento import EXTENSOES_ACEITES, Peca, carregar_peca, numerar_linhas
from .deteccao import detectar_estrutura, detectar_folios, detectar_personagens
from .normalizacao import compactar, normalizar
from .segmentacao import Segmento, segmentar

__all__ = [
    "EXTENSOES_ACEITES",
    "Peca",
    "carregar_peca",
    "numerar_linhas",
    "detectar_estrutura",
    "detectar_folios",
    "detectar_personagens",
    "compactar",
    "normalizar",
    "Segmento",
    "segmentar",
]
