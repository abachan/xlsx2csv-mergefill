"""Excel ワークブックをセルデータ読取用に安全に読み込む内部処理。"""

from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.workbook.workbook import Workbook


_DRAWING_RELATIONSHIP_SUFFIX = "/drawing"
_SPREADSHEETML_NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def _strip_drawing_relationships(content: bytes) -> bytes:
    """ワークシート等から図・画像・グラフへの関連だけを除去する。"""
    if b"/drawing" not in content:
        return content

    root = ET.fromstring(content)
    removed = False
    for relationship in list(root):
        relationship_type = relationship.get("Type", "")
        if relationship_type.endswith(_DRAWING_RELATIONSHIP_SUFFIX):
            root.remove(relationship)
            removed = True

    if not removed:
        return content
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _repair_chartsheet_custom_views(content: bytes) -> bytes:
    """openpyxl が読み込めない、scale 未指定のグラフシート表示設定を補正する。"""
    if b"customSheetView" not in content:
        return content

    root = ET.fromstring(content)
    changed = False
    custom_view_tag = f"{{{_SPREADSHEETML_NAMESPACE}}}customSheetView"
    for custom_view in root.iter(custom_view_tag):
        if custom_view.get("scale") is None:
            # OOXML 上の既定表示倍率。CSV化するセル値には影響しない。
            custom_view.set("scale", "100")
            changed = True

    if not changed:
        return content
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _prepare_xlsx_for_cell_data(data: io.BytesIO) -> io.BytesIO:
    """セル値の取得を妨げる不要な OOXML 要素・属性を除去する。

    除去対象:
    - <col> 要素の phonetic 属性（ColumnDimension TypeError の原因）
    - <phoneticPr> 要素（列・シートのふりがな表示設定）
    - <rPh> 要素（セル内リッチテキスト中のルビテキスト）
    - ワークシート・グラフシートの drawing 関連（画像・グラフ・図形）

    グラフシートの customSheetView に scale がない場合は、OOXML の既定値で
    補正する。入力ファイル自体は変更せず、openpyxl に渡すメモリ上のコピー
    だけを処理する。
    """
    output = io.BytesIO()
    with zipfile.ZipFile(data, "r") as source:
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
            for item in source.infolist():
                content = source.read(item.filename)
                if item.filename.startswith("xl/worksheets/") and item.filename.endswith(".xml"):
                    content = _strip_phonetic_xml(content)
                elif (
                    item.filename.startswith("xl/worksheets/_rels/")
                    or item.filename.startswith("xl/chartsheets/_rels/")
                ) and item.filename.endswith(".rels"):
                    content = _strip_drawing_relationships(content)
                elif item.filename.startswith("xl/chartsheets/") and item.filename.endswith(".xml"):
                    content = _repair_chartsheet_custom_views(content)
                target.writestr(item, content)

    output.seek(0)
    return output


def _strip_phonetic_from_xlsx(data: io.BytesIO) -> io.BytesIO:
    """互換性のために残す、旧名称の前処理関数。"""
    return _prepare_xlsx_for_cell_data(data)


def _strip_phonetic_xml(content: bytes) -> bytes:
    """ワークシート XML からルビ関連の要素・属性を除去する。"""
    # UTF-16 BOM を考慮してデコード（OOXML は UTF-8 か UTF-16 のみ合法）
    if content.startswith((b"\xff\xfe", b"\xfe\xff")):
        xml_text = content.decode("utf-16")
    else:
        xml_text = content.decode("utf-8")

    xml_text = re.sub(r'\s+phonetic="[^"]*"', "", xml_text)
    xml_text = re.sub(r"<phoneticPr\b[^>]*/>", "", xml_text)
    xml_text = re.sub(
        r"<phoneticPr\b[^>]*>.*?</phoneticPr>",
        "",
        xml_text,
        flags=re.DOTALL,
    )
    xml_text = re.sub(r"<rPh\b[^>]*>.*?</rPh>", "", xml_text, flags=re.DOTALL)
    return xml_text.encode("utf-8")


def _load_workbook(input_xlsx: Path | str) -> Workbook:
    """Excelワークブックを読み込む共通関数。"""
    input_path = Path(input_xlsx)
    if not input_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {input_path}")

    # BytesIO 経由にすることで解析中に例外が発生しても、Windows 上で
    # 入力ファイルのロックが残らないようにする。
    with input_path.open("rb") as input_file:
        data = io.BytesIO(input_file.read())

    data = _prepare_xlsx_for_cell_data(data)
    try:
        return load_workbook(filename=data, data_only=True, read_only=False)
    finally:
        data.close()
