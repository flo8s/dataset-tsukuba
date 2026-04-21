"""つくば市 指定緊急避難場所CSV → 自治体標準ODF形式 変換スクリプト。

つくば市が公開している 4 列の指定緊急避難場所 CSV を、
デジタル庁「推奨データセット（指定緊急避難場所）」の ODF 形式に整形する。

住所正規化とジオコーディングは normalize-japanese-addresses + Geolonia v2 API を利用。

依存 (optional):
    uv sync --extra convert

使い方:
    uv run python scripts/convert_shelter.py \\
        https://www.city.tsukuba.lg.jp/soshikikarasagasu/shichokoshitsukikikanrika/gyomuannai/1/2/1000608.html \\
        seeds/tsukuba_emergency_shelter_20241201.csv
"""

import csv
import json
import re
import sys
import tempfile
import urllib.parse
import urllib.request

from normalize_japanese_addresses import normalize

TSUKUBA_CODE = "082201"

ODF_HEADERS = [
    "全国地方公共団体コード", "ID", "名称", "名称_カナ", "名称_英字",
    "所在地_全国地方公共団体コード", "町字ID", "所在地_連結表記",
    "所在地_都道府県", "所在地_市区町村", "所在地_町字", "所在地_番地以下",
    "建物名等(方書)", "緯度", "経度", "標高",
    "電話番号", "内線番号", "連絡先メールアドレス", "連絡先FormURL",
    "連絡先備考（その他、SNSなど）", "郵便番号", "市区町村コード", "地方公共団体名",
    "災害種別_洪水", "災害種別_崖崩れ、土石流及び地滑り", "災害種別_高潮",
    "災害種別_地震", "災害種別_津波", "災害種別_大規模な火事",
    "災害種別_内水氾濫", "災害種別_火山現象",
    "指定避難所との重複", "想定収容人数", "対象となる町会・自治会",
    "URL", "画像", "画像_ライセンス", "備考",
]


def fetch(url, headers=None):
    h = {"User-Agent": "TsukubaODFConverter/1.0", **(headers or {})}
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def fetch_json(url):
    return json.loads(fetch(url).decode())


def resolve_csv_url(url):
    """つくば市ページURLからCSVリンクを自動検出。直接CSVなら素通し。"""
    if url.lower().endswith(".csv"):
        return url

    print(f"ページからCSVリンクを検出中: {url}")
    html = fetch(url).decode("utf-8", errors="replace")
    csv_links = re.findall(r'href=["\']([^"\']*\.csv)["\']', html, re.IGNORECASE)
    if not csv_links:
        raise ValueError(f"CSVリンクが見つかりません: {url}")

    csv_url = csv_links[0]
    if csv_url.startswith("//"):
        csv_url = "https:" + csv_url
    elif csv_url.startswith("/"):
        parsed = urllib.parse.urlparse(url)
        csv_url = f"{parsed.scheme}://{parsed.netloc}{csv_url}"

    print(f"  → CSV検出: {csv_url}")
    return csv_url


def download_csv(url):
    print(f"ダウンロード: {url}")
    data = fetch(url)
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    tmp.write(data)
    tmp.close()
    print(f"  → {tmp.name} ({len(data)} bytes)")
    return tmp.name


def parse_tsukuba_csv(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    header_idx = next(
        (i for i, r in enumerate(rows) if len(r) >= 2 and r[0].strip() == "No."),
        None,
    )
    if header_idx is None:
        raise ValueError("ヘッダ行が見つかりません")

    return [
        {
            "no": r[0].strip(),
            "name": r[1].strip(),
            "address": r[2].strip() if len(r) > 2 else "",
            "note": r[3].strip() if len(r) > 3 else "",
        }
        for r in rows[header_idx + 1:]
        if r and r[0].strip().isdigit()
    ]


def normalize_address(address):
    r = normalize(address)
    return {
        "pref": r.get("pref", ""),
        "city": r.get("city", ""),
        "town": r.get("town", ""),
        "addr": r.get("addr", ""),
        "lat": str(r["lat"]) if r.get("lat") else "",
        "lng": str(r["lng"]) if r.get("lng") else "",
        "level": r.get("level", 0),
    }


def to_odf_row(facility, norm, page_url):
    full_addr = f"{norm['pref']}{norm['city']}{norm['town']}{norm['addr']}"

    # 高潮・津波・火山現象はつくば市（内陸）では対象外として "0" を明示。
    # 他の災害種別は元データに情報がないため空欄のまま。
    return {
        "全国地方公共団体コード": TSUKUBA_CODE,
        "ID": f"{TSUKUBA_CODE}-shelter-{facility['no'].zfill(4)}",
        "名称": facility["name"],
        "名称_カナ": "",
        "名称_英字": "",
        "所在地_全国地方公共団体コード": TSUKUBA_CODE,
        "町字ID": "",
        "所在地_連結表記": full_addr,
        "所在地_都道府県": norm["pref"],
        "所在地_市区町村": norm["city"],
        "所在地_町字": norm["town"],
        "所在地_番地以下": norm["addr"],
        "建物名等(方書)": "",
        "緯度": norm["lat"],
        "経度": norm["lng"],
        "標高": "",
        "電話番号": "",
        "内線番号": "",
        "連絡先メールアドレス": "",
        "連絡先FormURL": "",
        "連絡先備考（その他、SNSなど）": "",
        "郵便番号": "",
        "市区町村コード": TSUKUBA_CODE,
        "地方公共団体名": f"{norm['pref']}{norm['city']}",
        "災害種別_洪水": "",
        "災害種別_崖崩れ、土石流及び地滑り": "",
        "災害種別_高潮": "0",
        "災害種別_地震": "",
        "災害種別_津波": "0",
        "災害種別_大規模な火事": "",
        "災害種別_内水氾濫": "",
        "災害種別_火山現象": "0",
        "指定避難所との重複": "",
        "想定収容人数": "",
        "対象となる町会・自治会": "",
        "URL": page_url,
        "画像": "",
        "画像_ライセンス": "",
        "備考": facility["note"],
    }


def write_odf_csv(rows, output_path):
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ODF_HEADERS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"出力: {output_path} ({len(rows)} 行)")


def convert(input_source, output_csv):
    page_url = input_source if input_source.startswith("http") else ""
    if input_source.startswith("http"):
        csv_url = resolve_csv_url(input_source)
        input_csv = download_csv(csv_url)
    else:
        input_csv = input_source

    facilities = parse_tsukuba_csv(input_csv)
    print(f"読み込み: {len(facilities)} 施設")

    def process(f):
        print(f"  正規化: {f['name']} ({f['address']})")
        norm = normalize_address(f["address"])
        geo = "✓" if norm["lat"] else "✗"
        print(f"    → L{norm['level']} {geo} town={norm['town']} addr={norm['addr']}")
        return to_odf_row(f, norm, page_url)

    odf_rows = list(map(process, facilities))

    geo_ok = sum(1 for r in odf_rows if r["緯度"])
    print(f"\nジオコーディング: {geo_ok}/{len(odf_rows)} 成功")

    write_odf_csv(odf_rows, output_csv)
    return odf_rows


if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else (
        "https://www.city.tsukuba.lg.jp/soshikikarasagasu/"
        "shichokoshitsukikikanrika/gyomuannai/1/2/1000608.html"
    )
    output = sys.argv[2] if len(sys.argv) > 2 else \
        "seeds/tsukuba_emergency_shelter_20241201.csv"
    convert(source, output)
