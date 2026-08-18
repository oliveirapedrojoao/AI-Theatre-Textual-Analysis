"""
Tarefa 4 — visualizações.

O dashboard é construído **exclusivamente** a partir das tabelas validadas da
Tarefa 3, como o protocolo exige: os gráficos não podem conter nada que não
esteja nos CSVs. Sendo gerado por código e não pelo modelo, é reproduzível — a
mesma peça produz sempre a mesma figura, incluindo a disposição do grafo.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import Config
from .validacao import Relatorio

MODELO = Path(__file__).parent / "recursos" / "dashboard.html"


def _json_seguro(dados: Any) -> str:
    """JSON para embutir em `<script>` — `<` escapado para não fechar a tag."""
    bruto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    return bruto.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def montar_dados(
    cfg: Config,
    tabelas: dict[str, list[dict[str, str]]],
    relatorio: Relatorio,
    seccoes: dict[str, str],
    meta_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    recursos = []
    for r in tabelas.get("recursos_expressivos", []):
        recursos.append(
            {
                "id": r.get("id", ""),
                "tipo_recurso": r.get("tipo_recurso", ""),
                "citacao": r.get("citacao", ""),
                "localizacao": r.get("localizacao", ""),
                "personagem": r.get("personagem", ""),
                "interpretacao": r.get("interpretacao", ""),
                "verificacao": r.get("_verificacao", ""),
                "linha": r.get("_linha_inicio", ""),
            }
        )

    meta = {
        "titulo": cfg.titulo,
        "datacao": cfg.datacao,
        "proveniencia": cfg.proveniencia,
        "genero": cfg.genero,
        "slug": cfg.slug,
        "data_execucao": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    meta.update(meta_extra or {})

    return {
        "meta": meta,
        "metricas": relatorio.metricas,
        "recursos": recursos,
        "personagens": tabelas.get("personagens", []),
        "relacoes": tabelas.get("relacoes", []),
        "vernaculo": tabelas.get("vernaculo", []),
        "frequencias": tabelas.get("frequencias_recursos", []),
        "validacao": relatorio.como_dict(),
        "analise": {
            "personagens": seccoes.get("personagens", ""),
            "vernaculo_recursos": seccoes.get("vernaculo_recursos", ""),
            "limitacoes": seccoes.get("limitacoes", ""),
        },
    }


def gerar_dashboard(
    cfg: Config,
    tabelas: dict[str, list[dict[str, str]]],
    relatorio: Relatorio,
    seccoes: dict[str, str],
    destino: Path,
    meta_extra: dict[str, Any] | None = None,
) -> Path:
    """Escreve um único ficheiro HTML autocontido (sem dependências externas)."""
    if not MODELO.exists():  # pragma: no cover
        raise FileNotFoundError(f"Modelo do dashboard em falta: {MODELO}")
    modelo = MODELO.read_text(encoding="utf-8")
    dados = montar_dados(cfg, tabelas, relatorio, seccoes, meta_extra)
    html = modelo.replace("__TITULO__", cfg.titulo).replace("__DADOS_JSON__", _json_seguro(dados))
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    return destino
