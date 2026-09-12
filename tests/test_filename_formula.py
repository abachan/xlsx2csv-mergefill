"""ブック名依存式の保存済み値補正に関する回帰テスト。"""

from __future__ import annotations

import csv
import io
import inspect
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from openpyxl import Workbook

from xlsx2csv_mergefill import convert_file, read_sheet, read_workbook
from xlsx2csv_mergefill._workbook import _prepare_xlsx_for_cell_data


_SPREADSHEETML_NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_FILENAME_FORMULA = (
    '=MID(@CELL("filename"),SEARCH("[",@CELL("filename"))+1,'
    'SEARCH("]",@CELL("filename"))-SEARCH("[",@CELL("filename"))-6)'
)


def _replace_formula_cache(xlsx_path: Path, cached_value: str) -> None:
    replacement_path = xlsx_path.with_suffix(".replacement.xlsx")
    cell_tag = f"{{{_SPREADSHEETML_NAMESPACE}}}c"
    value_tag = f"{{{_SPREADSHEETML_NAMESPACE}}}v"

    with zipfile.ZipFile(xlsx_path, "r") as source:
        with zipfile.ZipFile(replacement_path, "w", zipfile.ZIP_DEFLATED) as target:
            for item in source.infolist():
                content = source.read(item)
                if item.filename == "xl/worksheets/sheet1.xml":
                    root = ET.fromstring(content)
                    cell = next(
                        node for node in root.iter(cell_tag) if node.get("r") == "B2"
                    )
                    cell.set("t", "str")
                    value = cell.find(value_tag)
                    if value is None:
                        value = ET.SubElement(cell, value_tag)
                    value.text = cached_value
                    content = ET.tostring(root, encoding="utf-8", xml_declaration=True)
                target.writestr(item, content)
    replacement_path.replace(xlsx_path)


def _create_formula_workbook(path: Path, formula: str, cached_value: str) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "タイトル"
    worksheet["A1"] = "見出し"
    worksheet["B2"] = formula
    workbook.save(path)
    workbook.close()
    _replace_formula_cache(path, cached_value)


def test_reported_stale_filename_cache_is_corrected(tmp_path: Path) -> None:
    current_name = "帳票定義書_R_A01_02_予約キャンセル確認票 ver1.1"
    input_path = tmp_path / f"{current_name}.xlsx"
    _create_formula_workbook(
        input_path,
        _FILENAME_FORMULA,
        "帳票定義書_R_A01_02_予約明細票",
    )

    rows = read_sheet(input_path)

    assert rows[1][1] == current_name


def test_filename_cache_correction_is_used_by_all_read_apis(tmp_path: Path) -> None:
    input_path = tmp_path / "任意のブック名.xlsx"
    _create_formula_workbook(input_path, _FILENAME_FORMULA, "古いブック名")

    assert read_workbook(input_path)["タイトル"][1][1] == "任意のブック名"

    assert convert_file(input_path, tmp_path / "output.csv") == 0
    with (tmp_path / "output_タイトル.csv").open(
        encoding="utf-8", newline=""
    ) as csv_file:
        rows = list(csv.reader(csv_file))
    assert rows[1][1] == "任意のブック名"


def test_correction_does_not_modify_input_file(tmp_path: Path) -> None:
    input_path = tmp_path / "現在名.xlsx"
    _create_formula_workbook(input_path, _FILENAME_FORMULA, "旧名")
    original_bytes = input_path.read_bytes()

    assert read_sheet(input_path)[1][1] == "現在名"
    assert input_path.read_bytes() == original_bytes


def test_current_filename_cache_does_not_recompress_package(tmp_path: Path) -> None:
    input_path = tmp_path / "現在名.xlsx"
    _create_formula_workbook(input_path, _FILENAME_FORMULA, "現在名")
    source = io.BytesIO(input_path.read_bytes())

    prepared = _prepare_xlsx_for_cell_data(source, input_path.name)

    assert prepared is source
    assert prepared.tell() == 0
    prepared.close()


def test_sequential_reads_do_not_share_another_workbook_name(tmp_path: Path) -> None:
    first_path = tmp_path / "一つ目.xlsx"
    second_path = tmp_path / "二つ目.xlsx"
    _create_formula_workbook(first_path, _FILENAME_FORMULA, "共通の古い値")
    _create_formula_workbook(second_path, _FILENAME_FORMULA, "共通の古い値")

    assert read_sheet(first_path)[1][1] == "一つ目"
    assert read_sheet(second_path)[1][1] == "二つ目"
    assert read_sheet(first_path)[1][1] == "一つ目"


def test_same_sheet_reference_in_cell_filename_is_supported(tmp_path: Path) -> None:
    input_path = tmp_path / "参照あり.xlsx"
    formula = _FILENAME_FORMULA.replace(
        'CELL("filename")',
        'CELL("filename",$A$1)',
    )
    _create_formula_workbook(input_path, formula, "古い値")

    assert read_sheet(input_path)[1][1] == "参照あり"


def test_single_wrapper_in_cell_filename_is_supported(tmp_path: Path) -> None:
    input_path = tmp_path / "暗黙交差.xlsx"
    formula = _FILENAME_FORMULA.replace(
        '@CELL("filename")',
        '_xlfn.SINGLE(CELL("filename"))',
    )
    _create_formula_workbook(input_path, formula, "古い値")

    assert read_sheet(input_path)[1][1] == "暗黙交差"


def test_unrelated_formula_keeps_its_saved_value(tmp_path: Path) -> None:
    input_path = tmp_path / "ordinary.xlsx"
    _create_formula_workbook(input_path, "=1+1", "保存済みの値")

    assert read_sheet(input_path)[1][1] == "保存済みの値"


def test_context_dependent_filename_formula_keeps_saved_value(tmp_path: Path) -> None:
    input_path = tmp_path / "current.xlsx"
    _create_formula_workbook(input_path, '=CELL("filename")', "保存済みのフルパス")

    assert read_sheet(input_path)[1][1] == "保存済みのフルパス"


def test_unsupported_external_function_is_never_evaluated(tmp_path: Path) -> None:
    input_path = tmp_path / "current.xlsx"
    _create_formula_workbook(
        input_path,
        '=WEBSERVICE(CELL("filename"))',
        "保存済みの値",
    )

    assert read_sheet(input_path)[1][1] == "保存済みの値"


def test_public_api_has_no_formula_recalculator_parameter() -> None:
    for function in (convert_file, read_sheet, read_workbook):
        assert "formula_recalculator" not in inspect.signature(function).parameters


def test_normal_use_never_discovers_or_starts_external_programs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    input_path = tmp_path / "ordinary.xlsx"
    _create_formula_workbook(input_path, "=1+1", "2")

    def unexpected_call(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("external program access is prohibited")

    monkeypatch.setattr(shutil, "which", unexpected_call)
    monkeypatch.setattr(subprocess, "run", unexpected_call)

    assert read_sheet(input_path)[1][1] == "2"
