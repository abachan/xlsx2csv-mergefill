---
title: "Azure OpenAI Serviceでgpt-5を利用するためのアクセス申請手順"
emoji: "📝"
type: "tech"
topics:[microsoft,azure,openai,gpt-5]
published: false
---

<!-- TODO: 以下を調整 -->
<!-- - Qiita画像ホスティング -->
<!--   * そのままでも表示可。GitHub連携で運用する場合は画像を保存して相対パスへ書換推奨 -->

## はじめに


Azure OpenAI Serviceに、ついに **gpt-5** が追加されました。  
ただし、利用するには **事前のアクセス申請** が必要です。  

本記事では、私が実際に申請を行った際の流れを **図解つきで整理** しました。備忘録としてだけでなく、これから申請される方の参考になれば幸いです。  


## 申請が必要なモデル一覧

今回の申請フォームでは、以下のモデルが対象となっています。

- `gpt-5`  
- `o3`  
- `Model Router`  
- `o3-pro`  
- `deep research`  
- `gpt-image-1`  

需要が非常に高いため、申請後は **ウェイティングリスト** に登録される場合があります。 

## 申請前の注意点

以下のケースでは申請が却下されると明記されています。  

- **無効なAzureサブスクリプションIDを提出した場合**  
- **個人用メールアドレス（例: `@gmail.com`, `@yahoo.com` など）で申請した場合**  

つまり、必須となるのは以下の2点です。  

- **有効なサブスクリプションID**  
- **組織のメールアドレス**  

👉 個人利用のつもりで申請すると弾かれるので注意が必要です。

## アクセス申請の手順

### 1. モデルから`gpt-5`を選択後、`アクセスの要求`リンクをクリックします。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/dc4c6328-c0b3-464a-be9e-b0121ea1f1b8.png)

### 2. 申請フォームに、以下を入力します。

#### 2-1. 氏名の入力 (`First Name` / `Last Name`)

- `Your First Name`: **名** を入力します。
- `Your Last Name`: **姓** を入力します。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/0b2a805b-8480-413f-a4e2-b90efd219b17.png)

#### 2-2. Azure Subscription IDの入力

- `Please provide your Azure Subscription ID`: Azureの **サブスクリプションID** を入力します。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/f3ef15f7-1be6-46a4-8362-2183f96fe580.png)

#### ▼ Subscription IDの確認方法
Azure Portalの「サブスクリプション」サービスから確認できます。一覧に表示される「Subscription ID」の値をコピーします。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/0252664c-3120-4efa-860e-0134269ce21b.png)

#### 2-3. 会社情報と利用シナリオの入力

- `Your Company Email Address`: **会社のメールアドレス**を入力します。
- `Your Company Name`: **会社名（所属組織名）** を入力します。
- `For what scenario(s) do you plan to use this model?`: **モデルの利用シナリオ**を記述します。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/fe257b96-a454-4536-9861-f62404a06374.png)


#### 2-4. 会社の住所情報の入力

- `Please enter company street address`: **会社住所（番地など）** を入力します。
- `Please enter company city name`: **会社住所（市区町村）** を入力します。
- `Please enter company zip code`: **郵便番号** を入力します。
- `Please enter company country name`: **国名** を入力します。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/aa7dbc99-07f7-43e4-915c-f8992795672c.png)

#### 2-5. 申請者情報の確認、利用規約への同意とアンケート

- `Please confirm this application is for your own company and you are not applying on behalf of your customer.`: **申請が自社向けであること**を確認し、`My own organization` にチェックを入れます。
- `The Azure OpenAI Service is subject to the applicable Azure Legal Terms...`: **利用規約および法的条件を確認・同意**の上、チェックボックスにチェックを入れます。
- `(Optional) ...Please take this quick survey...`: サービス改善のための**任意のアンケート**です。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/3963503/32b90aac-8497-4409-8b74-ca20baf4ef44.png)

### 3. 申請フォームの送信ボタンを押下します。

すべての必須項目を入力後、フォーム下部の送信ボタンを押下して申請は完了です。

## おわりに

以上が **Azure OpenAI Serviceでgpt-5を利用するためのアクセス申請手順** でした。  

特に注意すべきポイントは次の2つです。  

- **有効なAzureサブスクリプションIDを用意すること**  
- **会社ドメインのメールで申請すること**  

これから申請される方の参考になれば幸いです。 
