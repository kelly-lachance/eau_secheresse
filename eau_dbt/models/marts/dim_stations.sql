{{ config(materialized='table') }}

SELECT code_bss,code_commune_insee,date_debut_mesure,date_fin_mesure, nom_commune,x,y,altitude_station,nb_mesures_piezo,code_departement,nom_departement,profondeur_investigation
FROM {{ref('stg_stations')}}
WHERE date_debut_mesure <= '2016-01-01'
AND date_fin_mesure  >= '2026-01-01'
AND nb_mesures_piezo >= 3300