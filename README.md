# cards

株式会社ハモミライ 社員デジタル名刺表示用リポジトリ。

`data/members.json` を唯一の情報源として、メンバーごとの名刺ページ・vCard(.vcf)・QR コードを
生成し、GitHub Pages で公開します。

公開 URL（Pages 有効化後）:

- メンバー一覧: <https://card.harmonious-future.com/>
- 個人の名刺: `https://card.harmonious-future.com/m/<slug>/`
  - 例: <https://card.harmonious-future.com/m/ryu_kairyu/>

## ディレクトリ構成

```
data/members.json          会社情報・メンバー情報（ここだけ編集する）
tools/build.py             サイトジェネレータ
assets/css/card.css        共通スタイル
index.html                 【生成物】メンバー一覧
m/<slug>/index.html        【生成物】個人の名刺ページ
m/<slug>/<slug>.vcf        【生成物】連絡先ファイル (vCard 3.0)
m/<slug>/qr.png            【生成物】vCard を格納した QR コード
CNAME                      【生成物】カスタムドメイン
```

`index.html` と `m/` 配下は **生成物** です。直接編集せず、`data/members.json` を直して
再生成してください。

## メンバーを追加・更新する

1. `data/members.json` の `members` 配列に項目を追加する。

   ```json
   {
     "slug": "yamada_taro",
     "family_name": "山田",
     "given_name": "太郎",
     "name_jp": "山田 太郎",
     "name_en": "Yamada Taro",
     "phonetic_last": "ヤマダ",
     "phonetic_first": "タロウ",
     "title": "CTO",
     "tagline": "任意のキャッチコピー",
     "tel": "080-0000-0000",
     "email": "yamada_taro@harmonious-future.com"
   }
   ```

   - `slug` が公開 URL（`/m/<slug>/`）とファイル名になります。半角英数字とアンダースコアのみ。
   - `tagline` / `tel` / `email` / `phonetic_*` は省略可能。省略した項目は名刺ページと
     vCard の両方から自動的に外れます。
   - 住所・法人番号・会社 URL は `company` ブロックで全員共通に管理しています。

2. 再生成する。

   ```bash
   pip install -r requirements.txt
   python3 tools/build.py
   ```

3. 生成物ごとコミットする。

   ```bash
   git add data/members.json index.html m
   git commit -m "Add 山田太郎 digital business card"
   git push
   ```

CI（`.github/workflows/pages.yml`）は再生成した結果とコミット済みの生成物が一致するかを
検証します。`data/members.json` だけを変更してコミットするとビルドが失敗します。

## GitHub Pages の有効化

リポジトリの **Settings → Pages** で、公開元を以下のどちらかに設定します。

- **GitHub Actions**（推奨）: `main` への push で `.github/workflows/pages.yml` が
  ビルドとデプロイを行います。
- **Deploy from a branch**: `main` / `/ (root)` を指定します。生成物をコミットしているため
  そのまま配信されます。

`.nojekyll` を置いているため、Jekyll による加工は行われません。

## カスタムドメイン (card.harmonious-future.com)

`harmonious-future.com` は XServer で管理しています。DNS 側と GitHub 側の両方の設定が必要です。

### 1. XServer で DNS レコードを追加

サーバーパネル → **DNSレコード設定** → `harmonious-future.com` を選択 →
**DNSレコード追加** タブで以下を登録します。

| 項目 | 値 |
| --- | --- |
| ホスト名 | `card` |
| 種別 | `CNAME` |
| 内容 | `harmoniousfuture.github.io`（末尾のドットは不要） |
| TTL | `3600` |
| 優先度 | `0` |

- 内容はリポジトリ名を含めません。`harmoniousfuture.github.io/cards` は誤りです。
- 既に `card` のレコード（A / CNAME）がある場合は、重複させず置き換えてください。
- ドメインが XServer 以外のネームサーバーを向いている場合は、そちらの管理画面で
  同じ CNAME レコードを追加します。

### 2. GitHub 側の設定

`CNAME` ファイル（`site.custom_domain` から自動生成）をコミット済みなので、
`main` にマージしてデプロイすれば **Settings → Pages → Custom domain** に
`card.harmonious-future.com` が反映されます。DNS チェックが通ったあと、
同じ画面の **Enforce HTTPS** にチェックを入れてください。

証明書（Let's Encrypt）の発行には DNS 伝播後さらに数分〜1時間ほどかかります。
それまでは HTTPS で証明書エラーが出ますが、待てば解消します。

### 3. 確認

```bash
dig card.harmonious-future.com CNAME +short   # -> harmoniousfuture.github.io.
curl -sI https://card.harmonious-future.com/ | head -1   # -> HTTP/2 200
```

### ドメインを変更・解除する

`data/members.json` の `site.custom_domain` と `site.base_url` を書き換えて再生成します。
`custom_domain` を削除すると `CNAME` も削除され、`<ユーザー名>.github.io/<リポジトリ名>/`
での配信に戻ります。両者が食い違っているとビルドがエラーで止まります。

## QR コードについて

QR コードには vCard の全文（氏名・ふりがな・会社名・役職・電話・メール・URL・住所・法人番号）が
入っています。スマートフォンのカメラでスキャンすると、そのまま連絡先に追加できます。

QR の中身は `data/members.json` の `site.qr_content` で切り替えられます。

- `"vcard"`（既定）: vCard 全文を格納。オフラインでも連絡先を追加できる。
- `"url"`: 名刺ページの URL を格納。QR が大幅に小さくなり読み取りやすいが、
  スキャン後にページ上の「連絡先を保存する」を押す必要がある。

## 動作確認（ローカル）

```bash
python3 tools/build.py
python3 -m http.server 8000
# http://localhost:8000/ を開く
```

`file://` で直接開くと `.vcf` のダウンロードやパス解決が正しく動かないため、
必ず HTTP サーバー経由で確認してください。
