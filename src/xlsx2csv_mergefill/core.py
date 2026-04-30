from __future__ import annotations

import csv
import io
import re
import zipfile
from pathlib import Path
from typing import Optional, Iterable, List, Tuple, Dict

from openpyxl import load_workbook
from openpyxl.cell.cell import Cell, MergedCell
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.workbook.workbook import Workbook

# 型エイリアス
CellCoord = Tuple[int, int]


def _strip_phonetic_from_xlsx(data: io.BytesIO) -> io.BytesIO:
    """xlsx ファイルのワークシート XML からルビ（phonetic）関連の要素・属性を除去する。

    除去対象:
    - <col> 要素の phonetic 属性（ColumnDimension TypeError の原因）
    - <phoneticPr> 要素（列・シートのふりがな表示設定）
    - <rPh> 要素（セル内リッチテキスト中のルビテキスト）
    """
    output = io.BytesIO()
    with zipfile.ZipFile(data, 'r') as zin:
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                content = zin.read(item.filename)
                if item.filename.startswith('xl/worksheets/') and item.filename.endswith('.xml'):
                    # UTF-16 BOM を考慮してデコード（OOXML は UTF-8 か UTF-16 のみ合法）
                    if content.startswith((b'\xff\xfe', b'\xfe\xff')):
                        xml_str = content.decode('utf-16')
                    else:
                        xml_str = content.decode('utf-8')
                    # <col> 要素の phonetic 属性を削除
                    xml_str = re.sub(r'\s+phonetic="[^"]*"', '', xml_str)
                    # <phoneticPr> 要素を削除（自己閉じ形式・開閉タグ形式の両方）
                    xml_str = re.sub(r'<phoneticPr\b[^>]*/>', '', xml_str)
                    xml_str = re.sub(r'<phoneticPr\b[^>]*>.*?</phoneticPr>', '', xml_str, flags=re.DOTALL)
                    # <rPh>...</rPh> ルビテキスト要素を削除
                    xml_str = re.sub(r'<rPh\b[^>]*>.*?</rPh>', '', xml_str, flags=re.DOTALL)
                    content = xml_str.encode('utf-8')
                zout.writestr(item, content)
    output.seek(0)
    return output


def _load_workbook(input_xlsx: Path | str) -> Workbook:
    """Excelワークブックを読み込む共通関数"""
    input_path = Path(input_xlsx)
    if not input_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {input_path}")

    # ファイルを先にメモリへ読み込み、ルビを除去してから openpyxl に渡す。
    # - BytesIO 経由にすることで解析中に例外が発生しても OS のファイルロックが残らない（Windows 対策）
    # - ルビ除去により ColumnDimension phonetic TypeError を根本から回避する
    with open(input_path, 'rb') as f:
        data = io.BytesIO(f.read())

    data = _strip_phonetic_from_xlsx(data)
    try:
        return load_workbook(filename=data, data_only=True, read_only=False)
    finally:
        data.close()


def _sanitize_filename(name: str) -> str:
    """
    ファイル名として使用できない文字を置換する
    """
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip(' .')
    return sanitized if sanitized else "Sheet"


def _get_display_value(cell: Cell | MergedCell | None) -> Optional[object]:
    """Excel 上で実際に見える値だけを返す。"""
    if cell is None or isinstance(cell, MergedCell):
        return None

    value = cell.value
    if value is None:
        return None

    hyperlink = getattr(cell, "hyperlink", None)
    if hyperlink is not None:
        location = getattr(hyperlink, "location", None)
        target = getattr(hyperlink, "target", None)
        # hyperlink 要素のみで定義された内部リンクは、openpyxl が参照先を
        # cell.value に設定することがある。Excel 上ではセル値として表示されないため除外する。
        if target is None and location and value == location:
            return None

    return value


def _build_merged_value_map(ws: Worksheet) -> Dict[CellCoord, Optional[object]]:
    """マージセルの値マップを構築"""
    merged_map: Dict[CellCoord, Optional[object]] = {}
    for mr in ws.merged_cells.ranges:
        # ws.cell() はセルを生成・キャッシュするため、_cells.get() で既存セルのみ参照する
        top_left = ws._cells.get((mr.min_row, mr.min_col))
        top_left_val = _get_display_value(top_left)
        for r in range(mr.min_row, mr.max_row + 1):
            for c in range(mr.min_col, mr.max_col + 1):
                merged_map[(r, c)] = top_left_val
    return merged_map


def _get_cell_value(
    ws: Worksheet,
    merged_map: Dict[CellCoord, Optional[object]],
    r: int,
    c: int,
) -> Optional[object]:
    """マージセルを考慮してセルの値を返す（ws.cell() を避けてメモリを節約）"""
    key = (r, c)
    if key in merged_map:
        return merged_map[key]
    cell = ws._cells.get(key)
    return _get_display_value(cell)


def _effective_bounds(
    ws: Worksheet,
    merged_map: Dict[CellCoord, Optional[object]],
) -> Tuple[int, int]:
    """値（None以外）が存在する最終行・最終列を返す"""
    last_row = last_col = 0
    # 実際に存在するセルのみ走査（ws.cell() での不要なセル生成を回避）
    for (r, c), cell in ws._cells.items():
        val = merged_map.get((r, c), _get_display_value(cell))
        if val is not None:
            last_row = max(last_row, r)
            last_col = max(last_col, c)
    # マージ範囲内の非左上隅セルも考慮
    for (r, c), val in merged_map.items():
        if val is not None:
            last_row = max(last_row, r)
            last_col = max(last_col, c)
    return last_row, last_col


def _iter_rows_values(ws: Worksheet) -> Iterable[List[Optional[object]]]:
    """ワークシートからマージセル展開済みの行データを取得"""
    merged_map = _build_merged_value_map(ws)
    last_row, last_col = _effective_bounds(ws, merged_map)
    for r in range(1, last_row + 1):
        yield [_get_cell_value(ws, merged_map, r, c) for c in range(1, last_col + 1)]


def convert_file(input_xlsx: Path | str, output_csv: Path | str, use_numeric_sheet_names: bool = False, include_hidden_sheets: bool = False) -> int:
    """
    ExcelファイルをCSVファイルに変換する（シンプル版）
    
    Args:
        input_xlsx: 入力Excelファイルのパス
        output_csv: 出力CSVファイルのパス
        use_numeric_sheet_names: Trueの場合、シート名を数値でカウントアップ（0, 1, 2...）
        include_hidden_sheets: Trueの場合、非表示シートも出力する。デフォルトはFalse
    """
    wb = _load_workbook(input_xlsx)
    try:
        sheets = wb.worksheets

        # 非表示シートをフィルタリング（オプションによる）
        if not include_hidden_sheets:
            sheets = [ws for ws in sheets if ws.sheet_state == 'visible']

        if not sheets:
            raise ValueError("ワークシートが見つかりません")

        output_path = Path(output_csv)
        base_output = output_path.with_suffix("")

        for i, ws in enumerate(sheets):
            sheet_identifier = str(i) if use_numeric_sheet_names else _sanitize_filename(ws.title)
            target_path = base_output.parent / f"{base_output.name}_{sheet_identifier}.csv"
            _write_csv(_iter_rows_values(ws), target_path)

        return 0
    finally:
        wb.close()


# Backward-compatible alias (deprecated)
def excel_to_csv(input_xlsx: Path | str, output_csv: Path | str, use_numeric_sheet_names: bool = False, include_hidden_sheets: bool = False) -> int:
    """Deprecated alias for convert_file. Will be removed in a future release."""
    return convert_file(input_xlsx, output_csv, use_numeric_sheet_names, include_hidden_sheets)


def read_sheet(input_xlsx: Path | str) -> List[List[Optional[object]]]:
    """Excelファイルからデータを読み込んでリスト形式で返す（シンプル版）"""
    wb = _load_workbook(input_xlsx)
    try:
        ws = wb.active
        if ws is None:
            if not wb.worksheets:
                raise ValueError("ワークシートが見つかりません")
            ws = wb.worksheets[0]
        return list(_iter_rows_values(ws))
    finally:
        wb.close()


# Backward-compatible alias (deprecated)
def load_excel_data(input_xlsx: Path | str) -> List[List[Optional[object]]]:
    """Deprecated alias for read_sheet. Will be removed in a future release."""
    return read_sheet(input_xlsx)


def read_workbook(input_xlsx: Path | str) -> Dict[str, List[List[Optional[object]]]]:
    """Excelファイルの全シートからデータを読み込んで辞書形式で返す（シンプル版）"""
    wb = _load_workbook(input_xlsx)
    try:
        return {ws.title: list(_iter_rows_values(ws)) for ws in wb.worksheets}
    finally:
        wb.close()


# Backward-compatible alias (deprecated)
def load_all_sheets_data(input_xlsx: Path | str) -> Dict[str, List[List[Optional[object]]]]:
    """Deprecated alias for read_workbook. Will be removed in a future release."""
    return read_workbook(input_xlsx)


def list_sheets(input_xlsx: Path | str) -> List[str]:
    """Excelファイルのシート名一覧を取得"""
    wb = _load_workbook(input_xlsx)
    try:
        return wb.sheetnames
    finally:
        wb.close()


# Backward-compatible alias (deprecated)
def get_sheet_names(input_xlsx: Path | str) -> List[str]:
    """Deprecated alias for list_sheets. Will be removed in a future release."""
    return list_sheets(input_xlsx)


def to_csv_string(data: List[List[Optional[object]]]) -> str:
    """データをCSV文字列に変換（シンプル版）"""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=",", quoting=csv.QUOTE_MINIMAL)
    for row in data:
        writer.writerow(_serialize_row(row))
    return output.getvalue()


# Backward-compatible alias (deprecated)
def data_to_csv_string(data: List[List[Optional[object]]]) -> str:
    """Deprecated alias for to_csv_string. Will be removed in a future release."""
    return to_csv_string(data)


def _serialize_row(row: List[Optional[object]]) -> List[str]:
    """行データを文字列リストに変換（None は空文字列）"""
    return ["" if v is None else str(v) for v in row]


def _write_csv(rows: Iterable[List[Optional[object]]], out_path: Path) -> None:
    """内部用CSV書き込み関数（UTF-8/カンマ区切り固定）"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="UTF-8") as f:
        writer = csv.writer(f, delimiter=",", quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            writer.writerow(_serialize_row(row))
