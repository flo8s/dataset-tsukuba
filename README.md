## データ出典

[つくば市](https://www.city.tsukuba.lg.jp/)が公開しているオープンデータを整備して提供しています。

## テーブル: mart_tsukuba_population

つくば市内の地区別・性別・年齢階級別の人口データです。複数時点のデータを統合しています。

- lg_code: 全国地方公共団体コード
- area_code / area_name: 地域コード / 地域名
- reference_date: 調査年月日
- sex: 性別（male / female）
- age_group: 年齢階級（0-4, 5-9, ..., 85+）
- population: 人口

## テーブル: mart_tsukuba_emergency_shelter

つくば市の指定緊急避難場所の一覧です。公式 CSV を自治体標準オープンデータセット（ODF）形式に整形し、住所正規化で緯度経度を補完しています。

- shelter_id: 避難場所 ID
- name / address: 名称 / 所在地
- pref / city / town / addr_detail: 正規化後の住所要素
- latitude / longitude: 緯度・経度（Geolonia でジオコーディング）
- flood / landslide / storm_surge / earthquake / tsunami / large_fire / inland_flooding / volcanic: 災害種別の対応フラグ
- url: 出典ページ URL

### 取得元と件数

取得元は市の公式ページに置かれた CSV 1 本で、`sources` にページと CSV の両方を挙げています。

- CSV: https://www.city.tsukuba.lg.jp/material/files/group/4/202412hinannbasyo.csv
- 時点: 2024 年 12 月
- 件数: 11 件（No.1〜11）。CSV は 4 列で、ODF 形式の 39 列へ整形しています

`mart_tsukuba_emergency_shelter` の行数は、この CSV の件数と一致します。件数を根拠に使うときは、
つくば市の指定避難所や、国土地理院の全国データ（`gsi`）に含まれる同名の施設と混ぜないでください。
指定の趣旨も収録項目も別で、件数は一致しません。

### データ更新手順

公式 CSV が更新されたら、`scripts/convert_shelter.py` で seeds を再生成します。

```bash
uv sync --extra convert
uv run python scripts/convert_shelter.py \
    https://www.city.tsukuba.lg.jp/soshikikarasagasu/shichokoshitsukikikanrika/gyomuannai/1/2/1000608.html \
    seeds/tsukuba_emergency_shelter_20241201.csv
```

出力時点のファイル名（`20241201` 部分）は、つくば市公式ページの更新時点に合わせて付けます。

## ライセンス

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
