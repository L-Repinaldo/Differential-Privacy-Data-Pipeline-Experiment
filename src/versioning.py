import json
import os
from pathlib import Path

import pandas as pd


class VersioningError(Exception):
    pass


class CsvDatasetWriter:
    """Grava chunks consecutivos em um CSV com um único cabeçalho."""

    def __init__(self, path: Path):
        self.path = path
        self._written = False

    def write(self, df: pd.DataFrame) -> None:
        df.to_csv(self.path, mode="a" if self._written else "w", header=not self._written, index=False)
        self._written = True


def create_version(base_dir: str = "datasets", version_name: str = "v-YYYY-MM-DD_HH-MM-SS", dataset_name: str = "") -> Path:
    version_path = Path(base_dir) / f"{dataset_name} - {version_name}"
    version_path.mkdir(parents=True, exist_ok=False)
    return version_path


def baseline_writer(version_path: Path) -> CsvDatasetWriter:
    return CsvDatasetWriter(Path(version_path) / "baseline.csv")


def dp_writer(version_path: Path, epsilon: float) -> CsvDatasetWriter:
    return CsvDatasetWriter(Path(version_path) / f"dp_eps_{epsilon}.csv")


def save_metadata(metadata: dict, version_path: Path) -> None:
    with (Path(version_path) / "metadata.json").open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, ensure_ascii=False)


def finish_version(version_path: Path) -> dict:
    version_path = Path(version_path)
    return {
        "version": version_path.name,
        "path": str(version_path),
        "files": sorted(os.listdir(version_path)),
    }
