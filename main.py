"""つくば市オープンデータのデータパイプライン。

1. population: 地域・年齢別人口を CKAN から取得
2. dbt:        ビルド

取得を毎回やり直すので、上流に新しい時点が増えれば次のビルドで自動的に入る。
モデル側にファイルを足す作業は要らない。
"""

import logging

from dbt.cli.main import dbtRunner

from pipelines.population import download_population

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("pipelines")


def dbt_build():
    dbt = dbtRunner()
    for command in (["deps"], ["seed"], ["run"], ["docs", "generate"]):
        result = dbt.invoke(command)
        if not result.success:
            raise SystemExit(f"dbt {' '.join(command)} failed")


def main():
    logger.info("1/2: population (地域・年齢別人口)")
    download_population("data/population")

    logger.info("2/2: dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
