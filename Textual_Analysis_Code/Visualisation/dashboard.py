"""
Montagem do dashboard: junta as fontes de `web/` num único ficheiro HTML.

As fontes do navegador vivem separadas por linguagem — `web/dashboard.html`,
`web/estilos/dashboard.css`, `web/scripts/*.js` — para serem legíveis e
versionáveis como código. O ficheiro entregue, esse, é sempre **um só**: um
HTML autocontido, sem pedidos de rede, que abre offline, viaja por email e pode
ser arquivado ao lado dos CSVs que o originaram.

Os ficheiros de `web/scripts/` são concatenados por ordem alfabética (daí o
prefixo numérico) dentro de um único invólucro, pelo que partilham um escopo:
não são módulos ES e não precisam de importações entre si. O último, por
convenção, é o que arranca a aplicação.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..dados.validacao import Relatorio
from ..nucleo.config import Config

# Candidatos à raiz das fontes do navegador. A pasta `web/` do repositório vem
# primeiro de propósito: em desenvolvimento, e numa instalação editável, é onde
# se está a trabalhar, e uma cópia embutida antiga passaria a mascarar as
# edições em silêncio. A cópia dentro do pacote — feita por
# `ferramentas/sincronizar_web.py` — só entra em jogo quando o repositório não
# está por perto, isto é, numa instalação a partir de wheel.
_CANDIDATOS_WEB = (
    Path(__file__).resolve().parents[3] / "web",
    Path(__file__).parent / "web",
)


def raiz_web() -> Path:
    """Localiza as fontes do navegador."""
    for candidato in _CANDIDATOS_WEB:
        if (candidato / "dashboard.html").exists():
            return candidato
    raise FileNotFoundError(
        "Não encontrei as fontes do dashboard. Esperava `web/dashboard.html` em "
        + " ou ".join(str(c) for c in _CANDIDATOS_WEB)
        + ".\nSe instalaste o pacote, corre `python ferramentas/sincronizar_web.py` "
        "antes de o construir."
    )


def _json_seguro(dados: Any) -> str:
    """JSON para embutir em `<script>` — `<` escapado para não fechar a tag."""
    bruto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    return bruto.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def compor_html(titulo: str, dados: dict[str, Any]) -> str:
    """Inline dos estilos, dos scripts e dos dados no esqueleto HTML."""
    web = raiz_web()
    modelo = (web / "dashboard.html").read_text(encoding="utf-8")

    css = (web / "estilos" / "dashboard.css").read_text(encoding="utf-8")
    estilos = f"<style>\n{css}\n</style>"

    partes = sorted((web / "scripts").glob("*.js"))
    if not partes:
        raise FileNotFoundError(f"Nenhum script encontrado em {web / 'scripts'}")
    corpo = "\n".join(p.read_text(encoding="utf-8") for p in partes)
    scripts = '<script>\n(function(){\n"use strict";\n' + corpo + "\n})();\n</script>"

    return (
        modelo.replace("<!--__ESTILOS__-->", estilos)
        .replace("<!--__SCRIPTS__-->", scripts)
        .replace("__TITULO__", titulo)
        .replace("__DADOS_JSON__", _json_seguro(dados))
    )


def montar_dados(
    cfg: Config,
    tabelas: dict[str, list[dict[str, str]]],
    relatorio: Relatorio,
    seccoes: dict[str, str],
    meta_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Reúne num só objecto tudo o que o dashboard mostra."""
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
    dados = montar_dados(cfg, tabelas, relatorio, seccoes, meta_extra)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(compor_html(cfg.titulo, dados), encoding="utf-8")
    return destino
