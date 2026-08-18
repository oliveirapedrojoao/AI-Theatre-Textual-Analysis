"""Configuração do pipeline: metadados da peça + parâmetros de execução."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


@dataclass
class Config:
    # --- Metadados da peça (preenchem o bloco CONTEXTO do prompt) -----------
    titulo: str = "[TÍTULO DA PEÇA]"
    datacao: str = "[DATA OU PERÍODO ESTIMADO]"
    proveniencia: str = "[FUNDO/COTA]"
    genero: str = "presépio teatral"
    notas_contexto: str = ""          # texto livre acrescentado ao CONTEXTO

    # --- Ficheiros ----------------------------------------------------------
    peca: str = ""                    # caminho da transcrição .txt/.md
    saida: str = "saidas"             # directório de saída

    # --- Modelo -------------------------------------------------------------
    modelo: str = "auto"              # "auto" = escolhe o Opus mais recente
    max_tokens_ronda1: int = 32000
    max_tokens_ronda2: int = 32000
    pensamento_ronda1: int = 10000    # orçamento de extended thinking (0 = off)
    pensamento_ronda2: int = 6000
    tentativas: int = 4               # retries com backoff exponencial

    # --- Segmentação de peças extensas -------------------------------------
    segmentar: bool = False
    max_linhas_segmento: int = 900

    # --- Numeração das linhas ----------------------------------------------
    numerar_linhas: bool = True
    prefixo_linha: str = "L"

    # --- Validação ----------------------------------------------------------
    verificar_citacoes: bool = True
    min_chars_fragmento: int = 12     # fragmento mínimo para dar match

    # --- Custos (opcional; confirmar preços correntes na documentação) ------
    # Valores em USD por milhão de tokens. Deixar a None para reportar apenas
    # contagens de tokens, sem estimativa de custo.
    preco_input: float | None = None
    preco_output: float | None = None
    preco_cache_escrita: float | None = None
    preco_cache_leitura: float | None = None

    # --- Interno ------------------------------------------------------------
    extra: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------ util
    @property
    def dir_saida(self) -> Path:
        return Path(self.saida).expanduser()

    @property
    def slug(self) -> str:
        """Identificador seguro para nomes de ficheiro, derivado do título."""
        import re
        import unicodedata

        base = unicodedata.normalize("NFKD", self.titulo)
        base = "".join(c for c in base if not unicodedata.combining(c))
        base = re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-").lower()
        return base or "peca"

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)


def carregar_config(caminho: str | os.PathLike | None = None, **sobreposicoes) -> Config:
    """Lê um YAML de configuração e aplica sobreposições da linha de comandos."""
    dados: dict[str, Any] = {}
    if caminho:
        p = Path(caminho).expanduser()
        if not p.exists():
            raise FileNotFoundError(f"Ficheiro de configuração não encontrado: {p}")
        if yaml is None:
            raise ImportError("PyYAML não está instalado: pip install PyYAML")
        dados = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if not isinstance(dados, dict):
            raise ValueError(f"{p} não contém um mapeamento YAML válido.")

    campos = {f for f in Config.__dataclass_fields__}
    extra = {k: v for k, v in dados.items() if k not in campos}
    dados = {k: v for k, v in dados.items() if k in campos}
    dados.update({k: v for k, v in sobreposicoes.items() if v is not None})
    cfg = Config(**dados)
    cfg.extra.update(extra)
    return cfg
