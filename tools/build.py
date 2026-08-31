#!/usr/bin/env python3
"""株式会社ハモミライ デジタル名刺サイト ジェネレータ.

data/members.json を唯一の情報源として、GitHub Pages に配置する静的ファイルを生成する。

生成物:
  index.html                 メンバー一覧
  m/<slug>/index.html        個人の名刺ページ
  m/<slug>/<slug>.vcf        連絡先ファイル (vCard 3.0)
  m/<slug>/qr.png            QR コード

使い方:
  pip install segno
  python3 tools/build.py
"""

from __future__ import annotations

import html
import json
import shutil
import sys
from pathlib import Path

try:
    import segno
except ImportError:  # pragma: no cover - 実行環境の案内
    sys.exit("segno が必要です。`pip install segno` を実行してください。")

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "members.json"
MEMBERS_DIR = ROOT / "m"


def esc(value: str) -> str:
    """HTML 用にエスケープする。"""
    return html.escape(str(value), quote=True)


def vcard_escape(value: str) -> str:
    """vCard の値としてエスケープする (RFC 6350 準拠の最小限)。"""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def build_vcard(member: dict, company: dict) -> str:
    """メンバー情報から vCard 3.0 のテキストを組み立てる。"""
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{vcard_escape(member['family_name'])};{vcard_escape(member['given_name'])};;;",
        f"FN:{vcard_escape(member['name_jp'])}",
    ]
    if member.get("phonetic_last"):
        lines.append(f"X-PHONETIC-LAST-NAME:{vcard_escape(member['phonetic_last'])}")
    if member.get("phonetic_first"):
        lines.append(f"X-PHONETIC-FIRST-NAME:{vcard_escape(member['phonetic_first'])}")
    lines.append(f"ORG:{vcard_escape(company['name'])}")
    if member.get("title"):
        lines.append(f"TITLE:{vcard_escape(member['title'])}")
    if member.get("tel"):
        lines.append(f"TEL;TYPE=CELL,VOICE:{vcard_escape(member['tel'])}")
    if member.get("email"):
        lines.append(f"EMAIL;TYPE=WORK:{vcard_escape(member['email'])}")
    lines.append(f"URL:{vcard_escape(company['url'])}")
    lines.append(
        "ADR;TYPE=WORK:;;"
        f"{vcard_escape(company['address_street'])};"
        f"{vcard_escape(company['address_city'])};"
        f"{vcard_escape(company['address_region'])};"
        f"{vcard_escape(company['postal_code'])};"
        f"{vcard_escape(company['address_country'])}"
    )
    if company.get("corporate_number"):
        lines.append(f"NOTE:法人番号 {vcard_escape(company['corporate_number'])}")
    lines.append("END:VCARD")
    return "\r\n".join(lines) + "\r\n"


def card_page(member: dict, company: dict, site: dict) -> str:
    """個人の名刺ページ HTML を組み立てる。"""
    slug = member["slug"]
    page_title = f"{member['name_jp']}｜{company['name']}"
    description = member.get("tagline") or f"{company['name']} {member.get('title', '')} {member['name_jp']}のデジタル名刺"
    page_url = f"{site['base_url'].rstrip('/')}/m/{slug}/"

    logo_html = "<br>".join(esc(line) for line in company["logo_lines"])
    address_html = "\n".join(
        f'      <span class="label"></span>{esc(line)}<br>' for line in company["address_lines"]
    )

    contact_rows = []
    if member.get("tel"):
        tel_href = member["tel"].replace("-", "")
        contact_rows.append(
            f'      <span class="label">TEL</span><a href="tel:{esc(tel_href)}">{esc(member["tel"])}</a><br>'
        )
    if member.get("email"):
        contact_rows.append(
            f'      <span class="label">Mail</span>'
            f'<a href="mailto:{esc(member["email"])}">{esc(member["email"])}</a><br>'
        )
    contact_rows.append(
        f'      <span class="label">URL</span>'
        f'<a href="{esc(company["url"])}" target="_blank" rel="noopener">{esc(company["url_label"])}</a><br>'
    )
    if company.get("corporate_number"):
        contact_rows.append(
            f'      <span class="label">法人番号</span>{esc(company["corporate_number"])}'
        )

    tagline_html = (
        f'\n      <div class="tagline">{esc(member["tagline"])}</div>' if member.get("tagline") else ""
    )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(page_title)}</title>
<meta name="description" content="{esc(description)}">
<meta property="og:title" content="{esc(page_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="profile">
<meta property="og:url" content="{esc(page_url)}">
<meta name="twitter:card" content="summary">
<link rel="canonical" href="{esc(page_url)}">
<link rel="stylesheet" href="../../assets/css/card.css">
</head>
<body>
  <div class="card">
    <div class="logo">{logo_html}</div>
    <div class="company">{esc(company["name"])}</div>

    <div class="name-block">
      <div class="title-label">{esc(member.get("title", ""))}</div>
      <div class="name-jp">{esc(member["name_jp"])}</div>
      <div class="name-en">{esc(member.get("name_en", ""))}</div>{tagline_html}
    </div>

    <div class="qr-wrap">
      <img src="qr.png" width="210" height="210" alt="{esc(member['name_jp'])}の連絡先QRコード">
    </div>
    <div class="hint">スマホのカメラでスキャン →「連絡先に追加」</div>

    <a class="save-btn" href="{esc(slug)}.vcf" download="{esc(slug)}.vcf">連絡先を保存する</a>
    <div class="save-note">このページを見ている方はこちらから直接保存できます</div>

    <div class="contact">
      <span class="label">住所</span>〒{esc(company["postal_code"])}<br>
{address_html}
{chr(10).join(contact_rows)}
    </div>

    <a class="back-link" href="../../">← メンバー一覧</a>
  </div>
</body>
</html>
"""


def index_page(members: list[dict], company: dict, site: dict) -> str:
    """メンバー一覧ページ HTML を組み立てる。"""
    logo_html = "<br>".join(esc(line) for line in company["logo_lines"])
    items = "\n".join(
        f"""      <li>
        <a class="member-link" href="m/{esc(m["slug"])}/">
          <span class="who">
            <span class="m-title">{esc(m.get("title", ""))}</span>
            <span class="m-name-jp">{esc(m["name_jp"])}</span>
            <span class="m-name-en">{esc(m.get("name_en", ""))}</span>
          </span>
          <span class="chevron" aria-hidden="true">›</span>
        </a>
      </li>"""
        for m in members
    )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(site["title"])}</title>
<meta name="description" content="{esc(site["description"])}">
<meta property="og:title" content="{esc(site["title"])}">
<meta property="og:description" content="{esc(site["description"])}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(site["base_url"].rstrip("/") + "/")}">
<link rel="canonical" href="{esc(site["base_url"].rstrip("/") + "/")}">
<link rel="stylesheet" href="assets/css/card.css">
</head>
<body class="index">
  <div class="directory">
    <div class="head">
      <div class="logo">{logo_html}</div>
      <div class="company">{esc(company["name"])}</div>
      <div class="page-title">DIGITAL BUSINESS CARD</div>
    </div>

    <ul class="member-list">
{items}
    </ul>

    <div class="site-foot">
      〒{esc(company["postal_code"])} {esc(company["address_lines"][0])}<br>
      <a href="{esc(company["url"])}" target="_blank" rel="noopener">{esc(company["url_label"])}</a>
    </div>
  </div>
</body>
</html>
"""


def main() -> int:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    site = data["site"]
    company = data["company"]
    members = data["members"]

    slugs = [m["slug"] for m in members]
    duplicates = {s for s in slugs if slugs.count(s) > 1}
    if duplicates:
        sys.exit(f"slug が重複しています: {', '.join(sorted(duplicates))}")

    # 削除されたメンバーのディレクトリが残らないように作り直す
    if MEMBERS_DIR.exists():
        shutil.rmtree(MEMBERS_DIR)
    MEMBERS_DIR.mkdir(parents=True)

    for member in members:
        slug = member["slug"]
        out_dir = MEMBERS_DIR / slug
        out_dir.mkdir(parents=True, exist_ok=True)

        vcard_text = build_vcard(member, company)
        (out_dir / f"{slug}.vcf").write_text(vcard_text, encoding="utf-8", newline="")

        page_url = f"{site['base_url'].rstrip('/')}/m/{slug}/"
        qr_payload = vcard_text if site.get("qr_content", "vcard") == "vcard" else page_url
        segno.make(qr_payload, error="m").save(
            out_dir / "qr.png", scale=8, border=2, dark="#000000", light="#ffffff"
        )

        (out_dir / "index.html").write_text(
            card_page(member, company, site), encoding="utf-8"
        )
        print(f"生成: m/{slug}/ (index.html, {slug}.vcf, qr.png)")

    (ROOT / "index.html").write_text(index_page(members, company, site), encoding="utf-8")
    print(f"生成: index.html (メンバー {len(members)} 名)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
