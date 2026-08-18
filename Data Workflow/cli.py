"""Interface de linha de comandos."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import Config, carregar_config


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="presepios",
        description=(
            "Análise assistida de literatura dramática portuguesa setecentista: "
            "das transcrições às tabelas e ao dashboard interactivo."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
exemplos:
  presepios analisar peca.txt --titulo "Presépio da Graça" --datacao "c. 1760"
  presepios analisar --config pecas/graca.yaml
  presepios reprocessar saidas/presepio-da-graca      # sem chamar a API
  presepios prompts peca.txt --config graca.yaml      # para correr à mão no chat
  presepios modelos
""",
    )
    p.add_argument("--versao", action="version", version=f"presepios {__version__}")
    sub = p.add_subparsers(dest="comando", required=True)

    def comuns(sp):
        sp.add_argument("peca", nargs="?", help="transcrição .txt/.md da peça")
        sp.add_argument("-c", "--config", help="ficheiro YAML de configuração")
        sp.add_argument("-o", "--saida", help="directório de saída (por omissão: saidas/)")
        sp.add_argument("--titulo")
        sp.add_argument("--datacao")
        sp.add_argument("--proveniencia")
        sp.add_argument("--genero")
        sp.add_argument("--notas-contexto", dest="notas_contexto")
        sp.add_argument("-q", "--silencioso", action="store_true")

    sa = sub.add_parser("analisar", help="corre o pipeline completo (chama a API)")
    comuns(sa)
    sa.add_argument("-m", "--modelo", help="id do modelo, ou 'auto'")
    sa.add_argument("--segmentar", action="store_true",
                    help="divide peças extensas em segmentos na Ronda 1")
    sa.add_argument("--max-linhas-segmento", type=int, dest="max_linhas_segmento")
    sa.add_argument("--sem-pensamento", action="store_true",
                    help="desliga o extended thinking (mais rápido, menos rigoroso)")
    sa.add_argument("--sem-cotejo", action="store_true",
                    help="não coteja as citações com a transcrição")

    sr = sub.add_parser("reprocessar",
                        help="reconstrói tabelas e dashboard a partir de respostas já gravadas")
    sr.add_argument("directorio", help="pasta de saída de uma execução anterior")
    sr.add_argument("-c", "--config", help="ficheiro YAML (por omissão usa execucao.json)")
    sr.add_argument("-q", "--silencioso", action="store_true")

    spp = sub.add_parser("prompts",
                         help="escreve os prompts e a transcrição numerada, para usar à mão")
    comuns(spp)

    sub.add_parser("modelos", help="lista os modelos disponíveis na conta")
    return p


def _config_de_args(args) -> Config:
    sobre = {
        k: getattr(args, k, None)
        for k in ("peca", "titulo", "datacao", "proveniencia", "genero",
                  "notas_contexto", "saida", "modelo", "max_linhas_segmento")
        if getattr(args, k, None)
    }
    cfg = carregar_config(getattr(args, "config", None), **sobre)
    if getattr(args, "segmentar", False):
        cfg.segmentar = True
    if getattr(args, "sem_pensamento", False):
        cfg.pensamento_ronda1 = 0
        cfg.pensamento_ronda2 = 0
    if getattr(args, "sem_cotejo", False):
        cfg.verificar_citacoes = False
    if not cfg.peca:
        raise SystemExit(
            "Erro: indica a transcrição, como argumento ou pelo campo `peca:` da configuração."
        )
    return cfg


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    verboso = not getattr(args, "silencioso", False)

    if args.comando == "modelos":
        import os
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("Falta ANTHROPIC_API_KEY no ambiente.", file=sys.stderr)
            return 2
        from anthropic import Anthropic
        for m in Anthropic().models.list(limit=100).data:
            print(f"{m.id}\t{getattr(m, 'display_name', '')}")
        return 0

    if args.comando == "prompts":
        from .prompts import SISTEMA, prompt_ronda1, prompt_ronda2
        from .texto import carregar_peca

        cfg = _config_de_args(args)
        peca = carregar_peca(cfg.peca, cfg.prefixo_linha, cfg.numerar_linhas)
        destino = cfg.dir_saida / cfg.slug / "prompts"
        destino.mkdir(parents=True, exist_ok=True)
        (destino / "sistema.txt").write_text(SISTEMA, encoding="utf-8")
        (destino / "ronda1.txt").write_text(
            prompt_ronda1(cfg, peca.resumo(), peca.personagens_detectadas), encoding="utf-8"
        )
        (destino / "ronda2.txt").write_text(prompt_ronda2(cfg), encoding="utf-8")
        (destino / "peca_numerada.txt").write_text(peca.texto_numerado, encoding="utf-8")
        print(f"Prompts e transcrição numerada em: {destino}")
        print(peca.resumo())
        return 0

    if args.comando == "reprocessar":
        import json
        from .pipeline import correr

        pasta = Path(args.directorio).expanduser()
        exec_json = pasta / "execucao.json"
        if args.config:
            cfg = carregar_config(args.config)
        elif exec_json.exists():
            dados = json.loads(exec_json.read_text("utf-8")).get("config", {})
            campos = set(Config.__dataclass_fields__)
            cfg = Config(**{k: v for k, v in dados.items() if k in campos})
        else:
            print(f"Sem `execucao.json` em {pasta}; indica --config.", file=sys.stderr)
            return 2
        saida = correr(cfg, reutilizar=pasta, verboso=verboso)
        print(saida.dashboard)
        return 0 if saida.relatorio.valido else 1

    # analisar
    from .pipeline import correr

    cfg = _config_de_args(args)
    try:
        saida = correr(cfg, verboso=verboso)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 2
    print(saida.dashboard)
    return 0 if saida.relatorio.valido else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
