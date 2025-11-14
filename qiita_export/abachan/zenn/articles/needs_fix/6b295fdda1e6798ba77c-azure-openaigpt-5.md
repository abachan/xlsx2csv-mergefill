---
title: "Azure OpenAIでgpt-5をデプロイした時に少し混乱した話"
emoji: "📝"
type: "tech"
topics:[microsoft,azure,openai,gpt-5]
published: false
---

<!-- TODO: 以下を調整 -->
<!-- - Qiita画像ホスティング -->
<!--   * そのままでも表示可。GitHub連携で運用する場合は画像を保存して相対パスへ書換推奨 -->
## はじめに

先日、Azure OpenAI Serviceで **gpt-5** のアクセス申請を行ったところ、無事に利用できるようになりました 🎉  

申請手順については、以前まとめたこちらの記事を参考にしてください。

https://qiita.com/abachan/items/1a537e4b073c7b588bd6

「よし、早速デプロイだ！」と意気込んだのですが……そこで思わぬ“落とし穴”にハマりました。 

この記事では、そのときの体験談を共有します。  

## これまでの環境

これまで **Japan East** に OpenAI リソースを作成し、以下のモデルをまとめて管理していました。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/f679b05b-a5d9-472c-ab8c-da7d59272791.png)

1つのリソース配下にまとめておくと管理がシンプルなので、gpt-5 もここで管理したいと思っていました。  
実際、デプロイ画面に「gpt-5」が選択肢として表示されていたので、Japan Eastでもデプロイできると思い込んでしまいました。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/82df1b11-77bb-4a3d-b7e6-9031b71a7cc6.png)

## 実際にデプロイしてみると…

いざ gpt-5 を Japan East のリソースにデプロイしようとすると、以下のような問題に直面しました。

- **リージョンで Japan East が選べない**  
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/c02529be-ed34-4a61-9f67-7edb65d244d2.png)

- 既存のOpenAIリソース名（GPT-4o や embedding を管理しているリソース）が候補に出てこない  

結果として、**East US 2 に新しいリソースが自動的に作成される**挙動になり、 「え、今までと同じリソース配下にデプロイできないの？」と違和感を覚えました。  

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/97fb5198-07dc-4247-8cff-720e95614416.png)

## 調べてみたら

公式ドキュメント（MS Learn）のモデル対応表を確認すると、理由はシンプルでした。  

- **GPT-5 は Japan East ではまだ提供されていない**  
- 現時点で利用できるのは **East US 2** と **Sweden Central** のみ  

👉 つまり、「Japan East の既存リソース配下に gpt-5 を追加する」という構成は、現状では不可能だったわけです。

https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/models?utm_source=chatgpt.com

## 対応策：オリジナルのリソース名で使いたいなら

自動生成された名前じゃなくて、自分で決めたリソース名で gpt-5 を使いたい場合は、**モデルをデプロイする前にリソースを作成しておく必要があります。**  

手順はシンプルです。  

1. **East US 2 または Sweden Central** を選んで、新しく OpenAI リソースを作成する  
   ![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/a84ec5b2-a710-452f-847d-2a2a94b30ff7.png)

2. そのリソースの中で gpt-5 をデプロイする  
   ![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/b23ee470-7a93-4b7e-a07c-9002009534e3.png)

こうすれば、勝手に作られた名前ではなく、**自分が付けたオリジナルのリソース名配下**で gpt-5 を利用できます。  


## まとめ

- gpt-5 は **Japan East ではまだ利用できない**  
- 現時点で利用可能なリージョンは **East US 2 / Sweden Central**  
- Japan East の既存のOpenAIリソース配下にモデル追加することは不可能  
- **オリジナルのリソース名で運用したいなら、先に利用可能なリージョンでOpenAIリソースを作成してからgpt-5をデプロイする**  

最初は「なんで既存リソース名が出てこないんだ？」と不思議に思いましたが、調べてみれば単純に **Japan East がまだ非対応だった**、というだけのことでした。  

とはいえ、新しくリソースを作らないといけないのは少し面倒…。
一日も早く Japan East でも GPT-5 が使えるようになることを期待しています 😊
