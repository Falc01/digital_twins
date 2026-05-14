from __future__ import annotations

import logging
import os
from typing import Optional
from src.qgis.data.models import ProcessingResult
from src.qgis.logic.reader import RowByRowReader, readings_to_table_data
from src.qgis.data.gpkg_writer import BaseWriter, GpkgWriter

logger = logging.getLogger("qgis_bridge.pipeline")

class ExportPipeline:
    def __init__(
        self,
        reader:  RowByRowReader,
        writers: list[BaseWriter],
    ) -> None:
        self._reader  = reader
        self._writers = writers

    def refresh(
        self,
        table_name: str,
        output_dir: str,
    ) -> tuple[dict[str, str], ProcessingResult]:
        readings, result = self._reader.read_all_valid(table_name)

        if not readings:
            logger.warning(
                "Nenhuma linha válida para '%s' — ficheiros não gerados.",
                table_name,
            )
            return {}, result

        table_data = readings_to_table_data(table_name, readings)

        paths: dict[str, str] = {}
        for writer in self._writers:
            try:
                path = writer.write(table_data, output_dir)
                paths[writer.extension] = path
            except Exception as exc:
                logger.error(
                    "Erro ao escrever %s para '%s': %s",
                    writer.extension, table_name, exc,
                )

        return paths, result

    def refresh_all(
        self,
        output_dir: str,
    ) -> dict[str, tuple[dict[str, str], ProcessingResult]]:
        return {
            name: self.refresh(name, output_dir)
            for name in self._reader.list_tables()
        }

    def exists(self, table_name: str) -> bool:
        return self._reader.exists(table_name)

    def list_tables(self) -> list[str]:
        return self._reader.list_tables()

    def output_paths(self, table_name: str, output_dir: str) -> dict[str, str]:
        return {
            w.extension: os.path.join(output_dir, f"{table_name}{w.extension}")
            for w in self._writers
        }

def build_default_pipeline(
    data_dir:        str,
    lat_hint:        Optional[str]  = None,
    lon_hint:        Optional[str]  = None,
    export_gpkg:     bool           = True,
    gpkg_srid:       int            = 4326,
) -> ExportPipeline:
    reader: RowByRowReader = RowByRowReader(
        data_dir=data_dir,
        lat_hint=lat_hint,
        lon_hint=lon_hint,
    )
    writers: list[BaseWriter] = []
    if export_gpkg:
        writers.append(GpkgWriter(srid=gpkg_srid))

    return ExportPipeline(reader, writers)
