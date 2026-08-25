"""
Controlo de qualidade das tabelas.

A verificação decisiva é o **cotejo de citações**: cada `citacao` é procurada no
texto da transcrição, primeiro na vizinhança da localização declarada e depois
na peça inteira. Uma citação que não exista no original é assinalada, não
corrigida — o pipeline não inventa nem apaga evidência, apenas a marca para
revisão humana.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..nucleo.config import Config
from ..nucleo.esquemas import ESQUEMAS, GRAUS_CERTEZA
from ..texto import Peca, compactar, normalizar

RE_REF_LINHA = re.compile(r"\bL\s*0*([0-9]{1,6})\b", re.IGNORECASE)
JANELA_LOCAL = 6          # linhas de tolerância à volta da localização declarada

VERIFICADA = "verificada"
DESLOCADA = "deslocada"
NAO_ENCONTRADA = "não encontrada"
SEM_LOCALIZACAO = "sem localização"


@dataclass
class Relatorio:
    erros: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    notas: list[str] = field(default_factory=list)
    metricas: dict[str, Any] = field(default_factory=dict)

    @property
    def valido(self) -> bool:
        return not self.erros

    def como_dict(self) -> dict[str, Any]:
        return {
            "valido": self.valido,
            "erros": self.erros,
            "avisos": self.avisos,
            "notas": self.notas,
            "metricas": self.metricas,
        }

    def como_markdown(self) -> str:
        def secao(titulo, itens, marca):
            if not itens:
                return ""
            corpo = "\n".join(f"- {marca} {i}" for i in itens)
            return f"\n### {titulo}\n\n{corpo}\n"

        m = self.metricas
        linhas = ["# Relatório de validação\n"]
        linhas.append(
            f"**Estado:** {'conforme' if self.valido else 'com erros'} · "
            f"{m.get('n_recursos', 0)} ocorrências · "
            f"{m.get('n_personagens', 0)} personagens · "
            f"{m.get('n_relacoes', 0)} relações · "
            f"{m.get('n_vernaculo', 0)} entradas de vernáculo\n"
        )
        if "citacoes_verificadas_pct" in m:
            linhas.append(
                f"**Cotejo de citações:** {m['citacoes_verificadas_pct']}% verificadas "
                f"({m.get('citacoes_verificadas', 0)}/{m.get('citacoes_testadas', 0)}), "
                f"{m.get('citacoes_deslocadas', 0)} deslocadas, "
                f"{m.get('citacoes_nao_encontradas', 0)} não encontradas.\n"
            )
        linhas.append(secao("Erros", self.erros, "✗"))
        linhas.append(secao("Avisos", self.avisos, "!"))
        linhas.append(secao("Notas", self.notas, "·"))
        return "".join(linhas)


# ------------------------------------------------------------------ auxiliares
def _refs_linha(localizacao: str) -> list[int]:
    return [int(m.group(1)) for m in RE_REF_LINHA.finditer(localizacao or "")]


def _inteiro(valor: str, omissao: int = 0) -> int:
    try:
        return int(float(str(valor).strip().replace(",", ".")))
    except (TypeError, ValueError):
        return omissao


def _fragmentos(citacao: str, minimo: int) -> list[str]:
    """Parte a citação em fragmentos por reticências, ignorando os curtos."""
    bruto = re.split(r"\.{3}|…|\[\.\.\.\]", citacao or "")
    frags = [compactar(f) for f in bruto]
    frags = [f for f in frags if len(f) >= minimo]
    if not frags:
        inteiro = compactar(citacao or "")
        return [inteiro] if inteiro else []
    return frags


def _normalizar_grau(valor: str) -> str | None:
    v = normalizar(valor)
    for g in GRAUS_CERTEZA:
        if normalizar(g) == v or v.startswith(normalizar(g)[:5]):
            return g
    return None


# ----------------------------------------------------------------- verificação
def verificar_citacao(
    citacao: str, localizacao: str, peca: Peca, texto_norm: str, linhas_norm: list[str], minimo: int
) -> tuple[str, int | None, int | None]:
    """Cotejo de uma citação com o original.

    Devolve `(estado, linha_inicio, linha_fim)`.
    """
    refs = _refs_linha(localizacao)
    inicio = min(refs) if refs else None
    fim = max(refs) if refs else None

    frags = _fragmentos(citacao, minimo)
    if not frags:
        return SEM_LOCALIZACAO, inicio, fim

    if refs:
        lo = max(1, min(refs) - JANELA_LOCAL)
        hi = min(len(linhas_norm), max(refs) + JANELA_LOCAL)
        janela = "".join(linhas_norm[lo - 1 : hi])
        if all(f in janela for f in frags):
            return VERIFICADA, inicio, fim

    if all(f in texto_norm for f in frags):
        return DESLOCADA if refs else SEM_LOCALIZACAO, inicio, fim

    return NAO_ENCONTRADA, inicio, fim


# ------------------------------------------------------------------- validação
def validar(
    tabelas: dict[str, list[dict[str, str]]],
    peca: Peca | None,
    cfg: Config,
    avisos_extraccao: list[str] | None = None,
) -> tuple[dict[str, list[dict[str, str]]], Relatorio]:
    """Valida e normaliza as tabelas. Devolve `(tabelas_corrigidas, relatório)`."""
    rel = Relatorio()
    rel.avisos.extend(avisos_extraccao or [])

    recursos = tabelas.get("recursos_expressivos", [])
    personagens = tabelas.get("personagens", [])
    relacoes = tabelas.get("relacoes", [])
    vernaculo = tabelas.get("vernaculo", [])

    # --- 0. presença mínima ------------------------------------------------
    for nome, esq in ESQUEMAS.items():
        if nome == "frequencias_recursos":
            continue
        if not tabelas.get(nome):
            rel.erros.append(f"`{esq.ficheiro}` está vazia — nada foi sistematizado.")

    # --- 1. campos obrigatórios -------------------------------------------
    for nome, esq in ESQUEMAS.items():
        for i, reg in enumerate(tabelas.get(nome, []), 1):
            em_falta = [c for c in esq.obrigatorias if not (reg.get(c) or "").strip()]
            if em_falta:
                rel.avisos.append(
                    f"`{esq.ficheiro}` linha {i}: campo(s) por preencher — {', '.join(em_falta)}."
                )

    # --- 2. ids únicos e sequenciais --------------------------------------
    ids = [r.get("id", "").strip() for r in recursos]
    repetidos = [k for k, v in Counter(i for i in ids if i).items() if v > 1]
    if repetidos:
        rel.erros.append(
            f"`recursos_expressivos.csv`: ids repetidos — {', '.join(sorted(repetidos)[:10])}."
        )
    for i, reg in enumerate(recursos, 1):
        if not reg.get("id", "").strip():
            reg["id"] = f"R{i:03d}"
            rel.notas.append(f"`recursos_expressivos.csv` linha {i}: id em falta, atribuído `{reg['id']}`.")

    # --- 3. cotejo de citações --------------------------------------------
    estados: dict[str, str] = {}
    if peca is not None and cfg.verificar_citacoes:
        texto_norm = compactar(peca.texto_bruto)
        linhas_norm = [compactar(l) for l in peca.linhas]
        contagem = Counter()
        for reg in recursos:
            estado, ini, fim = verificar_citacao(
                reg.get("citacao", ""),
                reg.get("localizacao", ""),
                peca,
                texto_norm,
                linhas_norm,
                cfg.min_chars_fragmento,
            )
            estados[reg["id"]] = estado
            reg["_linha_inicio"] = str(ini or "")
            reg["_linha_fim"] = str(fim or "")
            reg["_verificacao"] = estado
            contagem[estado] += 1

            refs = _refs_linha(reg.get("localizacao", ""))
            fora = [r for r in refs if r < 1 or r > peca.n_linhas]
            if fora:
                rel.avisos.append(
                    f"`{reg['id']}`: localização {reg.get('localizacao')} aponta para linha(s) "
                    f"inexistente(s) {fora} (a peça tem {peca.n_linhas} linhas)."
                )

        testadas = sum(contagem.values())
        if testadas:
            verificadas = contagem[VERIFICADA]
            rel.metricas.update(
                citacoes_testadas=testadas,
                citacoes_verificadas=verificadas,
                citacoes_deslocadas=contagem[DESLOCADA],
                citacoes_nao_encontradas=contagem[NAO_ENCONTRADA],
                citacoes_sem_localizacao=contagem[SEM_LOCALIZACAO],
                citacoes_verificadas_pct=round(100 * verificadas / testadas, 1),
            )
            if contagem[NAO_ENCONTRADA]:
                nao = [i for i, e in estados.items() if e == NAO_ENCONTRADA]
                rel.erros.append(
                    f"{contagem[NAO_ENCONTRADA]} citação(ões) não foram encontradas na "
                    f"transcrição e exigem revisão manual: {', '.join(nao[:15])}"
                    + (" …" if len(nao) > 15 else "")
                )
            if contagem[DESLOCADA]:
                desl = [i for i, e in estados.items() if e == DESLOCADA]
                rel.avisos.append(
                    f"{contagem[DESLOCADA]} citação(ões) existem no texto mas fora da "
                    f"localização declarada: {', '.join(desl[:15])}"
                    + (" …" if len(desl) > 15 else "")
                )

    # --- 4. integridade referencial ---------------------------------------
    nomes = {(p.get("personagem") or "").strip() for p in personagens}
    nomes.discard("")
    nomes_norm = {normalizar(n): n for n in nomes}

    def resolver(nome: str) -> str | None:
        n = (nome or "").strip()
        if not n or n in nomes:
            return n or None
        return nomes_norm.get(normalizar(n))

    for reg in recursos:
        p = (reg.get("personagem") or "").strip()
        if not p or p.startswith("("):
            continue
        alvo = resolver(p)
        if alvo is None:
            rel.avisos.append(
                f"`{reg['id']}`: personagem «{p}» não consta de `personagens.csv`."
            )
        elif alvo != p:
            reg["personagem"] = alvo
            rel.notas.append(f"`{reg['id']}`: personagem «{p}» harmonizada para «{alvo}».")

    for i, reg in enumerate(relacoes, 1):
        for campo in ("origem", "destino"):
            v = (reg.get(campo) or "").strip()
            alvo = resolver(v)
            if alvo is None:
                rel.avisos.append(
                    f"`relacoes.csv` linha {i}: «{v}» ({campo}) não consta de `personagens.csv`."
                )
            elif alvo != v:
                reg[campo] = alvo
                rel.notas.append(f"`relacoes.csv` linha {i}: «{v}» harmonizado para «{alvo}».")
        if (reg.get("origem") or "").strip() == (reg.get("destino") or "").strip():
            rel.avisos.append(f"`relacoes.csv` linha {i}: relação de uma personagem consigo mesma.")

    duplicadas = Counter(
        (r.get("origem", ""), r.get("destino", ""), r.get("tipo_relacao", "")) for r in relacoes
    )
    for chave, n in duplicadas.items():
        if n > 1 and all(chave):
            rel.avisos.append(f"`relacoes.csv`: aresta repetida {chave[0]} → {chave[1]} ({chave[2]}) ×{n}.")

    # --- 5. cobertura do elenco -------------------------------------------
    if peca is not None and peca.personagens_detectadas:
        detectadas_norm = {normalizar(p): p for p in peca.personagens_detectadas}
        em_falta = [
            orig for k, orig in detectadas_norm.items()
            if k not in nomes_norm and not any(k in n or n in k for n in nomes_norm)
        ]
        if em_falta:
            rel.avisos.append(
                "Rubricas de fala presentes na transcrição mas ausentes de "
                f"`personagens.csv`: {', '.join(sorted(em_falta))}. "
                "Podem ser variantes de grafia ou omissões da análise."
            )

    # --- 6. vocabulário controlado ----------------------------------------
    for i, reg in enumerate(vernaculo, 1):
        g = _normalizar_grau(reg.get("grau_certeza", ""))
        if g is None:
            rel.avisos.append(
                f"`vernaculo.csv` linha {i}: grau de certeza «{reg.get('grau_certeza')}» "
                f"fora do vocabulário ({'/'.join(GRAUS_CERTEZA)}); classificado como hipotético."
            )
            reg["grau_certeza"] = "hipotético"
        else:
            reg["grau_certeza"] = g
        reg["n_ocorrencias"] = str(max(1, _inteiro(reg.get("n_ocorrencias"), 1)))

    for reg in recursos:
        reg["tipo_recurso"] = (reg.get("tipo_recurso") or "").strip().lower()

    # --- 7. frequências recalculadas --------------------------------------
    contagem_real = Counter(r["tipo_recurso"] for r in recursos if r.get("tipo_recurso"))
    declarada = {
        (r.get("tipo_recurso") or "").strip().lower(): _inteiro(r.get("n_ocorrencias"))
        for r in tabelas.get("frequencias_recursos", [])
    }
    divergentes = [
        f"{t}: declarado {declarada.get(t, 0)}, real {n}"
        for t, n in contagem_real.items()
        if declarada.get(t, 0) != n
    ]
    extra_declarados = [t for t in declarada if t and t not in contagem_real]
    if divergentes or extra_declarados:
        detalhe = "; ".join(divergentes[:8])
        if extra_declarados:
            detalhe += f"; tipos declarados sem ocorrências: {', '.join(extra_declarados[:8])}"
        rel.notas.append(
            "`frequencias_recursos.csv` foi recalculada a partir de "
            f"`recursos_expressivos.csv` ({detalhe})."
        )
    tabelas["frequencias_recursos"] = [
        {"tipo_recurso": t, "n_ocorrencias": str(n)}
        for t, n in sorted(contagem_real.items(), key=lambda kv: (-kv[1], kv[0]))
    ]

    # --- 8. métricas -------------------------------------------------------
    rel.metricas.update(
        n_recursos=len(recursos),
        n_tipos_recurso=len(contagem_real),
        n_personagens=len(personagens),
        n_relacoes=len(relacoes),
        n_vernaculo=len(vernaculo),
        n_tipos_relacao=len({(r.get("tipo_relacao") or "").strip().lower() for r in relacoes} - {""}),
    )
    if peca is not None:
        rel.metricas["n_linhas_peca"] = peca.n_linhas
        rel.metricas["densidade_recursos_por_100_linhas"] = (
            round(100 * len(recursos) / peca.n_linhas, 2) if peca.n_linhas else 0
        )

    return tabelas, rel


def gravar_verificacao(recursos: list[dict[str, str]], destino: Path) -> Path | None:
    """Grava `recursos_expressivos_verificado.csv` com o resultado do cotejo."""
    if not recursos or "_verificacao" not in recursos[0]:
        return None
    caminho = destino / "recursos_expressivos_verificado.csv"
    colunas = list(ESQUEMAS["recursos_expressivos"].colunas) + [
        "linha_inicio",
        "linha_fim",
        "citacao_verificada",
    ]
    with caminho.open("w", encoding="utf-8-sig", newline="") as fh:
        escritor = csv.DictWriter(fh, fieldnames=colunas)
        escritor.writeheader()
        for r in recursos:
            linha = {c: r.get(c, "") for c in ESQUEMAS["recursos_expressivos"].colunas}
            linha["linha_inicio"] = r.get("_linha_inicio", "")
            linha["linha_fim"] = r.get("_linha_fim", "")
            linha["citacao_verificada"] = r.get("_verificacao", "")
            escritor.writerow(linha)
    return caminho
