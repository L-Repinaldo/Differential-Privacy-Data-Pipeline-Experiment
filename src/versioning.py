import os
import json
from pathlib import Path


class VersioningError(Exception):
    pass


def save_version(
    baseline_df,
    dp_results,
    metadata,
    base_dir="datasets",
    version_name="v-YYYY-MM-DD_HH-MM-SS"
):
    """
    Salva datasets versionados no formato:

    datasets/
      v-YYYY-MM-DD_HH-MM-SS/
        baseline.csv
        dp_eps_0.1.csv
        dp_eps_1.0.csv
        metadata.json
    """

    version_path = Path(base_dir) / version_name

    # cria diretório se não existir
    version_path.mkdir(parents=True, exist_ok=False)

    # baseline
    baseline_path = version_path / "baseline.csv"
    baseline_df.to_csv(baseline_path, index=False)

    # dp datasets
    for eps, df_dp in dp_results.items():
        fname = f"dp_eps_{eps}.csv"
        df_dp.to_csv(version_path / fname, index=False)

    # metadata
    metadata_path = version_path / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return {
        "version": version_name,
        "path": str(version_path),
        "files": sorted(os.listdir(version_path))
    }
