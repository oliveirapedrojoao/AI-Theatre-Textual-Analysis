"""
Núcleo: o que todas as outras partes precisam de conhecer.

`config` guarda os metadados da peça e os parâmetros de execução; `esquemas`
é a fonte única de verdade sobre as colunas das cinco tabelas — é importado
pelos prompts (para as pedir), pelo extractor (para as reconhecer) e pelo
validador (para as verificar); `pipeline` liga tudo de ponta a ponta.
"""

from .config import Config, carregar_config
from .esquemas import ESQUEMAS, Esquema, esquema_por_cabecalho

__all__ = ["Config", "carregar_config", "ESQUEMAS", "Esquema", "esquema_por_cabecalho"]
