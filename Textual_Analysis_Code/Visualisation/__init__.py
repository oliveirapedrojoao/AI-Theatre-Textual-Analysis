"""
Tarefa 4 — as visualizações.

O dashboard é construído **exclusivamente** a partir das tabelas validadas, como
o protocolo exige. Sendo gerado por código e não pelo modelo, é reproduzível: a
mesma peça produz sempre a mesma figura, incluindo a disposição do grafo.

O código do navegador não vive aqui: está em `web/`, separado por linguagem
(HTML, CSS, JS). Este pacote limita-se a juntá-lo num único ficheiro
autocontido, com os dados da peça embutidos.
"""

from .dashboard import gerar_dashboard, montar_dados

__all__ = ["gerar_dashboard", "montar_dados"]
