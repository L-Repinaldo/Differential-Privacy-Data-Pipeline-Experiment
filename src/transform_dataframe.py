"""Seleção e validação das colunas usadas pelo pipeline."""

import pandas as pd


class TransformError(Exception):
    pass


def prepare_dataframe(data: pd.DataFrame, transform_cfg: dict) -> pd.DataFrame:
    """Retorna somente as colunas de saída para um chunk de entrada.

    A seleção substitui a remoção prévia das demais colunas: o resultado é o
    mesmo, mas evita criar uma cópia intermediária do chunk inteiro.
    """
    columns = output_columns(transform_cfg)
    _validate_columns(data.columns, columns, "Colunas de saída")
    _validate_columns(data.columns, transform_cfg["drop_columns"], "Colunas para descarte")
    return data.loc[:, columns]


def output_columns(transform_cfg: dict) -> list[str]:
    required = ("drop_columns", "nominal_columns", "ordinal_columns", "numerical_columns", "target")
    missing = [key for key in required if key not in transform_cfg]
    if missing:
        raise TransformError(f"Configuração de transformação sem {missing}")

    target = transform_cfg["target"]
    if not isinstance(target, dict) or "column" not in target:
        raise TransformError("Configuração de transformação sem 'target.column'")

    columns = (
        list(transform_cfg["nominal_columns"])
        + list(transform_cfg["ordinal_columns"])
        + list(transform_cfg["numerical_columns"])
        + [target["column"]]
    )
    duplicated = sorted({column for column in columns if columns.count(column) > 1})
    if duplicated:
        raise TransformError(f"Colunas de saída duplicadas: {duplicated}")
    return columns


def _validate_columns(available: pd.Index, expected: list[str], label: str) -> None:
    missing = sorted(set(expected) - set(available))
    if missing:
        raise TransformError(f"{label} não encontradas: {missing}")
