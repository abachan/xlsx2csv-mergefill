# xlsx2csv-mergefill

Excelファイル（.xlsx）を、データ処理に適したCSV形式へ変換するPythonライブラリです。
結合セルの補完対応により、業務システムへのデータ取り込みを容易にします。

## 特徴

* **結合セルの自動補完** — 結合領域を左上セルの値で埋め、データ欠損を防止
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

→ 複数シートの場合は `<指定パスの拡張子なし>_シート名.csv` という形式で同ディレクトリに複数出力されます。単一シートの場合は第2引数で指定したパスに1ファイルをそのまま出力します（拡張子の自動付与は行いません）。

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
* `output_path`: 出力先のパス。複数シートの場合はプレフィックスとして扱われ、`<指定パスの拡張子なし>_シート名.csv` を同ディレクトリに出力します。単一シートの場合はこのパスにそのまま出力します（例：`out.csv` を指定すると `out.csv` を出力）。

**戻り値**

* 成功時に `0` を返します。

**例外**

* `FileNotFoundError` などの例外を送出することがあります。

## 制限事項

* 入力形式は `.xlsx` のみ対応（`.xls` 非対応）
* 出力形式は `UTP-8` / カンマ区切り固定
* 数式セルは計算済みの値として取得されます

## ライセンス

本プロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルをご覧ください。