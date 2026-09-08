import json
import os
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


class VersioningError(Exception):
    pass


class ParquetDatasetWriter:
    """Grava chunks consecutivos em um único arquivo Parquet."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._writer = None
        self._schema = None

    def write(self, df: pd.DataFrame) -> None:
        if df.empty:
            return

        table = pa.Table.from_pandas(
            df,
            preserve_index=False
        )

        if self._writer is None:
            self._schema = table.schema

            self.path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            self._writer = pq.ParquetWriter(
                self.path,
                self._schema
            )

        elif table.schema != self._schema:
            raise VersioningError(
                "O schema do chunk é diferente do schema "
                "dos chunks anteriores."
            )

        self._writer.write_table(table)

    def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            self._writer = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def create_version(
    base_dir: str = "datasets",
    version_name: str = "v-YYYY-MM-DD_HH-MM-SS",
    dataset_name: str = ""
) -> Path:

    version_path = Path(base_dir) / f"{dataset_name} - {version_name}"

    version_path.mkdir(
        parents=True,
        exist_ok=False
    )

    return version_path


def baseline_writer(version_path: Path) -> ParquetDatasetWriter:
    return ParquetDatasetWriter(
        Path(version_path) / "baseline.parquet"
    )


def dp_writer(
    version_path: Path,
    epsilon: float
) -> ParquetDatasetWriter:

    return ParquetDatasetWriter(
        Path(version_path) / f"dp_eps_{epsilon}.parquet"
    )


def save_metadata(
    metadata: dict,
    version_path: Path
) -> None:

    with (Path(version_path) / "metadata.json").open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
            ensure_ascii=False
        )


def finish_version(version_path: Path) -> dict:
    version_path = Path(version_path)

    return {
        "version": version_path.name,
        "path": str(version_path),
        "files": sorted(os.listdir(version_path)),
    }