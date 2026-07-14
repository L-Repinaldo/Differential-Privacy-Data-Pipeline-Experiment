import pandas as pd
import numpy as np

from diffprivlib.mechanisms import Laplace


class DPError(Exception):
    pass


def validate_privacy_config(df, privacy_cfg):

    if "sensitive_attributes" not in privacy_cfg:
        raise DPError(
            "Configuração de privacidade sem 'sensitive_attributes'"
        )

    if "mechanism" not in privacy_cfg:
        raise DPError(
            "Configuração de privacidade sem 'mechanism'"
        )

    for attr, bounds in privacy_cfg["sensitive_attributes"].items():

        if attr not in df.columns:
            raise DPError(
                f"Atributo sensível ausente no dataset: {attr}"
            )

        if not pd.api.types.is_numeric_dtype(df[attr]):
            raise DPError(
                f"Atributo não numérico: {attr}"
            )

        if "min" not in bounds or "max" not in bounds:
            raise DPError(
                f"Bounds incompletos para {attr}"
            )

        if bounds["min"] >= bounds["max"]:
            raise DPError(
                f"Bounds inválidos para {attr}"
            )

    epsilons = privacy_cfg["mechanism"].get("epsilons", [])

    for epsilon in epsilons:
        if epsilon <= 0:
            raise DPError(
                f"Epsilon inválido: {epsilon}"
            )


def clip_series(series, min_value, max_value):

    return series.clip(
        lower=min_value,
        upper=max_value
    )


def apply_laplace_noise(value, epsilon, sensitivity, rng=None):
    """
    Aplica ruído Laplace usando um RNG fornecido para reprodutibilidade.

    `rng` deve ser um objeto compatível com NumPy (Generator/RandomState) ou um int.
    """

    mechanism = Laplace(
        epsilon=epsilon,
        sensitivity=sensitivity,
        random_state=rng,
    )

    return mechanism.randomise(value)


def apply_dp(df, privacy_cfg):
    """
    Aplica Privacidade Diferencial linha a linha.

    Cada atributo sensível recebe ruído Laplace
    individualmente mantendo:
    - mesma estrutura do dataset;
    - mesmas colunas;
    - diferentes versões por epsilon.
    """

    validate_privacy_config(df, privacy_cfg)

    results = {}

    metadata = {
        "mechanism": "laplace",
        "attributes": {}
    }

    sensitive_attributes = privacy_cfg["sensitive_attributes"]
    mechanism_cfg = privacy_cfg["mechanism"]

    if mechanism_cfg["name"] != "laplace":
        raise DPError(
            f"Mecanismo não suportado: {mechanism_cfg['name']}"
        )

    for attr, bounds in sensitive_attributes.items():

        sensitivity = bounds["max"] - bounds["min"]

        metadata["attributes"][attr] = {
            "min": bounds["min"],
            "max": bounds["max"],
            "sensitivity": sensitivity
        }

    epsilons = sorted(
        mechanism_cfg["epsilons"]
    )

    # Seed / RNG para reprodutibilidade: usar seed configurada ou default 42
    seed = mechanism_cfg.get("seed", 42)
    # diffprivlib expects a RandomState-like object or an int; use RandomState
    rng = np.random.RandomState(seed)

    # registrar a seed nos metadados (adiciona campo sem remover os existentes)
    metadata["seed"] = seed

    for epsilon in epsilons:
        df_dp = df.copy()

        for attr, bounds in sensitive_attributes.items():
            sensitivity = bounds["max"] - bounds["min"]

            df_dp[attr] = df_dp[attr].apply(
                lambda value: apply_laplace_noise(
                    value=value,
                    epsilon=epsilon,
                    sensitivity=sensitivity,
                    rng=rng,
                )
            )

            df_dp[attr] = clip_series(df_dp[attr], bounds["min"], bounds["max"])

        results[epsilon] = df_dp

    metadata["epsilons"] = epsilons

    return results, metadata