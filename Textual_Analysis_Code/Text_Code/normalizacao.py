"""
Formas canónicas usadas **apenas** para cotejar citações com o original.

Nada do que aqui se produz é escrito em disco nem substitui a ortografia das
citações: serve só para responder à pergunta «esta citação existe no texto?».
"""

from __future__ import annotations

import re
import unicodedata

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
