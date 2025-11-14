---
title: "LDAP設定されたJenkinsでユーザ全員がログインできなくなった場合の対処法"
emoji: "📝"
type: "tech"
topics:[jenkins,ldap]
published: false
---

<!-- TODO: 以下を調整 -->
<!-- - トピック数/形式の調整 -->
<!--   * Zennのtopicsは最大5・半角英数とハイフンのみ。候補: jenkins, ldap -->
# はじめに
Jenkinsにて、LDAP認証設定中に、LDAPの設定を誤るとユーザがログインできなくなることがあります。本記事では、そのような事態に陥った際の対処法について具体的な手順を説明します。

# 事象
LDAPを用いた認証設定が行われたJenkinsで、全ユーザがログインできなくなった。

# 対策
以下の手順を実施することで、LDAP認証を再設定し、ユーザがログインできるようにします。

## 手順
**(1) config.xmlファイルのバックアップを取る**
   - `E:\Jenkins\.jenkins\config.xml` のバックアップを取ります。バックアップは、設定の誤りやデータの損失を防ぐために重要です。

**(2) config.xmlファイルをデスクトップにコピー**
   - `E:\Jenkins\.jenkins\config.xml` をデスクトップにコピーします。

**(3) config.xmlファイルを編集**
   - デスクトップにコピーしたファイルを開きます。
   - `hudson/authorizationStrategy/roleMap type="globalRoles"/role name="Admin"/assignedSIDs/sid` タグ内のIDをLDAP認証でログイン可能な管理者のIDに変更します。

```xml:config.xml
<roleMap type="globalRoles">
  <role name="Admin">
    <assignedSIDs>
      <sid>admin_user_id</sid>
    </assignedSIDs>
  </role>
</roleMap>
```

**(4) 編集したconfig.xmlファイルを上書き**
デスクトップにある編集済みのconfig.xmlファイルを E:\Jenkins\.jenkins にコピーして上書きします。

**(5) Jenkinsのサービスを再起動**
Jenkinsのサービスを再起動します。サービスの再起動は、設定変更を反映させるために必要です。

# まとめ
LDAP設定されたJenkinsにおいて、全ユーザがログインできなくなった場合の対処法について説明しました。主な原因はLDAP認証における設定ミスやLDAPサーバーとの接続問題であり、config.xmlファイルを適切に編集することで解決可能です。定期的なバックアップと設定ファイルの確認を行うことで、障害発生時の迅速な対応が可能となります。

困ったときは、この記事の手順を参考に対応してみてください。設定変更が反映され、ユーザが再びログインできるようになることを願っています。
