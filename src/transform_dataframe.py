"""Seleção e validação das colunas usadas pelo pipeline."""

import pandas as pd


class TransformError(Exception):
    pass


def prepare_dataframe(
    data: pd.DataFrame,
    transform_cfg: dict,
) -> pd.DataFrame:
    """Seleciona as colunas que permanecem no pipeline."""

    drop_columns = transform_cfg["drop_columns"]

    _validate_columns(
        data.columns,
        drop_columns,
        "Colunas para descarte",
    )

    columns = [
        column
        for column in data.columns
        if column not in drop_columns
    ]

    return data.loc[:, columns]


def output_columns(
    available_columns: pd.Index,
    transform_cfg: dict,
) -> list[str]:
    """Retorna as colunas que devem permanecer no dataset."""

    if "drop_columns" not in transform_cfg:
        raise TransformError(
            "Configuração de transformação sem 'drop_columns'"
        )

    drop_columns = list(transform_cfg["drop_columns"])

    columns = [
        column
        for column in available_columns
        if column not in drop_columns
    ]

    if not columns:
        raise TransformError(
            "Nenhuma coluna disponível após os descartes."
        )

    return columns


def _validate_columns(
    available: pd.Index,
    expected: list[str],
    label: str,
) -> None:
    missing = sorted(set(expected) - set(available))

    if missing:
        raise TransformError(
            f"{label} não encontradas: {missing}"
        )
