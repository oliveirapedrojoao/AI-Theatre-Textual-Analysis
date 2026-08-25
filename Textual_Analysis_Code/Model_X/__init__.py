"""
A fronteira com o modelo de linguagem — o único sítio do pacote que fala com a API.

    prompts.py   o protocolo de análise, repartido pelas duas rondas
    cliente.py   envio, cache do texto da peça, retomas e contagem de tokens

Manter esta fronteira estreita é deliberado: tudo o resto do pipeline trabalha
sobre texto e tabelas, e pode ser corrido, testado e depurado sem rede.
"""

from .prompts import SISTEMA, prompt_ronda1, prompt_ronda2

__all__ = ["SISTEMA", "prompt_ronda1", "prompt_ronda2"]
