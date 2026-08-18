"""
presepios — pipeline de análise de literatura dramática portuguesa setecentista.

Automatiza o fluxo de trabalho de análise de presépios teatrais, entremezes e
comédias: prepara a transcrição, corre a análise em duas rondas encadeadas
(prompt chaining) sobre a API da Claude, extrai e valida as tabelas de dados e
gera um dashboard HTML interactivo autocontido.
"""

__version__ = "1.0.0"

from .config import Config, carregar_config

__all__ = ["Config", "carregar_config", "__version__"]
