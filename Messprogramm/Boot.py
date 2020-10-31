import Sensoren
import datetime
import Pixhawk
import pyodbc
import statistics
import threading
import time

# Klasse, die alle Funktionalitäten des Bootes umfasst
# self.auslesen > self.fortlaufende_aktualisierung > self.datenbankbeschreiben
# -> d.h. damit zB self. datenbankbeschreiben True ist müssen mind. die anderen beiden auch True sein
class Boot:

    def __init__(self,GNSS1_COM="COM0", GNSS1_baud=0, GNSS1_timeout=0, GNSS1_takt=0.2, GNSS2_COM="COM0", GNSS2_baud=0, GNSS2_timeout=0, GNSS2_takt=0.2, ECHO_COM="COM0", ECHO_baud=0, ECHO_timeout=0, ECHO_takt=0.2, DIST_COM="COM0", DIST_baud=0, DIST_timeout=0, DIST_takt=1):

        self.auslesen = False                           # Schalter, ob die Sensoren dauerhaft ausgelesen werden
        self.fortlaufende_aktualisierung = False        # Schalter, ob das Dict mit den aktuellen Sensordaten permanent aktualisiert wird
        self.datenbankbeschreiben = False               # Schalter, ob die Datenbank mit Sensordaten beschrieben wird
        self.Sensorliste = [] # hier sind die Sensor-Objekte drin
        self.AktuelleSensordaten = [] # hier stehen die Daten-Objekte drin
        self.Sensornamen = [] # hier sind die Namen der Sensoren in der Reihenfolge wie in self.Sensorliste drin
        self.aktualisierungsprozess = None # Thread mit Funktion, die die Sensordaten innerhalb dieser Klasse speichert
        self.datenbankbeschreiben_thread = None
        self.db_verbindung = None
        self.db_zeiger = None
        self.db_database = None
        self.db_table = None
        self.db_id = 0
        takt = [GNSS1_takt, GNSS2_takt, ECHO_takt, DIST_takt]
        self.db_takt = min(*takt)

        if GNSS1_COM != "COM0":
            self.GNSS1 = Sensoren.GNSS(GNSS1_COM, GNSS1_baud, GNSS1_timeout, GNSS1_takt)
            self.Sensorliste.append(self.GNSS1)
            self.Sensornamen.append("GNSS1")

        if GNSS2_COM != "COM0":
            self.GNSS2 = Sensoren.GNSS(GNSS2_COM, GNSS2_baud, GNSS2_timeout, GNSS2_takt)
            self.Sensorliste.append(self.GNSS2)
            self.Sensornamen.append("GNSS2")

        if ECHO_COM != "COM0":
            self.Echo = Sensoren.Echolot(ECHO_COM, ECHO_baud, ECHO_timeout, ECHO_takt)
            self.Sensorliste.append(self.Echo)
            self.Sensornamen.append("Echolot")

        if DIST_COM != "COM0":
            self.DIST = Sensoren.Distanzmesser(DIST_COM, DIST_baud, DIST_timeout, DIST_takt)
            self.Sensorliste.append(self.DIST)
            self.Sensornamen.append("Distanz")

        #TODO: Verbindung mit Pixhawk

        self.AktuelleSensordaten = len(self.Sensorliste) * [None]


    # muss einmalig angestoßen werden und verbleibt im Messzustand, bis self.auslesen auf False gesetzt wird
    def Sensorwerte_auslesen(self):

        if not self.auslesen:
            self.auslesen = True
            for sensor in self.Sensorliste:
                sensor.read_datastream()


    # muss einmalig angestoßen werden
    def Datenbank_beschreiben(self, mode=0):
        """
        :param mode: 0 für eine DB-Tabelle, in der alle Daten als ein einziger Eintrag eingeführt werden
            1 für separate DB-Tabellen je Sensor (ursprüngliches Vorhaben)
        """
        self.Verbinden_mit_DB(mode)

        if not self.fortlaufende_aktualisierung:
            self.Datenaktualisierung()  # Funktion zum dauerhaften Überschreiben des aktuellen Zustands (neuer Thread wir aufgemacht)

        if mode == 0:

            def Datenbank_Boot(self):
                while self.datenbankbeschreiben:
                    db_text = "INSERT INTO " + self.db_database + "." + self.db_table + " VALUES ("
                    zeiten = []
                    db_temp = ""
                    for i, daten in enumerate(self.AktuelleSensordaten):
                        zeiten.append(daten.timestamp) #TODO: Testen , ob die Zeitpunkte nicht zu weit auseinander liegen?
                        db_temp = db_temp + ", " + self.Sensorliste[i].make_db_command(daten, id_zeit=False)
                    zeit_mittel = statistics.mean(zeiten)
                    self.db_id += 1
                    db_text = db_text + str(self.db_id) + ", " + str(zeit_mittel) + db_temp + ");"
                    self.db_zeiger.execute(db_text)
                    self.db_zeiger.commit()
                    time.sleep(self.db_takt/2)

            if not self.datenbankbeschreiben:
                self.datenbankbeschreiben = True
                self.datenbankbeschreiben_thread = threading.Thread(target=Datenbank_Boot, args=(self, ))
                self.datenbankbeschreiben_thread.start()

        elif mode == 1:
            if not self.datenbankbeschreiben:
                self.datenbankbeschreiben = True
                for Sensor in self.Sensorliste:
                    Sensor.start_pushing_db()       # Daten permanent in Datenbank ablegen

    def Verbinden_mit_DB(self, mode=0, server="localhost", uid="root", password="EchoBoat"):
        """
        :param mode: 0 für eine DB-Tabelle, in der alle Daten als ein einziger Eintrag eingeführt werden
            1 für separate DB-Tabellen je Sensor (ursprüngliches Vorhaben)
        """
        if mode == 0:
            self.db_database = "`"+str((datetime.datetime.fromtimestamp(time.time())))+"`"
            self.db_table = "Messkampagne"
            self.db_verb = pyodbc.connect("DRIVER={MySQL ODBC 8.0 ANSI Driver}; SERVER=" + server + "; UID=" + uid + ";PASSWORD=" + password + ";")
            self.db_zeiger = self.db_verbindung.cursor()

            # Anlegen einer Datenbank je Messkampagne und einer Tabelle
            self.db_zeiger.execute("CREATE SCHEMA IF NOT EXISTS " + self.db_database + ";")
            connect_table_string = "CREATE TABLE " + self.db_database + ".`" + self.db_table + "` ("
            temp = "id INT, zeitpunkt DOUBLE"
            spatial_index_check = False
            spatial_index_name = ""  # Name des Punktes, auf das der Spatial Index gelegt wird
            for i, sensor in enumerate(self.Sensorliste):
                for j in range(len(sensor.db_felder)-2):
                    spatial_string = ""
                    if not spatial_index_check and type(sensor).__name__ == "GNSS":
                        spatial_index_check = True
                        spatial_string = " NOT NULL SRID 25832"
                        spatial_index_name = self.Sensornamen[i] + "_" + sensor.db_felder[j+2][0]
                    temp = temp + ", " + self.Sensornamen[i] + "_" + sensor.db_felder[j+2][0] + spatial_string + " " + sensor.db_felder[j+2][1]

            temp = temp + ", SPATIAL INDEX(" + spatial_index_name + ")"
            self.db_zeiger.execute(connect_table_string + temp + ");")

        elif mode == 1:
            for i, sensor in enumerate(self.Sensorliste):
                try:
                    sensor.connect_to_db(self.Sensornamen[i])
                except:
                    print("Für " + self.Sensornamen[i] + " konnte keine Datenbanktabelle angelegt werden")

    def Datenaktualisierung(self):

        if not self.auslesen:
            self.Sensorwerte_auslesen()

        self.fortlaufende_aktualisierung = True

        def Ueberscheibungsfunktion(self):
            while self.fortlaufende_aktualisierung:
                for i in range(0, len(self.Sensorliste)):
                    sensor = self.Sensorliste[i]
                    self.AktuelleSensordaten[i] = sensor.aktdaten
                time.sleep(self.takt)

        self.aktualisierungsprozess = threading.Thread(target=Ueberscheibungsfunktion, args=(self, ), daemon=True)
        self.aktualisierungsprozess.start()

    def Hinderniserkennung(self):
        pass

    def Erkunden(self, Art_d_Gewaessers): # Art des Gewässers optional
        pass

    def Punkt_anfahren(self, e, n):
        pass

    def Wegberechnung(self):
        pass

    def Gewaesseraufnahme(self):
        pass

    def Trennen(self):

        for Sensor in self.Sensorliste:
            Sensor.kill()

    def RTL(self):
        pass

    def Kalibrierung(self):
        pass

    # gibt ein Dict mit Wahrheitswerten zurück, je nachdem, ob der Sensor aktiv ist oder nicht, Schlüsselwert ist der Name des jeweiligen Sensors (echter Name, nicht Klassenname!)
    def Lebenzeichen(self):
        aktiv = dict()
        for i, sensor in enumerate(self.Sensorliste):
            aktiv[self.Sensornamen[i]] = sensor.verbindung_hergestellt
        return aktiv

    def postprocessing(self):
        pass
    #TODO: Synchronisation/Fusion der einzelnen Messwerte (Echolot und GNSS)

# Zum Testen
if __name__=="__main__":

    Boot = Boot(GNSS1_COM="COM10", GNSS1_baud=115200, GNSS1_timeout=0, GNSS1_takt=0.2, GNSS2_COM="COM11", GNSS2_baud=115200, GNSS2_timeout=0, GNSS2_takt=0.2, ECHO_COM="COM1", ECHO_baud=19200, ECHO_timeout=0, ECHO_takt=0.2, DIST_COM="COM12", DIST_baud=19200, DIST_timeout=0, DIST_takt=1)

    Boot.Sensorwerte_auslesen()
    time.sleep(5)

    Boot.Datenbank_beschreiben()
    time.sleep(10)

    Boot.Trennen()
