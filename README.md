# xlsx2csv-mergefill

Excelファイル（.xlsx）を、データ処理に適したCSV形式へ変換するPythonライブラリです。
結合セルの補完対応により、業務システムへのデータ取り込みを容易にします。

## 特徴

* **結合セルの自動補完** — 結合領域を左上セルの値で埋め、データ欠損を防止
* **複数シートの一括変換** — Excelブック内の全シートを安全なファイル名で自動出力

## インストール

```bash
pip install xlsx2csv_mergefill
```

## 使い方

### 1. ExcelファイルをCSVに一括変換

```python
from xlsx2csv_mergefill import convert_file

# 基本的な使用方法
convert_file("input.xlsx", "output")

# シート名を数値にする場合
convert_file("input.xlsx", "output", use_numeric_sheet_names=True)

# 非表示シートも含めて出力する場合
convert_file("input.xlsx", "output", include_hidden_sheets=True)

# 結合セル補完の最大バイト数を変更する場合
convert_file("input.xlsx", "output", merge_fill_max_bytes=200)
```

→ 出力形式：
- 通常：`<指定パスの拡張子なし>_シート名.csv` という形式で同ディレクトリに出力されます
- 数値オプション使用時：`<指定パスの拡張子なし>_0.csv`, `<指定パスの拡張子なし>_1.csv` という形式で出力されます

※ 1シートの場合でも、シート名（または数値）が付与されたファイル名で出力されます。

### 2. 特定シートをPythonリストとして読み込み

```python
from xlsx2csv_mergefill import read_sheet

rows = read_sheet("input.xlsx")

# 結合セル補完の最大バイト数を変更する場合
rows = read_sheet("input.xlsx", merge_fill_max_bytes=200)
```

### 3. 全シートを辞書形式で読み込み

```python
from xlsx2csv_mergefill import read_workbook

data = read_workbook("input.xlsx")

# 結合セル補完の最大バイト数を変更する場合
data = read_workbook("input.xlsx", merge_fill_max_bytes=200)
```

**引数**

* `input_path`: 入力Excelファイルのパス
* `output_path`: 出力先のパス。プレフィックスとして扱われ、`<指定パスの拡張子なし>_シート名.csv` を同ディレクトリに出力します。
* `use_numeric_sheet_names` (オプション): `True` を指定すると、シート名の代わりに数値（0, 1, 2...）を使用してファイル名を生成します。デフォルトは `False`。
* `include_hidden_sheets` (オプション): `True` を指定すると、非表示シートも含めて出力します。デフォルトは `False`（非表示シートは出力しない）。
* `merge_fill_max_bytes` (オプション): 結合セルの左上セル値を結合範囲へ補完する最大バイト数です（UTF-8換算）。デフォルトは `100`。

**戻り値**

* 成功時に `0` を返します。

**例外**

* `FileNotFoundError` などの例外を送出することがあります。

## 制限事項

* 入力形式は `.xlsx` のみ対応（`.xls` 非対応）
* 出力形式は `UTP-8` / カンマ区切り固定
* 数式セルは計算済みの値として取得されます
* 結合セルの左上セル値が UTF-8 換算で `merge_fill_max_bytes + 1` バイト以上の場合、結合範囲への補完は行いません

## ライセンス

本プロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルをご覧ください。
