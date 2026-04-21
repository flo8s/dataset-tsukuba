{{ config(materialized='table') }}

{# つくば市公式サイトが公開している指定緊急避難場所CSV（4列、注記行あり）。
   先頭5行が注記行、次が "No.,施設名,所在地,備考" のヘッダー、データ後ろに空行多数。 #}
WITH source AS (
    SELECT *
    FROM read_csv(
        'https://www.city.tsukuba.lg.jp/material/files/group/4/202412hinannbasyo.csv',
        skip = 5,
        header = true,
        encoding = 'utf-8',
        all_varchar = true,
        null_padding = true,
        ignore_errors = true
    )
)
SELECT
    TRY_CAST("No." AS INTEGER)                       AS no,
    "施設名"                                          AS name,
    "所在地"                                          AS address,
    NULLIF("備考", '')                               AS note
FROM source
WHERE TRY_CAST("No." AS INTEGER) IS NOT NULL
ORDER BY no
