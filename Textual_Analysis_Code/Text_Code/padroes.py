"""Convenções de transcrição reconhecidas pelo carregador.

Este é o ficheiro a estender quando uma transcrição nova usar uma convenção
que o pipeline ainda não conhece: acrescenta-se aqui o padrão e todo o resto
— detecção, segmentação, localização — passa a reconhecê-lo."""

from __future__ import annotations

import re

EXTENSOES_ACEITES = {".txt", ".md", ".markdown", ".text"}

RE_ESTRUTURA = re.compile(
    r"^\s*(?:"
    r"(?:CENA|SCENA|SENA)\b"
    r"|(?:ACTO|ATO|AUTO)\b"
    r"|(?:JORNADA)\b"
    r"|(?:ENTREMEZ|ENTREMÊS)\b"
    r"|(?:PROLOGO|PRÓLOGO|LOA)\b"
    r"|(?:PASSO|PERCEITO|PRECEITO)\s+(?:DE|DA|DO|DOS|DAS)\b"
    r"|(?:VISTA)\s+(?:DE|DA|DO|DOS|DAS)\b"
    r"|(?:FIM|FINIS)\b"
    r")",
    re.IGNORECASE,
)

# Rubricas de fala. As transcrições usam convenções muito diferentes entre si,
# pelo que se tentam várias, da mais fiável para a mais ambígua.
RE_FALAS = (
    # "Chantre: Pára, vamos…"  ·  "1.º Capitão: Com a espada…"
    re.compile(r"^\s*(?P<n>[0-9A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][^\n:;]{0,34}?)\s*:\s+\S"),
    # "Adão – A tua voz, senhor…"  ·  "Padre Eterno -  Este é o lugar…"
    re.compile(r"^\s*(?P<n>[0-9A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][^\n:;]{0,34}?)\s*[–—]\s+\S"),
    # "BRAZ. Ó compadre Gil…"  (maiúsculas com ponto)
    re.compile(r"^\s*(?P<n>[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][A-ZÁÀÂÃÉÊÍÓÔÕÚÇ\s'’\-]{1,34}?)\s*\.\s+\S"),
    # "\tAlceto\tQue escuto?"  (colunas separadas por tabulação)
    re.compile(r"^[ \t]*(?P<n>[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][^\t\n]{0,30}?)\t+\s*\S"),
)

# Forma invertida: "Fala Eva – De todas nos facultou…", "Fala Adão e diz:"
RE_FALA_INVERTIDA = re.compile(
    r"^\s*(?:Fala|Diz|Recita|Responde)\s+(?:o\s+|a\s+)?"
    r"(?P<n>[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][^\n:;–—\-]{1,28}?)"
    r"\s*(?:e\s+diz)?\s*[:\-–—]\s*",
    re.IGNORECASE,
)

# Verbos de dizer colados à rubrica: "Luzbel diz:", "Padre Eterno fala:"
RE_VERBO_DIZER = re.compile(
    r"[\s,]*(?:fala\s+e\s+diz|canta\s+e\s+diz|fala|diz|canta|reza|responde)\s*$",
    re.IGNORECASE,
)

# Rubricas que são didascália, não personagem.
NAO_PERSONAGENS = {
    "fala", "diz", "fala e diz", "canta", "canta e diz", "sai", "saem", "sahe",
    "sahem", "vai-se", "vao-se", "recolhem-se", "aparece", "aparecem", "vista",
    "pessoas", "interlocutores", "personagens", "figuras", "nota", "soneto",
    "glosa", "decima", "fim", "finis", "passo", "cena", "acto", "jornada",
    "senhora", "senhor", "reza", "rezd", "dentro", "e r", "e r m", "advertencia",
    "continua o coro", "bebe", "vai se", "sao as pensoes da vida",
}

RE_FOLIO = re.compile(
    r"(?:\[\s*f(?:l|ól|ol)?\.?\s*[0-9]{1,4}\s*[vr]?\s*\]"
    r"|^\s*f(?:l|ól|ol)?\.?\s*[0-9]{1,4}\s*[vr]?\s*$)",
    re.IGNORECASE | re.MULTILINE,
)
