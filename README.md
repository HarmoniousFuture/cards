# cards

株式会社ハモミライ 社員デジタル名刺表示用リポジトリ。

`data/members.json` を唯一の情報源として、メンバーごとの名刺ページ・vCard(.vcf)・QR コードを
生成し、GitHub Pages で公開します。

公開 URL（Pages 有効化後）:

- メンバー一覧: <https://harmoniousfuture.github.io/cards/>
- 個人の名刺: `https://harmoniousfuture.github.io/cards/m/<slug>/`
  - 例: <https://harmoniousfuture.github.io/cards/m/ryu_kairyu/>

## ディレクトリ構成

```
data/members.json          会社情報・メンバー情報（ここだけ編集する）
tools/build.py             サイトジェネレータ
assets/css/card.css        共通スタイル
index.html                 【生成物】メンバー一覧
m/<slug>/index.html        【生成物】個人の名刺ページ
m/<slug>/<slug>.vcf        【生成物】連絡先ファイル (vCard 3.0)
m/<slug>/qr.png            【生成物】vCard を格納した QR コード
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
