"""Orquestração: da transcrição ao dashboard, num só percurso."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Config
from ..visualizacao.dashboard import gerar_dashboard
from ..dados.extracao import extrair_seccoes, extrair_tabelas, gravar_tabelas
from ..texto import carregar_peca
from ..dados.validacao import Relatorio, gravar_verificacao, validar


@dataclass
class Saida:
    directorio: Path
    dashboard: Path
    csvs: dict[str, Path]
    relatorio: Relatorio
    ficheiros: list[Path]


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def correr(
    cfg: Config,
    reutilizar: Path | None = None,
    apenas_dashboard: bool = False,
    verboso: bool = True,
) -> Saida:
    """Executa o pipeline completo.

    `reutilizar` aponta para um directório com `ronda1.md`/`ronda2.md` já
    gravados: reprocessa-os sem voltar a chamar a API — útil para afinar a
    validação ou o dashboard sem custo, e para reproduzir resultados.
    """
    if not cfg.peca:
        raise ValueError("Falta indicar a transcrição (`peca:` na configuração ou argumento posicional).")

    peca = carregar_peca(cfg.peca, cfg.prefixo_linha, cfg.numerar_linhas)
    if verboso:
        _log(f"» {peca.resumo()}")

    destino = cfg.dir_saida / cfg.slug
    destino.mkdir(parents=True, exist_ok=True)

    modelo_usado = "(reutilizado)"
    uso: dict[str, Any] = {}

    if reutilizar is not None:
        r1 = (reutilizar / "ronda1.md")
        r2 = (reutilizar / "ronda2.md")
        if not r1.exists() or not r2.exists():
            raise FileNotFoundError(
                f"Esperava `ronda1.md` e `ronda2.md` em {reutilizar}; "
                "corre primeiro o pipeline completo."
            )
        texto_r1, texto_r2 = r1.read_text("utf-8"), r2.read_text("utf-8")
        meta_anterior = reutilizar / "execucao.json"
        if meta_anterior.exists():
            try:
                modelo_usado = json.loads(meta_anterior.read_text("utf-8")).get("modelo", modelo_usado)
            except json.JSONDecodeError:
                pass
    else:
        from ..modelo.cliente import Analisador  # tardia: só aqui é preciso o SDK

        analisador = Analisador(cfg, verboso=verboso)
        resultado = analisador.analisar(peca)
        if resultado.interrompido:
            (destino / "ronda1.md").write_text(resultado.ronda1, encoding="utf-8")
            raise RuntimeError(resultado.motivo_interrupcao + f"\nResposta em {destino/'ronda1.md'}")
        texto_r1, texto_r2 = resultado.ronda1, resultado.ronda2
        modelo_usado = resultado.modelo
        uso = resultado.uso.como_dict(cfg)
        (destino / "ronda1.md").write_text(texto_r1, encoding="utf-8")
        (destino / "ronda2.md").write_text(texto_r2, encoding="utf-8")

    # --- extracção ---------------------------------------------------------
    seccoes = extrair_seccoes(texto_r1)
    seccoes_r2 = extrair_seccoes(texto_r2)
    if seccoes_r2.get("limitacoes"):
        seccoes["limitacoes"] = (
            (seccoes.get("limitacoes", "") + "\n\n" + seccoes_r2["limitacoes"]).strip()
        )
    tabelas, avisos = extrair_tabelas(texto_r2)
    if not any(tabelas.values()):
        # a Tarefa 3 pode ter sido respondida dentro da Ronda 1 em execuções manuais
        tabelas, avisos_extra = extrair_tabelas(texto_r1)
        avisos += avisos_extra

    # --- validação ---------------------------------------------------------
    tabelas, relatorio = validar(tabelas, peca, cfg, avisos)
    if verboso:
        m = relatorio.metricas
        _log(
            f"» {m.get('n_recursos',0)} ocorrências · {m.get('n_personagens',0)} personagens · "
            f"{m.get('n_relacoes',0)} relações · {m.get('n_vernaculo',0)} termos"
        )
        if "citacoes_verificadas_pct" in m:
            _log(f"» cotejo de citações: {m['citacoes_verificadas_pct']}% verificadas")
        for e in relatorio.erros:
            _log(f"  ✗ {e}")
        for a in relatorio.avisos[:12]:
            _log(f"  ! {a}")
        if len(relatorio.avisos) > 12:
            _log(f"  ! (+{len(relatorio.avisos)-12} avisos no relatório de validação)")

    # --- gravação ----------------------------------------------------------
    caminhos = gravar_tabelas(tabelas, destino)
    ficheiros = list(caminhos.values())
    verif = gravar_verificacao(tabelas.get("recursos_expressivos", []), destino)
    if verif:
        ficheiros.append(verif)

    (destino / "validacao.json").write_text(
        json.dumps(relatorio.como_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (destino / "validacao.md").write_text(relatorio.como_markdown(), encoding="utf-8")
    ficheiros += [destino / "validacao.json", destino / "validacao.md"]

    execucao = {
        "titulo": cfg.titulo,
        "peca": str(peca.caminho),
        "modelo": modelo_usado,
        "config": cfg.como_dict(),
        "uso": uso,
        "metricas": relatorio.metricas,
    }
    (destino / "execucao.json").write_text(
        json.dumps(execucao, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ficheiros.append(destino / "execucao.json")

    # --- dashboard ---------------------------------------------------------
    html = gerar_dashboard(
        cfg,
        tabelas,
        relatorio,
        seccoes,
        destino / f"{cfg.slug}-dashboard.html",
        meta_extra={
            "modelo": modelo_usado,
            "ficheiro": peca.caminho.name,
            "n_linhas": peca.n_linhas,
        },
    )
    ficheiros.append(html)

    if uso and verboso:
        _log(f"» tokens: {uso}")
    if verboso:
        _log(f"» dashboard: {html}")

    return Saida(destino, html, caminhos, relatorio, ficheiros)
