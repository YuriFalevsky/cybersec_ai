"""
Поддержка TEXT и PDF; легко расширяется под DOCX, Markdown и т.п.
"""

from pathlib import Path
from typing import Final
from .config import MAX_FILE_SIZE
import pypdf

_TEXT_EXT: Final = {".txt", ".md", ".csv", ".log"}
_PDF_EXT:  Final = {".pdf"}

def load_text(file_path: str | Path) -> str:
    path = Path(file_path)

    if path.stat().st_size > MAX_FILE_SIZE:
        raise ValueError(f"Файл слишком большой: {path.stat().st_size} байт > {MAX_FILE_SIZE}")

    if path.suffix in _TEXT_EXT:
        return path.read_text(encoding="utf-8", errors="ignore")

    if path.suffix in _PDF_EXT:
        pdf = pypdf.PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

    raise ValueError(f"Неподдерживаемый тип файла: {path.suffix}")
