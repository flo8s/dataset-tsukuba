{# 自治体標準オープンデータセット「地域・年齢別人口」のスキーマ定義
   https://www.digital.go.jp/resources/open_data/municipal-standard-data-set-test #}
{% macro read_population_csv(path) %}
select *
from read_csv(
    '{{ path }}',
    header=true,
    {# 取得時に UTF-8 へ揃えている (pipelines/ckan.py の to_utf8)。
       上流は CP932 と UTF-8 が混在していて、片方を指定すると必ずどちらかで落ちる #}
    encoding='utf-8',
    null_padding=true,
    dtypes={
        '全国地方公共団体コード': 'VARCHAR',
        '地域コード': 'VARCHAR',
        '調査年月日': 'DATE',
        '備考': 'VARCHAR'
    }
)
{% endmacro %}
