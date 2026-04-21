{{ config(materialized='table') }}

SELECT * FROM {{ ref('tsukuba_emergency_shelter_20241201') }}
