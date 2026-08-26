"""CSV のファイル名生成・直列化・書き込みを行う内部処理。"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Iterable, List, Optional


def _sanitize_filename(name: str) -> str:
    """ファイル名として使用できない文字を置換する。"""
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", name)
    sanitized = re.sub(r"_+", "_", sanitized)
    sanitized = sanitized.strip(" .")
    return sanitized if sanitized else "Sheet"


def _serialize_row(row: List[Optional[object]]) -> List[str]:
    """行データを文字列リストに変換する。None は空文字列にする。"""
    return ["" if value is None else str(value) for value in row]


def _write_csv(rows: Iterable[List[Optional[object]]], out_path: Path) -> None:
    """UTF-8・カンマ区切りでCSVファイルを書き込む。"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="UTF-8") as output_file:
        writer = csv.writer(output_file, delimiter=",", quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            writer.writerow(_serialize_row(row))


def to_csv_string(data: List[List[Optional[object]]]) -> str:
    """データをCSV文字列に変換する。"""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=",", quoting=csv.QUOTE_MINIMAL)
    for row in data:
        writer.writerow(_serialize_row(row))
    return output.getvalue()
