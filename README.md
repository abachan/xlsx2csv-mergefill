# xlsx2csv-mergefill

Excelファイル（`.xlsx`）を、データ処理に適したUTF-8のCSVへ変換するPythonライブラリです。結合セルの値を補完し、ブック内の各シートを個別のCSVとして出力します。

## 特徴

- **結合セルの自動補完** — 結合範囲を左上セルの値で補完します。
- **全シートを順番どおりに出力** — ワークシートとグラフシートを、Excelブック内の順番を維持して出力します。
- **複数シートの一括変換** — シート名または連番を付けたCSVをシートごとに生成します。
- **不要オブジェクトを除外** — セルデータの取得に不要な画像、グラフ、図形は読み込み対象から除外します。
- **入力ファイルを変更しない** — 読み込み前処理はメモリ上のコピーに対して行います。

## インストール

```bash
pip install xlsx2csv_mergefill
```

## 使い方

### ExcelファイルをCSVへ一括変換する

```python
from xlsx2csv_mergefill import convert_file

# 基本的な使用方法
convert_file("input.xlsx", "output.csv")

# シート名の代わりに 0, 1, 2... の連番を使用
convert_file("input.xlsx", "output.csv", use_numeric_sheet_names=True)

# 非表示シートも出力
convert_file("input.xlsx", "output.csv", include_hidden_sheets=True)

# 結合セルを補完する値の最大バイト数を変更
convert_file("input.xlsx", "output.csv", merge_fill_max_bytes=200)
```

出力ファイル名は次の形式です。

- 通常：`<出力パスの拡張子なし>_<シート名>.csv`
- `use_numeric_sheet_names=True`：`<出力パスの拡張子なし>_0.csv`、`<出力パスの拡張子なし>_1.csv`、…

1シートだけのブックでも、シート名または連番が付加されます。ファイル名に使用できないシート名の文字は `_` に置換されます。

グラフシートも1シートとして出力・採番されます。ただしグラフシートにはセルデータがないため、生成されるCSVは空ファイルです。例えば `ワークシート → Graph1 → ワークシート` の順に並ぶブックを連番で出力すると、`_0.csv`、空の `_1.csv`、`_2.csv` が生成されます。

デフォルトでは非表示シートを出力しません。`include_hidden_sheets=True` を指定すると非表示シートも出力します。連番は、実際に出力するシートを対象に0から順番に付与されます。

#### 引数

- `input_xlsx`：入力する `.xlsx` ファイルのパス
- `output_csv`：出力先のベースパス。指定した拡張子は取り除かれ、シート識別子と `.csv` が付加されます。
- `use_numeric_sheet_names`：`True` の場合、シート名の代わりに `0, 1, 2...` を使用します。デフォルトは `False` です。
- `include_hidden_sheets`：`True` の場合、非表示シートも出力します。デフォルトは `False` です。
- `merge_fill_max_bytes`：結合セルを補完する値の最大バイト数です。UTF-8換算で判定し、デフォルトは `100` です。

#### 戻り値

正常終了時に `0` を返します。

### アクティブなワークシートをリストとして読み込む

```python
from xlsx2csv_mergefill import read_sheet

rows = read_sheet("input.xlsx")
rows = read_sheet("input.xlsx", merge_fill_max_bytes=200)
```

アクティブシートがグラフシートの場合は、ブック内の先頭ワークシートを読み込みます。ワークシートが存在しない場合は `ValueError` を送出します。

### 全シートを辞書として読み込む

```python
from xlsx2csv_mergefill import read_workbook

data = read_workbook("input.xlsx")
data = read_workbook("input.xlsx", merge_fill_max_bytes=200)
```

キーはシート名、値は行データのリストです。グラフシートはシート順とシート名を維持し、値を空のリスト `[]` として返します。`read_workbook` は非表示シートも含む全シートを返します。

### シート名の一覧を取得する

```python
from xlsx2csv_mergefill import list_sheets

sheet_names = list_sheets("input.xlsx")
```

ワークシートとグラフシートを含む全シート名を、ブック内の順番で返します。

### リストをCSV文字列へ変換する

```python
from xlsx2csv_mergefill import to_csv_string

csv_text = to_csv_string([
    ["名前", "年齢"],
    ["田中", 30],
])
```

`None` は空文字列として出力され、それ以外の値は文字列へ変換されます。

## 結合セルの補完仕様

- 結合範囲の左上セル値を、結合範囲内の全セルへ補完します。
- 左上セル値がUTF-8換算で `merge_fill_max_bytes` バイト以下の場合に補完します。
- `merge_fill_max_bytes + 1` バイト以上の場合は補完せず、左上セルだけに値を残します。
- デフォルトの `merge_fill_max_bytes` は `100` です。

## 画像・グラフ・図形の扱い

このライブラリがCSVへ出力するのはセルデータだけです。画像、埋め込みグラフ、図形はCSVへ出力せず、Excel読み込み時にも解析対象から除外します。これにより、巨大画像やCSV変換に不要な描画オブジェクトが含まれるブックでも、セルデータの変換を継続できます。

グラフシートについてはシートの存在と順番だけを扱い、空のCSVを出力します。グラフの画像化、系列データの展開、図形内テキストの抽出は行いません。

## 文字コードと値

- CSVはUTF-8・カンマ区切りで出力します。BOMは付与しません。
- `None` は空文字列として出力します。
- 数式セルは、Excelファイル内に保存されている計算済みの値を取得します。計算済みの値が保存されていない場合は空になることがあります。
- セル値のないワークシートおよびグラフシートは、0バイトの空CSVになります。

## 例外

- 入力ファイルが存在しない場合は `FileNotFoundError` を送出します。
- 対象となるシートまたはワークシートが存在しない場合は `ValueError` を送出します。
- 破損したXLSXなど、読み込み・出力を継続できない場合は原因となった例外を送出します。

## 制限事項

- 入力形式は `.xlsx` のみ対応し、`.xls` には対応しません。
- CSVはUTF-8・カンマ区切り固定です。
- 画像、グラフ、図形、図形内テキストはCSVへ変換しません。
- グラフシートは空CSVとして出力します。

## 後方互換API

次の旧関数名も利用できますが、将来のバージョンで削除予定です。

- `excel_to_csv` → `convert_file`
- `load_excel_data` → `read_sheet`
- `load_all_sheets_data` → `read_workbook`
- `get_sheet_names` → `list_sheets`
- `data_to_csv_string` → `to_csv_string`

## ライセンス

本プロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)をご覧ください。
