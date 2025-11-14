---
title: "Gitで削除したブランチがVisual Studioに表示される問題の解決法"
emoji: "📝"
type: "tech"
topics:[git,visualstudio]
published: false
---

<!-- TODO: 以下を調整 -->
<!-- - Qiita画像ホスティング -->
<!-- - トピック数/形式の調整 -->
<!--   * そのままでも表示可。GitHub連携で運用する場合は画像を保存して相対パスへ書換推奨 -->
<!--   * Zennのtopicsは最大5・半角英数とハイフンのみ。候補: git, visualstudio -->
# はじめに
Gitを利用している開発者の中には、リモート上で削除したブランチがVisual Studio上に残ってしまうという現象を経験したことがある方もいるでしょう。この問題は、特に複数のブランチを扱う大規模プロジェクトでは見逃しがちな場合があり、影響を受けることが多いです。今回は、この問題の事象、原因、および解決策を詳しく説明します。

# 事象
Git上で削除したブランチがVisual Studioに表示され続ける。

# 原因
Visual Studio上の設定により、フェッチ中にリモートブランチが自動的に取り除かれないためです。

# 対策
Visual Studioの設定を変更し、「フェッチ中にリモートブランチを取り除く」オプションを有効にすることで、この問題を解決できます。

# 手順
(1) Visual Studioを起動し、メニューから「項目 > Git > 設定」を選択します。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/635fc27a-f334-5bfe-3eff-778e1588b57b.png)

(2)「リソース管理 > Gitグローバル設定」に移動し、「フェッチ中にリモートブランチを取り除く」プルダウンリストを「True」に変更します。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/7339014b-cc2d-c057-279d-d0185d45b89c.png)

# まとめ
Git上で削除したブランチがVisual Studioに表示される問題を解決するためには、Visual Studioの「フェッチ中にリモートブランチを取り除く」設定を有効にすることが重要です。この設定を行うことで、リモートブランチが正しく管理され、開発作業の効率が向上します。今回の手順を参考にし、適切に設定を変更してみてください。

# 参考記事:
https://learn.microsoft.com/ja-jp/visualstudio/version-control/git-settings?view=vs-2019

