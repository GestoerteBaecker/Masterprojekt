import pyodbc
import datetime
import time
import random
import math

def schnitt_berechnen(pruef_pkt, umring):
    schnittpunkte = 0
    anzahl = len(umring)
    for i in range(anzahl):
        punkt1 = umring[i]
        punkt2 = umring[(i + 1) % anzahl]
        if punkt1[0] <= pruef_pkt[0] < punkt2[0] or punkt1[0] >= pruef_pkt[0] > punkt2[0]: #wenn die geogr. Länge des prüfenden Punkts zwischen den zwei betrachteten der Polygonlinie liegt (nur dann Schnitt mit Längengrad möglich
            # der betrachtete Punkt und Nordpol müssen für Schnitt der Geometrie zwischen beiden Punkten jeweils auf zwei Seiten der Ebene der betrachetetn Linie liegen
            y_p_soll = (punkt2[1]-punkt1[1])/(punkt2[0]-punkt1[0])*(pruef_pkt[0]-punkt1[0])+punkt1[1]
            abstand = pruef_pkt[1]-y_p_soll
            if abstand <= 0:
                schnittpunkte += 1
    if schnittpunkte % 2 != 0:
        return True
    else:
        return False

server = "localhost"
uid = "root"
password = "8Bleistift8"
db_database = "`2020-11-07 17:22:45.160446`"  #"`"+str((datetime.datetime.fromtimestamp(time.time())))+"`"
db_table = "Messkampagne"
db_verbindung = pyodbc.connect("DRIVER={MySQL ODBC 8.0 ANSI Driver}; SERVER=" + server + "; UID=" + uid + ";PASSWORD=" + password + ";")
db_zeiger = db_verbindung.cursor()

"""
db_zeiger.execute("CREATE SCHEMA IF NOT EXISTS " + db_database + ";")
connect_table_string = "CREATE TABLE " + db_database + ".`" + db_table + "` (pkt POINT NOT NULL SRID 25832);"
db_zeiger.execute(connect_table_string)
spatial = "CREATE SPATIAL INDEX ind ON " + db_database + ".`" + db_table + "`(pkt);"
punkte = []
for i in range(10000):
    x = str(round(random.uniform(32450000, 32451000), 5))
    y = str(round(random.uniform(5800000, 5801000), 5))
    db_string = "INSERT INTO " + db_database + ".`" + db_table + "` VALUES (ST_pointfromtext('POINT(" + x + " " + y + ")', 25832));"
    db_zeiger.execute(db_string)
    db_zeiger.commit()
    punkte.append([float(x),float(y)])

print("///////////////////////////////////////////////////////////////////////////////////")

test_pkt = [32450172.68375, 5800782.17895]
radius = 100
print("Diese Punkte sollten enthalten sein:")
zeit_start = time.time()
for pkt in punkte:
    abstand = math.sqrt((pkt[0] - test_pkt[0])**2 + (pkt[1] - test_pkt[1])**2)
    if abstand < radius:
        print(pkt)
print("Benötigte Zeit für Abstandberechnung, normal:", time.time() - zeit_start)
print("///////////////////////////////////////////////////////////////////////////////////")
"""
test_pkt = [32450172.68375, 5800782.17895]
radius = 100
zeit_anfang = time.time()
db_text = "SELECT ST_X(pkt), ST_Y(pkt) FROM " + db_database + ".`" + db_table + "` WHERE ST_Distance(" + db_table + ".pkt, ST_pointfromtext('POINT(" + str(test_pkt[0]) + " " + str(test_pkt[1]) + ")', 25832)) < " + str(radius) + ";"
db_zeiger.execute(db_text)
db_zeiger.commit()
for pkt in db_zeiger.fetchall():
    print(pkt[0], pkt[1])
# abfrage über sql und Ausgabe
print("Benötigte für DB-Abfrage:", time.time()-zeit_anfang)
db_verbindung.close()


#   SELECT bla FROM bla WHERE ST_Distance_Sphere(bla_feld, POINT(x y)) < grenzwert;
# SET @poly = ST_GEOMFROMTEXT('POLYGON((x1 y1, xn yn, ..., x1 y1))', 25832);
# SELECT bla FROM bla WHERE ST_CONTAINS(@poly, bla_feld);


