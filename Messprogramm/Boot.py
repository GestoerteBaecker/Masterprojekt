import Sensoren
import datetime
import numpy
import Pixhawk
import pyodbc
import statistics
import threading
import time

# Klasse, die alle Funktionalitäten des Bootes umfasst
# self.auslesen > self.fortlaufende_aktualisierung > self.datenbankbeschreiben
# -> d.h. damit zB self. datenbankbeschreiben True ist müssen mind. die anderen beiden auch True sein
class Boot:

    def __init__(self,Pix_COM="com0", GNSS1_COM="COM0", GNSS1_baud=0, GNSS1_timeout=0, GNSS1_takt=0.2, GNSS2_COM="COM0", GNSS2_baud=0, GNSS2_timeout=0, GNSS2_takt=0.2, ECHO_COM="COM0", ECHO_baud=0, ECHO_timeout=0, ECHO_takt=0.2, DIST_COM="COM0", DIST_baud=0, DIST_timeout=0, DIST_takt=1):

        self.auslesen = False                           # Schalter, ob die Sensoren dauerhaft ausgelesen werden
        self.fortlaufende_aktualisierung = False        # Schalter, ob das Dict mit den aktuellen Sensordaten permanent aktualisiert wird
        self.datenbankbeschreiben = False               # Schalter, ob die Datenbank mit Sensordaten beschrieben wird
        self.Sensorliste = []                           # hier sind die Sensor-Objekte drin
        self.AktuelleSensordaten = []                   # hier stehen die Daten-Objekte drin
        self.Sensornamen = []                           # hier sind die Namen der Sensoren in der Reihenfolge wie in self.Sensorliste drin
        self.aktualisierungsprozess = None              # Thread mit Funktion, die die Sensordaten innerhalb dieser Klasse speichert
        self.datenbankbeschreiben_thread = None
        self.db_verbindung = None
        self.db_zeiger = None
        self.db_database = None
        self.db_table = None
        self.db_id = 0
        takt = [GNSS1_takt, GNSS2_takt, ECHO_takt, DIST_takt]
        self.db_takt = min(*takt)

        if Pix_COM != "com0":
            self.PixHawk = Pixhawk.Pixhawk(Pix_COM)

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
            self.db_verbindung = pyodbc.connect("DRIVER={MySQL ODBC 8.0 ANSI Driver}; SERVER=" + server + "; UID=" + uid + ";PASSWORD=" + password + ";")
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
                    if type(sensor).__name__ == "GNSS" and sensor.db_felder[j+2][1] == "POINT":
                        spatial_string = " NOT NULL SRID 25832"
                        if not spatial_index_check:
                            spatial_index_check = True
                            spatial_index_name = self.Sensornamen[i] + "_" + sensor.db_felder[j+2][0]
                    temp = temp + ", " + self.Sensornamen[i] + "_" + sensor.db_felder[j+2][0] + " " + sensor.db_felder[j+2][1] + spatial_string

            self.db_zeiger.execute(connect_table_string + temp + ");")
            temp = "CREATE SPATIAL INDEX ind_" + spatial_index_name + " ON " + self.db_database + ".`" + self.db_table + "`(" + spatial_index_name + ");"
            self.db_zeiger.execute(temp)

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

        def Ueberschreibungsfunktion(self):
            while self.fortlaufende_aktualisierung:
                for i in range(0, len(self.Sensorliste)):
                    sensor = self.Sensorliste[i]
                    self.AktuelleSensordaten[i] = sensor.aktdaten
                time.sleep(self.takt)

        self.aktualisierungsprozess = threading.Thread(target=Ueberschreibungsfunktion, args=(self, ), daemon=True)
        self.aktualisierungsprozess.start()

    def Hinderniserkennung(self):
        pass

    def Erkunden(self, Art_d_Gewaessers):   # Art des Gewässers (optional)
        pass

    def Punkt_anfahren(self, e, n, geschw =2.0):  # Utm-Koordinaten und Gechwindigkeit setzen

        self.PixHawk.Geschwindigkeit_setzen(geschw)
        self.PixHawk.Wegpunkt_anfahren(e, n)
        print("Fahre Punkt mit Koordinaten E:", e, "N:", n, "an")

    def Wegberechnung(self):
        pass

    def Gewaesseraufnahme(self):
        pass

    def Boot_stoppen(self):

        self.Punkt_anfahren(self.AktuelleSensordaten[0].daten[0], self.AktuelleSensordaten[0].daten[1], 0.5)
        print("Notstopp! Letzte Posotion wird langsam angefahren")

        #todo: Notstopp richtig implementieren

    def Trennen(self):

        for Sensor in self.Sensorliste:
            Sensor.kill()

        if self.PixHawk:
            self.PixHawk.Trennen()

    def RTL(self):

        self.PixHawk.Return_to_launch()

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

    # Berechnet das Gefälle unterhalb des Bootes
    # sollte höchstens alle paar Sekunden aufgerufen werden, spätestens bei der Profilberechnung
    def Hydrographische_abfrage(self, punkt):
        """
        :param punkt: Punkt des Bootes
        :return: Liste mit Vektor der größten Steigung (Richtung gemäß Vektor und für Betrag gilt: arcsin(betrag) = Steigungswinkel) und Angabe, ob flächenhaft um das Boot herum gesucht wurde (True) oder ob nur 1-dim Messungen herangezogen wurden (False)
        """
        punkte = self.Daten_abfrage(punkt)
        fläche = Flächenberechnung(punkte[0], punkte[1])

        if fläche < 5: # dann sind nur Punkte enthalten, die vermutlich aus den momentanen Messungen herrühren

            # Ausgleichsgerade und Gradient auf Kurs projizieren (<- Projektion ist implizit, da die zuletzt aufgenommenen Punkte auf dem Kurs liegen müssten)
            n_pkt = int(len(punkte[0]))  # Anzahl Punkte
            p1 = numpy.array([punkte[0][0], punkte[1][0], punkte[2][0]])
            p2 = numpy.array([punkte[0][-1], punkte[1][-1], punkte[2][-1]])
            r0 = p2 - p1
            d12 = numpy.linalg.norm(r0)
            r0 = r0 / d12
            st0 = p1 - numpy.dot(r0, p1) * r0
            L = []
            temp = numpy.matrix(numpy.array([1, 0, 0] * n_pkt)).getT()  # Erste Spalte der A-Matrix
            A = temp  # A-Matrix ist folgendermaßen aufgebaut: U in Spalten: erst 3 Komp. des Stützvektors, dann alle lambdas
            #   je Punkt und zuletzt 3 Komp. des Richtungsvektors (immer die Ableitungen nach diesen)
            #   in den Zeilen sind die Beobachtungen je die Komponenten der Punkte
            A = numpy.hstack((A, numpy.roll(temp, 1, 0)))
            A = numpy.hstack((A, numpy.roll(temp, 2, 0)))  # bis hierher sind die ersten 3 Spalten angelegt
            A_spalte_r0 = numpy.matrix(numpy.array([0.0] * n_pkt * 3))  # Spalte mit Lambdas (Abl. nach r0)
            A_spalte_lamb = numpy.hstack((numpy.matrix(r0), numpy.matrix(
                numpy.array([0] * 3 * (n_pkt - 1))))).getT()  # Spalte mit Komp. von r0 (Ableitungen nach den Lambdas)
            lambdas = []
            for i in range(n_pkt):
                p = []  # gerade ausgelesener Punkt
                for j in range(3):
                    p.append(punkte[j][i])
                L += p
                p = numpy.array(p)
                lamb = numpy.dot(r0, (p - st0)) / d12
                lambdas.append(lamb)
                A_spalte_r0[0, i * 3] = lamb
                # x0 = numpy.append(x0, lamb)
                A = numpy.hstack((A, numpy.roll(A_spalte_lamb, 3 * i, 0)))
            A_spalte_r0 = A_spalte_r0.getT()
            A = numpy.hstack((A, A_spalte_r0))
            A = numpy.hstack((A, numpy.roll(A_spalte_r0, 1, 0)))
            A = numpy.hstack((A, numpy.roll(A_spalte_r0, 2, 0)))

            # Kürzung der Beobachtungen
            l = numpy.array([])
            for i in range(n_pkt):
                pkt0 = st0 + lambdas[i] * r0
                pkt = L[3 * i:3 * (i + 1)]
                beob = numpy.array(pkt) - pkt0
                l = numpy.hstack((l, beob))

            # Einführung von Bedingungen an Stütz- und Richtungsvektor (Stütz senkrecht auf Richtung und Betrag von Richtung = 1)
            A_trans = A.getT()
            N = A_trans.dot(A)
            # Bedingungen an die N-Matrix anfügen
            A_bed_1 = numpy.matrix(
                numpy.hstack((numpy.hstack((r0, numpy.zeros((1, n_pkt))[0])), st0)))  # st skalarpro r = 0
            A_bed_2 = numpy.matrix(numpy.hstack((numpy.zeros((1, n_pkt + 3))[0], 2 * r0)))  # r0 = 1
            N = numpy.hstack((N, A_bed_1.getT()))
            N = numpy.hstack((N, A_bed_2.getT()))
            A_bed_1 = numpy.hstack((A_bed_1, numpy.matrix(numpy.array([0, 0]))))
            A_bed_2 = numpy.hstack((A_bed_2, numpy.matrix(numpy.array([0, 0]))))
            N = numpy.vstack((N, A_bed_1))
            N = numpy.vstack((N, A_bed_2))
            # Anfügen der Widersprüche
            w_senkrecht = 0 - numpy.dot(r0, st0)
            w_betrag_r = 1 - (r0[0] ** 2 + r0[1] ** 2 + r0[2] ** 2)
            n = A_trans.dot(l)
            n = numpy.hstack((n, numpy.array([[w_senkrecht, w_betrag_r]])))

            # Auswertung
            x0 = numpy.matrix(numpy.hstack((numpy.hstack((st0, numpy.array(lambdas))), r0))).getT()
            q = N.getI()
            x_dach = numpy.matrix(q.dot(n.getT()))
            x_dach = x_dach[0:len(x_dach) - 2, 0]
            X_dach = x0 + x_dach
            r = numpy.array([X_dach[len(X_dach) - 3, 0], X_dach[len(X_dach) - 2, 0], X_dach[len(X_dach) - 1, 0]])
            r[2] = 0

            max_steigung = r  # Vektor
            flächenhaft = False
        else: # dann sind auch seitlich Messungen vorhanden und demnach ältere Messungen als nur die aus der unmittelbaren Fahrt
            # Ausgleichsebene und finden der max. Steignug
            a_matrix = numpy.matrix(numpy.column_stack((punkte[0], punkte[1], numpy.array(len(punkte[0])*[1]))))
            q = (a_matrix.getT().dot(a_matrix)).getI()
            x_dach = (q.dot(a_matrix.getT())).dot(punkte[2])
            n = numpy.array([x_dach[0, 0], x_dach[0, 1], -1])
            n = n / numpy.linalg.norm(n)
            max_steigung = n
            max_steigung[2] = 0
            flächenhaft = True
        return [max_steigung, flächenhaft] #TODO: Ausgabe der Standardabweichung als Rauhigkeitsmaß


    # Fragt Daten aus der DB im "Umkreis" (Bounding Box) von radius Metern des punktes (Boot) ab
    def Daten_abfrage(self, punkt, radius=20):
        x = []
        y = []
        tiefe = []
        db_string = "SELECT " #TODO: implementieren
        return [numpy.array(x), numpy.array(y), numpy.array(tiefe)]

# Berechnet die Fläche des angeg. Polygons
# https://en.wikipedia.org/wiki/Shoelace_formula
# https://stackoverflow.com/questions/24467972/calculate-area-of-polygon-given-x-y-coordinates
def Flächenberechnung(x, y):
    """
    :param x, y: sind numpy-arrays
    :return:
    """
    # dot: Skalarprodukt, roll: nimmt das array und verschiebt alle Werte um den angeg. Index nach vorne
    return 0.5 * numpy.abs(numpy.dot(x, numpy.roll(y, 1)) - numpy.dot(y, numpy.roll(x, 1)))


# Zum Testen
if __name__=="__main__":

    Boot = Boot(Pix_COM="com0", GNSS1_COM="COM10", GNSS1_baud=115200, GNSS1_timeout=0, GNSS1_takt=0.2, GNSS2_COM="COM11", GNSS2_baud=115200, GNSS2_timeout=0, GNSS2_takt=0.2, ECHO_COM="COM1", ECHO_baud=19200, ECHO_timeout=0, ECHO_takt=0.2, DIST_COM="COM12", DIST_baud=19200, DIST_timeout=0, DIST_takt=1)

    Boot.Sensorwerte_auslesen()
    time.sleep(5)

    Boot.Datenbank_beschreiben()
    time.sleep(10)

    Boot.Trennen()
