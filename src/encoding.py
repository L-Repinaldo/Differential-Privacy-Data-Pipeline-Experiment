"""Codificação reversível de atributos categóricos."""

import numpy as np
import pandas as pd


class EncodingError(Exception):
    pass


def encode_dataframe(df: pd.DataFrame, encoding_cfg: dict) -> pd.DataFrame:
    """Codifica o chunk recebido *in place* e o retorna."""
    validate_encoding(df, encoding_cfg)
    for column, mapping in encoding_cfg.items():
        df[column] = df[column].map(mapping)
    return df


def reverse_mappings(encoding_cfg: dict) -> dict:
    """Monta os mapeamentos de decodificação e valida sua reversibilidade."""
    reverse = {}
    for column, mapping in encoding_cfg.items():
        if len(mapping) != len(set(mapping.values())):
            raise EncodingError(f"Mapeamento da coluna '{column}' não é reversível.")
        if not all(isinstance(code, (int, float, np.integer, np.floating)) for code in mapping.values()):
            raise EncodingError(f"Códigos da coluna '{column}' devem ser numéricos.")
        reverse[column] = {code: value for value, code in mapping.items()}
    return reverse


def sensitive_mappings(encoding_cfg: dict, sensitive_attributes: list[str]) -> dict:
    """Retorna somente categorias que efetivamente serão perturbadas."""
    return {
        column: mapping
        for column, mapping in encoding_cfg.items()
        if column in sensitive_attributes
    }


def decode_dataframe(df: pd.DataFrame, reverse_mapping: dict) -> pd.DataFrame:
    """Decodifica o DataFrame *in place* imediatamente antes da persistência."""
    for column, mapping in reverse_mapping.items():
        codes = np.asarray(sorted(mapping))
        values = np.asarray([mapping[code] for code in codes], dtype=object)
        numeric = pd.to_numeric(df[column], errors="coerce").to_numpy()
        valid = ~np.isnan(numeric)
        decoded = np.full(len(df), np.nan, dtype=object)
        if valid.any():
            positions = np.searchsorted(codes, numeric[valid], side="left")
            positions = positions.clip(0, len(codes) - 1)
            previous = (positions - 1).clip(0, len(codes) - 1)
            nearest = np.where(
                np.abs(numeric[valid] - codes[previous]) <= np.abs(numeric[valid] - codes[positions]),
                previous,
                positions,
            )
            decoded[valid] = values[nearest]
        df[column] = decoded
    return df


def validate_encoding(df: pd.DataFrame, encoding_cfg: dict) -> None:
    for column, mapping in encoding_cfg.items():
        if column not in df.columns:
            raise EncodingError(f"Coluna '{column}' não encontrada.")
        if not isinstance(mapping, dict) or not mapping:
            raise EncodingError(f"Mapeamento inválido para a coluna '{column}'.")

        unknown = set(df[column].dropna().unique()) - set(mapping)
        if unknown:
            raise EncodingError(
                f"Valores desconhecidos na coluna '{column}': {sorted(unknown)}"
            )
