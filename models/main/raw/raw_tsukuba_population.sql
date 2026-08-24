{{ config(materialized='table') }}

{# data/population/ 配下のすべての時点をまとめて読む。時点は CSV の
   `調査年月日` 列が持っているので、ファイル名からは復元しない #}
{{ read_population_csv('data/population/082201_population_*.csv') }}
