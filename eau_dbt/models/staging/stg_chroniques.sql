SELECT code_bss, date_mesure, niveau_nappe_eau AS niveau_ngf_m, qualification,profondeur_nappe AS profondeur_m
FROM {{source('brut','raw_chroniques')}}