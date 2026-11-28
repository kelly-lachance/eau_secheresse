import duckdb


con = duckdb.connect("data/eau_secheresse.duckdb")

con.sql(""" SELECT COUNT(*) FROM fct_niveaux_journaliers""").show()
