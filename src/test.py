import duckdb


con = duckdb.connect("data/eau_secheresse.duckdb")


con.execute("ATTACH 'data/eau_secheresse.db' AS lite (TYPE sqlite)")

con.sql(
""" WITH manquantes AS (
SELECT code_bss, CAST(date_mesure AS VARCHAR) AS date_txt
FROM lite.raw_chroniques
EXCEPT
SELECT code_bss, CAST(date_mesure AS VARCHAR) AS date_txt
FROM raw_chroniques
)
SELECT code_bss, COUNT(*) AS nombre, MIN(date_txt) AS min_date, MAX(date_txt) AS max_date
FROM manquantes
GROUP BY code_bss
ORDER BY nombre DESC
""").show()
