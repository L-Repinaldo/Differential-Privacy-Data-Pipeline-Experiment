"""Aplicação incremental do mecanismo de Laplace."""

import numpy as np
import pandas as pd



class DPError(Exception):
    pass


def validate_privacy_config(privacy_cfg: dict, columns: list[str]) -> None:
    required = ("mechanism", "epsilons", "seed", "sensitive_attributes")
    missing = [key for key in required if key not in privacy_cfg]
    if missing:
        raise DPError(f"Configuração de privacidade sem {missing}")
    if privacy_cfg["mechanism"] != "laplace":
        raise DPError("Somente mecanismo Laplace é suportado.")

    if not isinstance(privacy_cfg["epsilons"], list) or not privacy_cfg["epsilons"]:
        raise DPError("'epsilons' deve ser uma lista não vazia.")

    unknown = sorted(set(privacy_cfg["sensitive_attributes"]) - set(columns))
    if unknown:
        raise DPError(f"Atributos sensíveis ausentes no dataset: {unknown}")
    if any(epsilon <= 0 for epsilon in privacy_cfg["epsilons"]):
        raise DPError("Todos os valores de epsilon devem ser positivos.")


def update_bounds(bounds: dict, df: pd.DataFrame, attributes: list[str]) -> int:
    """Acumula limites globais de cada atributo e retorna as linhas lidas."""
    for column in attributes:
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise DPError(f"'{column}' deve ser numérica após a codificação.")
        column_min = df[column].min(skipna=True)
        column_max = df[column].max(skipna=True)
        if pd.isna(column_min) or pd.isna(column_max):
            raise DPError(f"'{column}' não pode conter somente valores ausentes.")
        current = bounds.setdefault(column, {"min": float(column_min), "max": float(column_max)})
        current["min"] = min(current["min"], float(column_min))
        current["max"] = max(current["max"], float(column_max))
    return len(df)


def apply_dp(
    df: pd.DataFrame,
    sensitive_attributes: list[str],
    epsilon: float,
    bounds: dict,
    rng: np.random.RandomState,
) -> pd.DataFrame:
    """Retorna uma visão rasa do chunk com ruído apenas nas colunas sensíveis."""
    if epsilon <= 0:
        raise DPError("Epsilon deve ser positivo.")
    df_dp = df.copy(deep=False)
    for column in sensitive_attributes:
        if column not in bounds:
            raise DPError(f"Limites não calculados para '{column}'.")
        minimum = bounds[column]["min"]
        maximum = bounds[column]["max"]
        df_dp[column] = apply_noise(df[column], epsilon, maximum - minimum, minimum, maximum, rng)
    return df_dp


def apply_noise(
    series: pd.Series,
    epsilon: float,
    sensitivity: float,
    minimum: float,
    maximum: float,
    rng: np.random.RandomState,
) -> pd.Series:
    if sensitivity == 0:
        return series.copy(deep=False)
    noise = rng.laplace(loc=0.0, scale=sensitivity / epsilon, size=len(series))
    return (series + noise).clip(lower=minimum, upper=maximum)


def build_metadata(
    dataset_name: str,
    privacy_cfg: dict,
    row_count: int,
    column_count: int,
    bounds: dict,
) -> dict:
    attributes = {
        column: {**limits, "sensitivity": limits["max"] - limits["min"]}
        for column, limits in bounds.items()
    }
    return {
        "dataset": dataset_name,
        "mechanism": privacy_cfg["mechanism"],
        "seed": privacy_cfg["seed"],
        "rows": row_count,
        "columns": column_count,
        "epsilons": privacy_cfg["epsilons"],
        "attributes": attributes,
    }
