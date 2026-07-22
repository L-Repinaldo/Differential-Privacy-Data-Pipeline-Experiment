"""Extração incremental de datasets tabulares."""

from collections.abc import Iterator

import pandas as pd


DEFAULT_CHUNK_SIZE = 100_000


class ExtractionError(Exception):
    pass


def extract(source_cfg: dict) -> Iterator[pd.DataFrame]:
    """Lê a fonte CSV em chunks, sem materializar o arquivo inteiro em memória."""
    required_keys = ("file", "separator", "encoding")
    missing = [key for key in required_keys if key not in source_cfg]
    if missing:
        raise ExtractionError(f"Configuração de fonte de dados sem {missing}")

    chunk_size = source_cfg.get("chunk_size", DEFAULT_CHUNK_SIZE)
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ExtractionError("'chunk_size' deve ser um inteiro positivo")

    return pd.read_csv(
        source_cfg["file"],
        sep=source_cfg["separator"],
        encoding=source_cfg["encoding"],
        chunksize=chunk_size,
    )
