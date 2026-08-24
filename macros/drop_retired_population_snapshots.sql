{# 時点別に分かれていた人口モデルの後始末。

   モデルファイルを消しても DuckLake 側のテーブルは残る。放っておくと
   2024〜2025年だけを持つ raw_/stg_ が引ける状態で居座り、最新のつもりで
   古い範囲を読んでしまう。本番のカタログには raw が6テーブル、stg が6ビュー残る。

   raw はテーブル、stg はビューで、DROP TABLE / DROP VIEW は IF EXISTS を付けても
   型が違うとエラーになる。カタログに実際どちらで載っているかを引いてから落とす。

   引き先が duckdb_tables() / duckdb_views() なのは、DuckLake の information_schema が
   カタログを跨いでは見えないため。

   **DROP はデータベース名まで修飾する。** プロファイルの `path` が `:memory:` なので
   接続の既定データベースは `memory` で、DuckLake は別名で ATTACH されている。
   修飾しないと `IF EXISTS` が既定データベース側で空振りし、エラーも出さずに
   1件も落ちない。落とす先は探した先と同じ database_name を使う。

   **本番の sync が1回通ったら、この macro と dbt_project.yml の on-run-start を
   まとめて消してよい。** #}
{% macro drop_retired_population_snapshots() %}
  {% if not execute %}{{ return('') }}{% endif %}

  {% set pattern = '^(raw|stg)_tsukuba_population_[0-9]{8}$' %}
  {% set found = run_query(
      "SELECT database_name, table_name AS name, 'TABLE' AS kind FROM duckdb_tables()"
      ~ "  WHERE database_name = 'tsukuba' AND schema_name = 'main'"
      ~ "    AND regexp_matches(table_name, '" ~ pattern ~ "')"
      ~ " UNION ALL "
      ~ "SELECT database_name, view_name, 'VIEW' FROM duckdb_views()"
      ~ "  WHERE database_name = 'tsukuba' AND schema_name = 'main'"
      ~ "    AND regexp_matches(view_name, '" ~ pattern ~ "')"
  ) %}

  {% for row in found.rows %}
    {% set qualified = '"' ~ row[0] ~ '".main."' ~ row[1] ~ '"' %}
    {% do log('dropping retired ' ~ row[2] ~ ' ' ~ qualified, info=True) %}
    {% do run_query('DROP ' ~ row[2] ~ ' IF EXISTS ' ~ qualified) %}
  {% endfor %}
{% endmacro %}
