{{ config(materialized='table') }}

SELECT c.code_bss, c.date_mesure, c.niveau_ngf_m, c.qualification, c.profondeur_m
FROM {{ref('stg_chroniques')}} AS c
JOIN {{ref('dim_stations')}} AS d
ON c.code_bss = d.code_bss
