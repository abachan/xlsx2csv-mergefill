---
title: "Azure Functionsの専用（App Service）プランでEvent Hubsのトリガーが動作しなかった話と解決策"
emoji: "📝"
type: "tech"
topics:[microsoft,azure,functions,alwayson]
published: false
---

<!-- TODO: 以下を調整 -->
<!-- - Qiita画像ホスティング -->
<!-- - トピック数/形式の調整 -->
<!--   * そのままでも表示可。GitHub連携で運用する場合は画像を保存して相対パスへ書換推奨 -->
<!--   * Zennのtopicsは最大5・半角英数とハイフンのみ。候補: microsoft, azure, functions, alwayson -->
## はじめに

Azure Functionsの専用(App Service)プランでシステムを運用していた際に、**昨日までは正常に動いていたのに、突然動かなくなる**という事象に遭遇しました。

私が構築していたのは、Blob Storageにファイルを置くと自動的に検知され、Event Hubs経由でFunctionsを呼び出してメールを送信する仕組みです。
最初は正常に動いていましたが、ある日突然、ファイルをアップロードしても通知メールが届かなくなりました。

本記事では、そのときの調査過程で分かった原因と解決策を紹介します。

## システム構成

当時利用していたシステムの流れは以下のとおりです。

1. **Blob Storage** にファイルをアップロード
2. **Event Grid** がファイルアップロードを検知
3. **Event Hubs** にイベントを送信
4. **Azure Functions** がイベントを受け取り、メール送信

## 発生した問題
ある日、ユーザーから「ファイルをアップロードしたのに通知メールが届かない」との連絡がありました。調査の結果は以下のとおりです。

| コンポーネント         | 状況                   |
| --------------- | -------------------- |
| Event Grid      | 正常にイベントを検知           |
| Event Hubs      | メッセージを受信済み（メトリクスで確認） |
| Azure Functions | 実行ログなし（呼び出されていない状態）  |

つまり、**Event Hubsまでは処理が流れているのに、Functionsに到達していない**状況でした。

## 調査で判明した原因

日本語のMS公式ドキュメントには以下の記載がありました。

https://learn.microsoft.com/ja-jp/azure/azure-functions/functions-app-settings?utm_source=chatgpt.com#alwayson

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/1c04a7c1-75ff-4aaf-95bc-f3f6e1660f7d.png)

つまり、専用(App Service)プランでは数分間の非アクティブ後にアイドル化し、HTTP以外のトリガー（今回の場合はEvent Hubs）は反応しなくなる仕様であることが分かりました。

## 解決策：alwaysOn を有効化

**「alwaysOn (常時接続)」を有効化**することで、Functionsを常にアクティブに保ち、イベントを確実に処理できるようになりました。

### 方法①：Azure Portal設定手順

1. Azure Portalで対象のFunction Appを開く
2. 左メニューから **「設定」>「構成」** を選択
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/6524d3be-d68b-480a-b201-50cfc980fd57.png)

3. **「全般設定」** タブを開く
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/eaec6b53-a857-46c5-8284-c9e9116db0c0.png)

4. 「常時接続」を **オン** に変更
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/ed754802-fd7b-4e09-b0ed-1a21bdb4d207.png)

5. 保存
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/6d2e5b9f-a662-47ce-af39-49b166c5f4e8.png)

### 方法②：Azure CLI（IaC/自動化向け）
```bash
# alwaysOn を有効化
az functionapp config set \
  --resource-group <リソースグループ名> \
  --name <Functions名> \
  --always-on true
```

この設定を行った後、再びFunctionsが安定して呼び出され、メール送信が復旧しました。

## プランごとの違い

今回の経験を通じて、**Functionsのホスティングプランごとに挙動が異なる**ことを改めて理解しました。

https://learn.microsoft.com/ja-jp/azure/azure-functions/functions-scale?utm_source=chatgpt.com

| ホスティング プラン          | Always On 必要性 | 主な特徴                                               | 典型ユースケース             |
| ------------------- | ------------- | -------------------------------------------------- | -------------------- |
| **従量課金**            | **不要**        | 真のサーバーレス。イベントに応じ自動スケール                             | 不定期イベント、コスト効率重視      |
| **Flex 従量課金**       | **不要**        | Linux 専用。VNet/メモリ選択/スケールの柔軟性                       | 私設ネットワークや大規模スケール     |
| **Premium**         | **不要**        | \*\*常時ウォーム（Always Ready）\*\*でコールドスタート回避、VNet/長時間実行 | 低遅延・高スループット・隔離要件     |
| **専用（App Service）** | **必要**        | Web Apps と同居可。**非アクティブでアイドル化**                     | 既存 App Service 資産の流用 |

## まとめ

* **事象**: 専用(App Service)プランのFunctionsがEvent Hubsからトリガーされなかった
* **原因**: アイドル状態により非HTTPトリガーを受け付けなかった
* **解決策**: 「alwaysOn (常時接続)」を有効化
* **学び**: プラン選定はコストだけでなく、挙動の違いを理解して行うことが重要

専用（App Service）プランは 既存の App Service 資産を流用しやすいため採用しましたが、非アクティブ時にランタイムがアイドル化し、HTTP 以外のトリガーでは起きないという仕様を見落としていました。
同様の構成の方は、Function App の alwaysOn (常時接続)を有効化してください
