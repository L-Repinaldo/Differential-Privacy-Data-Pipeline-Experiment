import datetime

import numpy as np
import yaml

from src import (
    data_exraction,
    diferential_privacy,
    encoding,
    transform_dataframe,
    versioning,
)


CONFIG_PATH = "config/enem.yaml"


def _prepared_chunks(cfg: dict):
    """Extrai e prepara os chunks da fonte de dados."""
    for chunk in data_exraction.extract(cfg["source"]):
        yield transform_dataframe.prepare_dataframe(
            chunk,
            cfg,
        )


def _profile_dataset(
    cfg: dict,
    encoding_cfg: dict,
) -> tuple[dict, int, list[str]]:
    """Calcula limites globais e identifica as colunas de saída."""

    bounds = {}
    row_count = 0
    columns = None

    for chunk_index, chunk in enumerate(
        _prepared_chunks(cfg),
        start=1,
    ):
        if columns is None:
            columns = list(chunk.columns)

        encoding.encode_dataframe(
            chunk,
            encoding_cfg,
        )

        row_count += diferential_privacy.update_bounds(
            bounds,
            chunk,
            cfg["privacy"]["sensitive_attributes"],
        )

        print(
            f"  profiling: {row_count:,} rows read "
            f"(chunk {chunk_index})",
            flush=True,
        )

    if columns is None:
        raise RuntimeError("Nenhum dado foi encontrado.")

    return bounds, row_count, columns


def run(config_path: str = CONFIG_PATH) -> dict:
    """Executa o pipeline completo de geração dos datasets."""

    with open(
        config_path,
        encoding="utf-8",
    ) as file:
        cfg = yaml.safe_load(file)

    privacy_cfg = cfg["privacy"]

    sensitive_encoding_cfg = encoding.sensitive_mappings(
        privacy_cfg["encoding"],
        privacy_cfg["sensitive_attributes"],
    )

    print("Profiling data...")

    bounds, row_count, columns = _profile_dataset(
        cfg,
        sensitive_encoding_cfg,
    )

    diferential_privacy.validate_privacy_config(
        privacy_cfg,
        columns,
    )

    version_name = (
        "v-"
        + datetime.datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )
    )

    print("Creating version...")

    version_path = versioning.create_version(
        version_name=version_name,
        dataset_name=cfg["dataset"]["name"],
    )

    baseline = versioning.baseline_writer(
        version_path,
    )

    dp_writers = {
        epsilon: versioning.dp_writer(
            version_path,
            epsilon,
        )
        for epsilon in privacy_cfg["epsilons"]
    }

    generators = {
        epsilon: np.random.RandomState(
            privacy_cfg["seed"]
        )
        for epsilon in privacy_cfg["epsilons"]
    }

    print("Writing baseline and private versions...")

    processed_rows = 0

    for chunk_index, chunk in enumerate(
        _prepared_chunks(cfg),
        start=1,
    ):
        print(
            f"  processing chunk {chunk_index}...",
            flush=True,
        )

        # Baseline permanece com a representação original.
        baseline.write(chunk)

        # Codifica somente os atributos que serão perturbados.
        encoding.encode_dataframe(
            chunk,
            sensitive_encoding_cfg,
        )

        for epsilon, writer in dp_writers.items():
            private_chunk = diferential_privacy.apply_dp(
                chunk,
                privacy_cfg["sensitive_attributes"],
                epsilon,
                bounds,
                generators[epsilon],
            )

            # Os valores perturbados permanecem numéricos,
            # inclusive com valores fracionários.
            writer.write(private_chunk)

        processed_rows += len(chunk)

        print(
            f"  {processed_rows:,}/{row_count:,} rows written "
            f"(chunk {chunk_index})",
            flush=True,
        )

    metadata = {
        epsilon: diferential_privacy.build_metadata(
            cfg["dataset"]["name"],
            privacy_cfg,
            row_count,
            len(columns),
            bounds,
        )
        for epsilon in privacy_cfg["epsilons"]
    }

    versioning.save_metadata(
        metadata,
        version_path,
    )

    return versioning.finish_version(
        version_path,
    )


if __name__ == "__main__":
    print(run())
    print("\nFinished.")
