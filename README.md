# xlsx2csv-mergefill

Excelファイル（.xlsx）を、データ処理に適したCSV形式へ変換するPythonライブラリです。
結合セルの補完や文字コード（cp932）対応により、業務システムへのデータ取り込みを容易にします。

## 特徴

* **結合セルの自動補完** — 結合領域を左上セルの値で埋め、データ欠損を防止
* **cp932形式での出力** — Shift_JIS互換のCSVを出力（業務システムでの互換性重視）
* **複数シートの一括変換** — Excelブック内の全シートを安全なファイル名で自動出力

## インストール

```bash
pip install xlsx2csv-mergefill
```

## 使い方

### 1. ExcelファイルをCSVに一括変換

```python
from xlsx2csv_mergefill import convert_file

convert_file("input.xlsx", "output")
```

→ `output_シート名.csv` という形式で出力されます。

### 2. 特定シートをPythonリストとして読み込み

```python
from xlsx2csv_mergefill import read_sheet

rows = read_sheet("input.xlsx")
```

### 3. 全シートを辞書形式で読み込み

```python
from xlsx2csv_mergefill import read_workbook

data = read_workbook("input.xlsx")
```

**引数**

* `input_path`: 入力Excelファイルのパス
* `output_prefix`: 出力ファイル名のプレフィックス（例：`output` → `output_シート名.csv`）

**戻り値**

* 成功時に `0` を返します。

**例外**

* `FileNotFoundError` などの例外を送出することがあります。

## 制限事項

* 入力形式は `.xlsx` のみ対応（`.xls` 非対応）
* 出力形式は `cp932` / カンマ区切り固定
* 数式セルは計算済みの値として取得されます

## ライセンス

本プロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルをご覧ください。