"""
Extracção das secções e das tabelas a partir das respostas do modelo.

O extractor é deliberadamente tolerante: identifica cada bloco CSV pelo
cabeçalho (e não apenas pelo nome anunciado), de modo que uma resposta bem
formada mas com o rótulo trocado não perde dados.
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from ..nucleo.esquemas import ESQUEMAS, esquema_por_cabecalho

RE_SECCAO = re.compile(
    r"<(?P<tag>personagens|vernaculo_recursos|dados|visualizacoes|limitacoes)>"
    r"(?P<corpo>.*?)"
    r"</(?P=tag)>",
    re.DOTALL | re.IGNORECASE,
)

RE_BLOCO = re.compile(
    r"```(?P<lang>[a-zA-Z]*)[^\n]*\n(?P<corpo>.*?)```",
    re.DOTALL,
)


# ------------------------------------------------------------------- secções
def extrair_seccoes(texto: str) -> dict[str, str]:
    """Devolve `{tag: conteúdo}` para todas as secções XML presentes.

    Secções repetidas (ex.: <limitacoes> nas duas rondas) são concatenadas.
    """
    saida: dict[str, str] = {}
    for m in RE_SECCAO.finditer(texto):
        tag = m.group("tag").lower()
        corpo = m.group("corpo").strip()
        saida[tag] = f"{saida[tag]}\n\n{corpo}" if tag in saida else corpo
    return saida


def prosa_sem_blocos(texto: str) -> str:
    """Texto da resposta sem os blocos de código — para o relatório em prosa."""
    return RE_BLOCO.sub("", texto).strip()


# --------------------------------------------------------------------- CSVs
def _linhas_csv(corpo: str) -> list[list[str]]:
    corpo = corpo.strip("\n")
    if not corpo.strip():
        return []
    leitor = csv.reader(io.StringIO(corpo))
    return [linha for linha in leitor if any(c.strip() for c in linha)]


def extrair_tabelas(texto: str) -> tuple[dict[str, list[dict[str, str]]], list[str]]:
    """Extrai as tabelas CSV da resposta.

    Devolve `({nome_tabela: [registos]}, avisos)`. Blocos que não correspondem a
    nenhum esquema conhecido são registados como avisos em vez de silenciados.
    """
    tabelas: dict[str, list[dict[str, str]]] = {}
    avisos: list[str] = []

    for m in RE_BLOCO.finditer(texto):
        corpo = m.group("corpo")
        linhas = _linhas_csv(corpo)
        if len(linhas) < 2:
            continue

        cabecalho = [c.strip() for c in linhas[0]]
        nome = esquema_por_cabecalho(cabecalho)
        if nome is None:
            # segunda hipótese: nome do ficheiro anunciado nas linhas anteriores
            antes = texto[max(0, m.start() - 200) : m.start()]
            for chave, esq in ESQUEMAS.items():
                if esq.ficheiro in antes:
                    nome = chave
                    break
        if nome is None:
            lang = m.group("lang")
            if lang.lower() in ("csv", "") and len(cabecalho) > 1:
                avisos.append(
                    "Bloco CSV não reconhecido (cabeçalho: "
                    + ", ".join(cabecalho[:6])
                    + ") — ignorado."
                )
            continue

        esq = ESQUEMAS[nome]
        registos: list[dict[str, str]] = []
        for linha in linhas[1:]:
            # tolera linhas com mais/menos campos do que o cabeçalho
            if len(linha) < len(cabecalho):
                linha = linha + [""] * (len(cabecalho) - len(linha))
            elif len(linha) > len(cabecalho):
                linha = linha[: len(cabecalho) - 1] + [", ".join(linha[len(cabecalho) - 1 :])]
            registo = {col: (val or "").strip() for col, val in zip(cabecalho, linha)}
            # reordena/completa segundo o esquema canónico
            registos.append({c: registo.get(c, "") for c in esq.colunas})

        if nome in tabelas:
            avisos.append(f"`{esq.ficheiro}` apareceu mais do que uma vez; as linhas foram somadas.")
            tabelas[nome].extend(registos)
        else:
            tabelas[nome] = registos

    for nome, esq in ESQUEMAS.items():
        if nome not in tabelas:
            avisos.append(f"Tabela em falta na resposta: `{esq.ficheiro}`.")
            tabelas[nome] = []

    return tabelas, avisos


# ------------------------------------------------------------------- escrita
def gravar_tabelas(tabelas: dict[str, list[dict[str, str]]], destino: Path) -> dict[str, Path]:
    """Escreve cada tabela em CSV UTF-8 (com BOM, para abrir bem no Excel)."""
    destino.mkdir(parents=True, exist_ok=True)
    caminhos: dict[str, Path] = {}
    for nome, esq in ESQUEMAS.items():
        registos = tabelas.get(nome, [])
        caminho = destino / esq.ficheiro
        with caminho.open("w", encoding="utf-8-sig", newline="") as fh:
            escritor = csv.DictWriter(fh, fieldnames=list(esq.colunas), extrasaction="ignore")
            escritor.writeheader()
            for r in registos:
                escritor.writerow({c: r.get(c, "") for c in esq.colunas})
        caminhos[nome] = caminho
    return caminhos


def ler_tabelas(origem: Path) -> dict[str, list[dict[str, str]]]:
    """Relê as tabelas do disco (permite regerar o dashboard sem chamar a API)."""
    tabelas: dict[str, list[dict[str, str]]] = {}
    for nome, esq in ESQUEMAS.items():
        caminho = origem / esq.ficheiro
        if not caminho.exists():
            tabelas[nome] = []
            continue
        with caminho.open(encoding="utf-8-sig", newline="") as fh:
            tabelas[nome] = [dict(r) for r in csv.DictReader(fh)]
    return tabelas
