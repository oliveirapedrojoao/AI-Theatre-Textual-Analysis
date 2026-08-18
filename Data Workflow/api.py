"""
Cliente da API: encadeamento das duas rondas, cache do texto da peça,
extended thinking, retomas em caso de truncagem e contabilidade de tokens.

O texto da peça é enviado uma única vez por ronda como bloco em cache
(`cache_control`), pelo que a segunda ronda relê a peça a preço de cache em vez
de a reenviar por inteiro — a poupança cresce com a extensão da peça.
"""

from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .config import Config
from .prompts import (
    SISTEMA,
    prompt_ronda1,
    prompt_ronda1_continuacao,
    prompt_ronda2,
)
from .texto import Peca, Segmento, segmentar

ERROS_RETENTAVEIS = ("overloaded", "rate_limit", "429", "500", "502", "503", "529", "timeout")


# ------------------------------------------------------------------ utilidades
def _chave_natural(s: str) -> list:
    """Ordena `claude-opus-10` depois de `claude-opus-4` (e não antes)."""
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", s)]


def escolher_modelo(client, preferencia: str = "auto") -> str:
    """Resolve o identificador do modelo.

    `auto` consulta a API e escolhe o Opus mais recente disponível na conta,
    recuando para Sonnet. Evita identificadores fixos no código, que envelhecem.
    """
    if preferencia and preferencia != "auto":
        return preferencia
    try:
        disponiveis = [m.id for m in client.models.list(limit=100).data]
    except Exception as e:  # pragma: no cover - depende da rede
        raise RuntimeError(
            "Não foi possível listar os modelos disponíveis para resolver "
            f"`modelo: auto` ({e}). Define `modelo:` explicitamente na configuração."
        ) from e
    for familia in ("claude-opus", "claude-sonnet", "claude-haiku"):
        candidatos = [m for m in disponiveis if m.startswith(familia)]
        if candidatos:
            return sorted(candidatos, key=_chave_natural)[-1]
    raise RuntimeError(f"Nenhum modelo Claude encontrado. Disponíveis: {disponiveis}")


@dataclass
class Uso:
    """Acumulador de tokens e de custo estimado."""

    input: int = 0
    output: int = 0
    cache_escrita: int = 0
    cache_leitura: int = 0
    chamadas: int = 0
    segundos: float = 0.0

    def somar(self, usage: Any) -> None:
        self.input += getattr(usage, "input_tokens", 0) or 0
        self.output += getattr(usage, "output_tokens", 0) or 0
        self.cache_escrita += getattr(usage, "cache_creation_input_tokens", 0) or 0
        self.cache_leitura += getattr(usage, "cache_read_input_tokens", 0) or 0
        self.chamadas += 1

    def custo(self, cfg: Config) -> float | None:
        precos = (cfg.preco_input, cfg.preco_output, cfg.preco_cache_escrita, cfg.preco_cache_leitura)
        if any(p is None for p in precos):
            return None
        pi, po, pce, pcl = precos  # type: ignore[misc]
        return (
            self.input * pi
            + self.output * po
            + self.cache_escrita * pce
            + self.cache_leitura * pcl
        ) / 1_000_000

    def como_dict(self, cfg: Config | None = None) -> dict[str, Any]:
        d = {
            "tokens_input": self.input,
            "tokens_output": self.output,
            "tokens_cache_escrita": self.cache_escrita,
            "tokens_cache_leitura": self.cache_leitura,
            "chamadas": self.chamadas,
            "segundos": round(self.segundos, 1),
        }
        if cfg is not None:
            c = self.custo(cfg)
            if c is not None:
                d["custo_usd_estimado"] = round(c, 4)
        return d


@dataclass
class Resultado:
    ronda1: str
    ronda2: str
    modelo: str
    uso: Uso = field(default_factory=Uso)
    segmentos: list[str] = field(default_factory=list)
    interrompido: bool = False
    motivo_interrupcao: str = ""


# --------------------------------------------------------------------- cliente
class Analisador:
    def __init__(self, cfg: Config, verboso: bool = True, on_log: Callable[[str], None] | None = None):
        try:
            from anthropic import Anthropic
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "O SDK da Anthropic não está instalado: pip install anthropic"
            ) from e

        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "Falta a variável de ambiente ANTHROPIC_API_KEY.\n"
                "  export ANTHROPIC_API_KEY='sk-ant-...'"
            )

        self.cfg = cfg
        self.verboso = verboso
        self._log_externo = on_log
        self.client = Anthropic(max_retries=0)  # os retries são geridos aqui
        self.modelo = escolher_modelo(self.client, cfg.modelo)
        self.uso = Uso()

    # -------------------------------------------------------------------- log
    def log(self, msg: str) -> None:
        if self._log_externo:
            self._log_externo(msg)
        if self.verboso:
            print(f"  {msg}", file=sys.stderr, flush=True)

    # ------------------------------------------------------------- chamada base
    def _chamar(
        self,
        mensagens: list[dict],
        max_tokens: int,
        pensamento: int,
        etiqueta: str,
    ) -> tuple[str, str]:
        """Uma chamada em streaming, com retries. Devolve (texto, stop_reason)."""
        kwargs: dict[str, Any] = {
            "model": self.modelo,
            "max_tokens": max_tokens,
            "system": [{"type": "text", "text": SISTEMA, "cache_control": {"type": "ephemeral"}}],
            "messages": mensagens,
        }
        if pensamento and pensamento > 0:
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": pensamento}
            kwargs["max_tokens"] = max(max_tokens, pensamento + 8000)
            kwargs["temperature"] = 1

        atraso = 5.0
        ultimo_erro: Exception | None = None
        for tentativa in range(1, self.cfg.tentativas + 1):
            inicio = time.time()
            try:
                partes: list[str] = []
                with self.client.messages.stream(**kwargs) as stream:
                    for fragmento in stream.text_stream:
                        partes.append(fragmento)
                    final = stream.get_final_message()
                self.uso.somar(final.usage)
                self.uso.segundos += time.time() - inicio
                texto = "".join(partes)
                self.log(
                    f"{etiqueta}: {len(texto):,} caracteres · "
                    f"{final.usage.output_tokens:,} tokens de saída · "
                    f"cache lido {getattr(final.usage, 'cache_read_input_tokens', 0):,} · "
                    f"stop={final.stop_reason}".replace(",", " ")
                )
                return texto, (final.stop_reason or "")
            except Exception as e:  # pragma: no cover - depende da rede
                self.uso.segundos += time.time() - inicio
                ultimo_erro = e
                msg = str(e).lower()
                retentavel = any(t in msg for t in ERROS_RETENTAVEIS)
                if not retentavel or tentativa == self.cfg.tentativas:
                    raise
                self.log(f"{etiqueta}: erro transitório ({e.__class__.__name__}); "
                         f"nova tentativa em {atraso:.0f}s [{tentativa}/{self.cfg.tentativas}]")
                time.sleep(atraso)
                atraso *= 2
        raise ultimo_erro  # type: ignore[misc]

    def _chamar_completo(
        self,
        mensagens: list[dict],
        max_tokens: int,
        pensamento: int,
        etiqueta: str,
        max_continuacoes: int = 3,
    ) -> str:
        """Chama e, se a resposta for truncada por `max_tokens`, pede continuação."""
        texto, motivo = self._chamar(mensagens, max_tokens, pensamento, etiqueta)
        continuacoes = 0
        while motivo == "max_tokens" and continuacoes < max_continuacoes:
            continuacoes += 1
            self.log(f"{etiqueta}: resposta truncada; a pedir continuação {continuacoes}")
            mensagens = mensagens + [
                {"role": "assistant", "content": texto.rstrip()},
                {"role": "user", "content": prompt_ronda1_continuacao()},
            ]
            extra, motivo = self._chamar(
                mensagens, max_tokens, 0, f"{etiqueta} (continuação {continuacoes})"
            )
            juncao = "" if texto.endswith(("\n", " ")) else ""
            texto = texto + juncao + extra
        return texto

    # ------------------------------------------------------------ blocos úteis
    def _bloco_peca(self, texto_numerado: str, rotulo: str) -> dict:
        return {
            "type": "text",
            "text": f"<transcricao rotulo=\"{rotulo}\">\n{texto_numerado}\n</transcricao>",
            "cache_control": {"type": "ephemeral"},
        }

    # ------------------------------------------------------------------ rondas
    def ronda1(self, peca: Peca) -> tuple[str, list[str]]:
        cfg = self.cfg
        segmentos: list[Segmento] = (
            segmentar(peca, cfg.max_linhas_segmento)
            if cfg.segmentar
            else [Segmento(1, 1, peca.n_linhas, peca.texto_numerado, "peça integral")]
        )
        if len(segmentos) > 1:
            self.log(f"Peça dividida em {len(segmentos)} segmentos para a Ronda 1.")

        partes: list[str] = []
        for seg in segmentos:
            rotulo = seg.descricao if len(segmentos) > 1 else ""
            instrucao = prompt_ronda1(
                cfg,
                peca.resumo(),
                peca.personagens_detectadas,
                rotulo_segmento=rotulo,
            )
            mensagens = [
                {
                    "role": "user",
                    "content": [
                        self._bloco_peca(seg.texto_numerado, rotulo or cfg.titulo),
                        {"type": "text", "text": instrucao},
                    ],
                }
            ]
            etiqueta = f"Ronda 1{f' · seg. {seg.indice}/{len(segmentos)}' if len(segmentos) > 1 else ''}"
            texto = self._chamar_completo(
                mensagens, cfg.max_tokens_ronda1, cfg.pensamento_ronda1, etiqueta
            )
            if len(segmentos) > 1:
                texto = f"## {seg.descricao}\n\n{texto}"
            partes.append(texto)

        return "\n\n---\n\n".join(partes), [s.descricao for s in segmentos]

    def ronda2(self, peca: Peca, analise_ronda1: str, segmentado: bool) -> str:
        cfg = self.cfg
        if segmentado:
            # A análise vem em partes: consolidar numa só passagem, com a peça
            # integral em cache para consulta.
            mensagens = [
                {
                    "role": "user",
                    "content": [
                        self._bloco_peca(peca.texto_numerado, cfg.titulo),
                        {"type": "text", "text": prompt_ronda2(cfg, analise_ronda1)},
                    ],
                }
            ]
        else:
            instrucao1 = prompt_ronda1(cfg, peca.resumo(), peca.personagens_detectadas)
            mensagens = [
                {
                    "role": "user",
                    "content": [
                        self._bloco_peca(peca.texto_numerado, cfg.titulo),
                        {"type": "text", "text": instrucao1},
                    ],
                },
                {"role": "assistant", "content": analise_ronda1.rstrip()},
                {"role": "user", "content": prompt_ronda2(cfg)},
            ]
        return self._chamar_completo(
            mensagens, cfg.max_tokens_ronda2, cfg.pensamento_ronda2, "Ronda 2"
        )

    # ------------------------------------------------------------------ fachada
    def analisar(self, peca: Peca) -> Resultado:
        self.log(f"Modelo: {self.modelo}")
        self.log(peca.resumo())

        r1, segmentos = self.ronda1(peca)
        if _parece_recusa(r1):
            return Resultado(
                ronda1=r1,
                ronda2="",
                modelo=self.modelo,
                uso=self.uso,
                segmentos=segmentos,
                interrompido=True,
                motivo_interrupcao=(
                    "A Ronda 1 comunicou um problema com a transcrição em vez de "
                    "produzir a análise. Verifica o ficheiro antes de repetir."
                ),
            )
        r2 = self.ronda2(peca, r1, segmentado=len(segmentos) > 1)
        return Resultado(
            ronda1=r1, ronda2=r2, modelo=self.modelo, uso=self.uso, segmentos=segmentos
        )


def _parece_recusa(texto: str) -> bool:
    """Detecta a paragem prevista no protocolo (transcrição ausente/ilegível)."""
    if len(texto.strip()) > 2500:
        return False
    baixo = texto.lower()
    sinais = ("ilegível", "ilegivel", "não recebi", "nao recebi", "ausente", "truncada")
    tem_seccoes = "<personagens>" in baixo or "<vernaculo_recursos>" in baixo
    return (not tem_seccoes) and any(s in baixo for s in sinais)
