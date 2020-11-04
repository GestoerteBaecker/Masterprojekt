import pyodbc
import time
import datetime

class Sensor:
    def __init__(self):
        self.db_felder = [("id", "INT"), ("zeitpunkt", "DOUBLE")]

class Echolot(Sensor):
    def __init__(self):
        super().__init__()
        self.db_felder = [("id", "INT"), ("zeitpunkt", "DOUBLE"), ("tiefe1", "DOUBLE"), ("tiefe2", "DOUBLE")]


class GNSS(Sensor):
    def __init__(self):
        super().__init__()
        self.db_felder = [("id", "INT"), ("zeitpunkt", "DOUBLE"), ("punkt", "POINT"), ("HDOP", "DOUBLE"),
                          ("up", "DOUBLE"), ("Qualitaet", "INT")]

def db_verbinden(Sensorliste, Sensornamen):
    db_database = "`"+str((datetime.datetime.fromtimestamp(time.time())))+"`"
    db_table = "Messkampagne"
    db_verbindung = pyodbc.connect("DRIVER={MySQL ODBC 8.0 ANSI Driver}; SERVER=localhost; UID=root; PASSWORD=8Bleistift8;")
    db_zeiger = db_verbindung.cursor()

    # Anlegen einer Datenbank je Messkampagne und einer Tabelle
    db_zeiger.execute("CREATE SCHEMA IF NOT EXISTS " + db_database + ";")
    connect_table_string = "CREATE TABLE " + db_database + ".`" + db_table + "` ("
    temp = "id INT, zeitpunkt DOUBLE"
    spatial_index_check = False
    spatial_index_name = ""  # Name des Punktes, auf das der Spatial Index gelegt wird
    for i, sensor in enumerate(Sensorliste):
        for j in range(len(sensor.db_felder)-2):
            spatial_string = ""
            if not spatial_index_check and type(sensor).__name__ == "GNSS":
                spatial_index_check = True
                spatial_string = " NOT NULL SRID 25832"
                spatial_index_name = Sensornamen[i] + "_" + sensor.db_felder[j+2][0]
            temp = temp + ", " + Sensornamen[i] + "_" + sensor.db_felder[j+2][0] + " " + sensor.db_felder[j+2][1] + spatial_string

    temp = temp + ", SPATIAL INDEX(" + spatial_index_name + ")"
    db_zeiger.execute(connect_table_string + temp + ");")
    print(connect_table_string + temp + ");")
    return [db_zeiger, db_database, db_table]

Sensorliste = [Echolot(), GNSS()]
Sensornamen = ["echo", "gnss"]
temp = db_verbinden(Sensorliste, Sensornamen)
zeiger = temp[0]

db = "INSERT INTO " + temp[1] + ".`" + temp[2] + "` VALUES (0, 0.0, 5.0, 5.0, ST_pointfromtext('POINT(99 99)'), ST_pointfromtext('POINT(99 99)'), 0);"
print(db)
zeiger.execute(db)
zeiger.commit()