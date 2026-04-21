{{ config(materialized='view') }}

SELECT * FROM {{ ref('stg_tsukuba_emergency_shelter_20241201') }}
