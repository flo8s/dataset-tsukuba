{% docs __overview__ %}

# Tsukuba City Open Data

A dataset of statistical data published by Tsukuba city, transformed and organized using dbt.

## Data Sources

- Provider: [Tsukuba City](https://www.city.tsukuba.lg.jp/)
- License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

### Population by Area/Age

- Data format: [Municipal Standard Open Data Set "Population by Area/Age"](https://www.digital.go.jp/resources/open_data/municipal-standard-data-set-test)
- Coverage period: April 2024 – October 2025 (6 time points)

### Designated Emergency Evacuation Sites

- Source page: [つくば市 危機管理課](https://www.city.tsukuba.lg.jp/soshikikarasagasu/shichokoshitsukikikanrika/gyomuannai/1/2/1000608.html)
- Data format: Municipal Standard Open Data Set ("Designated Emergency Evacuation Sites") — derived from the city's 4-column CSV and enriched with geocoded lat/lon via the normalize-japanese-addresses library
- Coverage: snapshot as of December 2024 (11 sites)

## Model Structure

### raw: Raw Data Ingestion

Ingests each source CSV with column names preserved in Japanese.

Population (Shift_JIS CSV read directly by URL):

| Model | Time Point |
|---|---|
| `raw_tsukuba_population_20240401` | April 1, 2024 |
| `raw_tsukuba_population_20240501` | May 1, 2024 |
| `raw_tsukuba_population_20241001` | October 1, 2024 |
| `raw_tsukuba_population_20250401` | April 1, 2025 |
| `raw_tsukuba_population_20250501` | May 1, 2025 |
| `raw_tsukuba_population_20251001` | October 1, 2025 |

Emergency Shelter (dbt seed, ODF-formatted CSV):

| Model | Time Point |
|---|---|
| `raw_tsukuba_emergency_shelter_20241201` | December 2024 |

### stg: Normalization

Population: UNPIVOTs raw data for each time point into a long format with one row per sex and age group.
Emergency Shelter: renames Japanese columns to English snake_case, converts disaster type flags to BOOLEAN, and normalizes empty strings to NULL.

### mart: Public Tables

Views that expose the latest normalized data to downstream consumers.

| Model | Description |
|---|---|
| `mart_tsukuba_population` | Mart table unifying Tsukuba city population data across all periods |
| `mart_tsukuba_emergency_shelter` | Mart table of Tsukuba city's designated emergency evacuation sites (ODF format) |

## Lineage

Click the blue icon in the bottom right to view the lineage graph.

{% enddocs %}
