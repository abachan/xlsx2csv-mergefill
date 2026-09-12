"""XLSX読込前処理の回帰テスト。"""

from __future__ import annotations

import io
import zipfile

from openpyxl import Workbook

from xlsx2csv_mergefill._workbook import (
    _prepare_xlsx_for_cell_data,
    _strip_phonetic_from_xlsx,
)


def _create_standard_workbook_bytes() -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet["A1"] = "value"
    output = io.BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def _inject_phonetic_property(data: bytes) -> bytes:
    source_buffer = io.BytesIO(data)
    output_buffer = io.BytesIO()
    with zipfile.ZipFile(source_buffer, "r") as source:
        with zipfile.ZipFile(output_buffer, "w", zipfile.ZIP_DEFLATED) as target:
            for item in source.infolist():
                content = source.read(item)
                if item.filename == "xl/worksheets/sheet1.xml":
                    content = content.replace(
                        b"<sheetData>",
                        b'<phoneticPr fontId="1"/><sheetData>',
                    )
                target.writestr(item, content)
    return output_buffer.getvalue()


def test_unchanged_package_reuses_original_buffer() -> None:
    source = io.BytesIO(_create_standard_workbook_bytes())

    prepared = _prepare_xlsx_for_cell_data(source)

    assert prepared is source
    assert prepared.tell() == 0
    with zipfile.ZipFile(prepared) as package:
        assert "xl/worksheets/sheet1.xml" in package.namelist()


def test_changed_package_uses_copy_and_keeps_source_unchanged() -> None:
    original_bytes = _inject_phonetic_property(_create_standard_workbook_bytes())
    source = io.BytesIO(original_bytes)

    prepared = _prepare_xlsx_for_cell_data(source)

    assert prepared is not source
    assert source.getvalue() == original_bytes
    assert not source.closed
    with zipfile.ZipFile(prepared) as package:
        worksheet_xml = package.read("xl/worksheets/sheet1.xml")
    assert b"phoneticPr" not in worksheet_xml


def test_legacy_preprocessor_name_remains_compatible() -> None:
    source = io.BytesIO(_create_standard_workbook_bytes())

    prepared = _strip_phonetic_from_xlsx(source)

    assert prepared is source
    prepared.close()
