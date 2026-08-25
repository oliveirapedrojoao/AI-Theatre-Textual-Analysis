"""Divisão de peças extensas em segmentos, para a primeira ronda de análise.

Os cortes procuram os marcos de estrutura (cena, passo, vista) mais próximos
do tamanho alvo, de modo que nenhum segmento parta uma cena a meio. Peças
curtas devolvem um único segmento: não há caminho de código especial."""

from __future__ import annotations

from dataclasses import dataclass

from .carregamento import Peca


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
