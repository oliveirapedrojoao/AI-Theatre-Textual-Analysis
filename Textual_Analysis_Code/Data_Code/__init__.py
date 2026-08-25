"""
Das respostas do modelo às tabelas verificadas.

    extracao.py    lê as secções e os blocos CSV da resposta
    validacao.py   coteja citações, verifica integridade e recalcula frequências

O cotejo de citações é a verificação decisiva: cada citação é procurada no
texto da transcrição e marcada como verificada, deslocada ou não encontrada.
Nada é corrigido em silêncio — a evidência é assinalada para revisão humana.
"""

from .extracao import extrair_seccoes, extrair_tabelas, gravar_tabelas, ler_tabelas
from .validacao import Relatorio, gravar_verificacao, validar

__all__ = [
    "extrair_seccoes",
    "extrair_tabelas",
    "gravar_tabelas",
    "ler_tabelas",
    "Relatorio",
    "gravar_verificacao",
    "validar",
]
