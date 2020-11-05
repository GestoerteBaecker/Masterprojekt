import pyodbc
import time
import datetime
import statistics

class Daten:
    def __init__(self, id, daten, timestamp=time.time()):
        # je nach zugeordnetem Sensor
        self.id = id
        self.daten = daten
        #self.sensor = sensor
        self.timestamp = timestamp

class Sensor:
    def __init__(self):
        self.db_felder = [("id", "INT"), ("zeitpunkt", "DOUBLE")]

class Echolot(Sensor):
    def __init__(self):
        super().__init__()
        self.db_felder = [("id", "INT"), ("zeitpunkt", "DOUBLE"), ("tiefe1", "DOUBLE"), ("tiefe2", "DOUBLE")]
    def make_db_command(self, datenpaket, id_zeit=True):
        if id_zeit:
            db_string_daten = [datenpaket.id, datenpaket.timestamp, datenpaket.daten[0], datenpaket.daten[1]]
        else:
            db_string_daten = [datenpaket.daten[0], datenpaket.daten[1]]
        db_string_daten = ", ".join(str(x) for x in db_string_daten)
        return db_string_daten


class GNSS(Sensor):
    def __init__(self):
        super().__init__()
        self.db_felder = [("id", "INT"), ("zeitpunkt", "DOUBLE"), ("punkt", "POINT"), ("HDOP", "DOUBLE"),
                          ("up", "DOUBLE"), ("Qualitaet", "INT")]

    def make_db_command(self, datenpaket, id_zeit=True):
        punkt_temp = "ST_pointfromtext('POINT(" + str(datenpaket.daten[0]) + " " + str(datenpaket.daten[1]) + ")', 25832)"
        if id_zeit:
            db_string_daten = [datenpaket.id, datenpaket.timestamp, punkt_temp, str(datenpaket.daten[2]), str(datenpaket.daten[3]), str(datenpaket.daten[4])] # Einfügen von Id, Timestamp, lat, lon, Höhe, Qualität,
        else:
            db_string_daten = [punkt_temp, str(datenpaket.daten[2]), str(datenpaket.daten[3]), str(datenpaket.daten[4])]  # Einfügen von Id, Timestamp, lat, lon, Höhe, Qualität,
        db_string_daten = ", ".join(str(x) for x in db_string_daten)
        return db_string_daten

def db_verbinden(Sensorliste, Sensornamen, db_database, db_table):

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
            if type(sensor).__name__ == "GNSS" and sensor.db_felder[j+2][1] == "POINT":
                spatial_string = " NOT NULL SRID 25832"
                if not spatial_index_check:
                    spatial_index_check = True
                    spatial_index_name = Sensornamen[i] + "_" + sensor.db_felder[j+2][0]
            temp = temp + ", " + Sensornamen[i] + "_" + sensor.db_felder[j+2][0] + " " + sensor.db_felder[j+2][1] + spatial_string

    print(connect_table_string + temp + ");")
    db_zeiger.execute(connect_table_string + temp + ");")
    temp = "CREATE SPATIAL INDEX ind_" + spatial_index_name + " ON " + db_database + ".`" + db_table + "`(" + spatial_index_name + ");"
    print(temp)
    db_zeiger.execute(temp)
    return db_zeiger

db_database = "`"+str((datetime.datetime.fromtimestamp(time.time())))+"`"
db_table = "Messkampagne"
Sensorliste = [Echolot(), GNSS()]
Sensornamen = ["echo", "gnss"]
zeiger = db_verbinden(Sensorliste, Sensornamen, db_database, db_table)

gnss_daten = Daten(1, [32500000, 5800000, 0, 40, 1], time.time())
echo_daten = Daten(2, [5,5.5], time.time())
akt_daten = [echo_daten, gnss_daten]

db_text = "INSERT INTO " + db_database + "." + db_table + " VALUES ("
zeiten = []
db_temp = ""
for i, daten in enumerate(akt_daten):
    zeiten.append(daten.timestamp)
    db_temp = db_temp + ", " + Sensorliste[i].make_db_command(daten, id_zeit=False)
zeit_mittel = statistics.mean(zeiten)
db_id = 1
db_text = db_text + str(db_id) + ", " + str(zeit_mittel) + db_temp + ");"
zeiger.execute(db_text)
zeiger.commit()
