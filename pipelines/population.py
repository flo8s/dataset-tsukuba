"""自治体標準オープンデータセット「地域・年齢別人口」を取得する。

CKAN に平成15年度から令和7年度までの各時点が1ファイルずつ載っている。
どの時点かは CSV の `調査年月日` 列が持っているので、ファイル名からは読まない。
"""

from __future__ import annotations

import logging
from pathlib import Path

from pipelines.ckan import download, search_resources

logger = logging.getLogger("pipelines.population")

QUERY = "地域・年齢別人口"

# 同じ検索語で「行政区別年齢別人口」など別系統も引っかかるので、
# 自治体標準オープンデータセットの命名規則でふるいにかける
FILENAME_PREFIX = "082201_population_"

# 上流が一部しか返さなかったときに、黙って収録期間の短いテーブルを作り直して
# publish してしまうのを止める下限。**この数を下回ったら履歴が消える。**
# 2026-08 時点で69件あり、上流は時点を減らさないので、下回るのは
# 検索の不調かカタログの再編成のとき。そのときは人が見て決める
MIN_EXPECTED_FILES = 60


def download_population(dest: str) -> list[Path]:
    resources = [
        r for r in search_resources(QUERY, "CSV") if r.name.startswith(FILENAME_PREFIX)
    ]
    # 上流は CP932 と UTF-8 が混在している。読み手が1つの encoding を指定できるよう揃える
    paths = download(resources, Path(dest), normalize_encoding=True)

    if len(paths) < MIN_EXPECTED_FILES:
        raise SystemExit(
            f"population: {len(paths)} ファイルしか取れなかった (下限 {MIN_EXPECTED_FILES})。"
            " 上流の検索結果かカタログの構成が変わった可能性がある。"
            " このまま進めると収録期間の短いテーブルで既存の履歴を置き換えてしまう"
        )

    logger.info("population: %d ファイル", len(paths))
    return paths
