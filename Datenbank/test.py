import pyodbc

# der Treiber (hier MySQL ODBC 8.0 ANSI Driver) muss unbedingt mit der Version des Python-Interpreters zusammenpassen (32 oder 64 bit)
# nachzugucken bei Windowssuche -> odbc 32 oder 64 bit
# aufgelistetet Treiber über pyodbc.drivers()

# WICHTIG: es gibt nur 2D Punkte, Tiefe muss als separates Attribut/Feld gespeichert werden

verb = pyodbc.connect("DRIVER={MySQL ODBC 8.0 ANSI Driver}; SERVER=localhost; DATABASE=geom; UID=root; PASSWORD=8Bleistift8;")
zeiger = verb.cursor()

#zeiger.execute("select * from world.city order by world.city.Name")

zeiger.execute("SELECT ST_AsText(g) FROM geom.geom;")
print(zeiger.description)
for eintrag in zeiger.fetchall():
    # eintrag ist eine row: zugriff auf column (Feld) über Index (0 ist erstes Feld) oder Name des Feldes (geht hier gerade nicht, weil
    # das Feld ST_AsText(g) und nicht g heißt)
    koords = [float(koord) for koord in eintrag[0][6:-1].split()]
    print(koords[0], koords[1])

# spatial functions: https://dev.mysql.com/doc/refman/5.6/en/spatial-relation-functions-object-shapes.html
	
#zeiger.execute("SELECT * FROM geom.test;")
"""
#Beschreibung der Curser.description:
column name (or alias, if specified in the SQL)
type code
display size (pyodbc does not set this value)
internal size (in bytes)
precision
scale
nullable (True/False)
print(zeiger.description)
for eintrag in zeiger.fetchall():
    # eintrag ist eine row: zugriff auf column (Feld) über Index (0 ist erstes Feld) oder Name des Feldes (geht hier gerade nicht)
    print(eintrag[0])"""