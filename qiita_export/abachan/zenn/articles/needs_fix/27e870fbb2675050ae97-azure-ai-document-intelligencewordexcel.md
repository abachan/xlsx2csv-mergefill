---
title: "Azure AI Document Intelligenceの前処理：Word/Excelのルビ（ふりがな）を除去する"
emoji: "📝"
type: "tech"
topics:[python,windows,azure,documentintelligence]
published: false
---

<!-- TODO: 以下を調整 -->
<!-- - トピック数/形式の調整 -->
<!--   * Zennのtopicsは最大5・半角英数とハイフンのみ。候補: python, windows, azure, documentintelligence -->
## はじめに
Azure AI Document Intelligence は、ドキュメントからテキストや表などの構造を機械可読な形で抽出できる強力なサービスです。レイアウト（テキスト・表・チェックボックス等）の抽出に対応し、OCRと深層学習を組み合わせて文書構造を取り出せます。

https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/layout?view=doc-intel-4.0.0&utm_source=chatgpt.com&tabs=rest%2Csample-code

一方で、Officeドキュメントに含まれるルビ（ふりがな）が、そのまま抽出テキストに連結され、**後段の検索（Azure AI Search等）でノイズ**になることがあります。本稿では、この問題に対して新規作成・公開した Python ライブラリ **`office_ruby_remover`** を用いた前処理のアプローチを解説します。

## 背景：なぜルビがノイズになるのか

* **Excelのふりがな**は、セルに付随する読み情報です。OOXML（SpreadsheetML）では *phoneticPr / rPh* などの要素で表現され、VBA/APIの世界では *Phonetics* や `PHONETIC()` 関数でも扱えます。

https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.phoneticproperties?view=openxml-3.0.1&utm_source=chatgpt.com

* **Wordのルビ**は、OOXML（WordprocessingML）で `w:ruby` 要素として格納されます。

https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.phoneticproperties?view=openxml-3.0.1&utm_source=chatgpt.com

これらの“読み”は**人間には有用**ですが、Document Intelligenceに載せると、たとえば「東京」に「トウキョウ」が後続連結された文字列（例: `東京トウキョウ`）として取り込まれ、**Azure AI Searchを利用した検索語との一致判定やスコアリングに悪影響**となる場合があります（リコール/適合率の低下、意図しないヒットの増加など）。

> 例：Document IntelligenceのJSON出力（観測例）

```json
{
  "content": "日本の首都は東京トウキョウです。",
  "spans": [...]
}
```

※この連結挙動は筆者の実観測に基づくものであり、仕様として明記されていない点は留意ください（Document Intelligenceはレイアウト/テキストを構造化抽出するAPI群を提供）。

https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/layout?view=doc-intel-4.0.0&utm_source=chatgpt.com&tabs=rest%2Csample-code

## 解決策：Pythonライブラリ「office-ruby-remover」の開発

この問題に対処するため、Document Intelligenceへのアップロード前処理として、Word (`.docx`) と Excel (`.xlsx`) ファイルからルビ情報をプログラムで除去するPythonライブラリ **`office-ruby-remover`** を開発し、公開しました。

https://github.com/abachan/office-ruby-remover

**スターをいただけるととても励みになります:grinning:**


このライブラリを利用することで、Document Intelligenceが処理するドキュメントからルビ情報を事前に取り除き、よりクリーンなテキストデータを抽出させることが可能になります。

`PyPIへの公開が初めてだったので、Kenta Nakamura氏 (@c60evaporator) が公開されている以下の記事を参考にさせていただきました。非常に有益な情報に感謝いたします。`

https://qiita.com/c60evaporator/items/e1ecccab07a607487dcf

## 実証：ライブラリ適用による出力結果の比較

`office-ruby-remover` を用いた前処理の効果を、Document Intelligenceの出力結果で比較します。

**1. 前処理の実行**

まず、以下のPythonコードで対象ファイルのルビを除去します。

```python
import pathlib
from office_ruby_remover import remove_excel_ruby, remove_word_ruby

in_dir = pathlib.Path("in_docs")
out_dir = pathlib.Path("out_docs")
out_dir.mkdir(exist_ok=True)

for p in in_dir.glob("**/*"):
    if p.suffix.lower() == ".xlsx":
        remove_excel_ruby(p, out_dir / p.name, overwrite=True)
    elif p.suffix.lower() == ".docx":
        remove_word_ruby(p, out_dir / p.name, overwrite=True)
```

**2. 出力結果の比較**

  * **Before（前処理なし）**

    ```json
    {
      "content": "日本の首都は東京トウキョウです。",
      "spans": [...]
    }
    ```

  * **After（前処理あり）**

    ```json
    {
      "content": "日本の首都は東京です。",
      "spans": [...]
    }
    ```

前処理を施したファイルをDocument Intelligenceで処理することで、ルビ情報が除去された純粋なテキストデータのみを抽出できました。これにより、Azure AI Searchにおける検索ノイズの問題を未然に防ぐことができます。

## まとめ

* **Officeのルビ/ふりがな**は、人に優しい一方で**検索インデックスにはノイズ**になり得ます。
* **`office_ruby_remover`** で**前処理除去**することで、**抽出テキストをクリーン化**し、**検索精度やスコアの安定性**に寄与します。
* ルビ自体が価値のある場面では、**本文と読みを分離保管**し、**用途に応じて使い分け**る設計が安全です。

本ライブラリが、Officeドキュメントを扱う皆さまの**前処理品質向上**の一助になれば幸いです。
