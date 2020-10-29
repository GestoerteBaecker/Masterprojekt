import Sensoren
import datetime
import threading
import time


class Boot:

    def __init__(self,GNSS1_COM = False, GNSS1_baud = False, GNSS1_timeout = 0, GNSS1_takt = 0.2, GNSS2_COM = False, GNSS2_baud = False, GNSS2_timeout = 0, GNSS2_takt = 0.2, ECHO_COM = False, ECHO_baud = False, ECHO_timeout = 0, ECHO_takt = 0.2, DIST_COM = False, DIST_baud = False, DIST_timeout = False, DIST_takt = False):

        self.fortlaufende_aktualisierung = False        # Schlater, ob das Dict mit den aktuellen Sensordaten permanent aktualisiert wird
        self.auslesen = False                           # Schalter, ob die Sensoren dauerhaft ausgelesen werden
        self.AktuelleSensordaten = {}
        self.Sensorliste = []
        self.AktuelleSensordaten = {} # hier stehen die Daten-Objekte mit den jeweiligen Sensorennamen (wie GNSS1) als Schlüssekwörter drin
        self.Sensornamen = []

        if GNSS1_COM:
            self.GNSS1 = Sensoren.GNSS(GNSS1_COM, GNSS1_baud, GNSS1_timeout, GNSS1_takt)
            self.Sensorliste.append(self.GNSS1)
            self.Sensornamen.append("GNSS1")

        if GNSS2_COM:
            self.GNSS2 = Sensoren.GNSS(GNSS2_COM, GNSS2_baud, GNSS2_timeout, GNSS2_takt)
            self.Sensorliste.append(self.GNSS2)
            self.Sensornamen.append("GNSS2")

        if ECHO_COM:
            self.Echo = Sensoren.Echolot(ECHO_COM, ECHO_baud, ECHO_timeout, ECHO_takt)
            self.Sensorliste.append(self.Echo)
            self.Sensornamen.append("Echolot")

        if DIST_COM:
            self.DIST = Sensoren.Distanzmesser(DIST_COM, DIST_baud, DIST_timeout, DIST_takt)
            self.Sensorliste.append(self.DIST)
            self.Sensornamen.append("Distanz")


    def Sensorwerteauslesen(self):

        if not self.auslesen:
            self.auslesen = True
            for Sensor in self.Sensorliste:
                Sensor.read_datastream()

            self.Datenaktualisierung()  # Funktion zum dauerhaften Überschreiben des aktuellen Zustands (neuer Thread wir aufgemacht)

    def Verbinden_mit_DB(self):

        for i in range(0,len(self.Sensorliste)):
            try:
                self.Sensorliste[i].connect_to_db(self.Sensornamen[i])
            except:
                print("Für" + self.Sensornamen[i] + "konnte keine Datenbanktabelle angelegt werden")

    def Punktanfahren(self, e, n):
        pass

    def Datenbankbeschreiben(self):

        if not self.auslesen:
            self.Sensorwerteauslesen()
            self.auslesen = True

        for Sensor in self.Sensorliste:
            Sensor.start_pushing_db()       # Daten permanent in Datenbank ablegen

        if not self.fortlaufende_aktualisierung:
            self.Datenaktualisierung()  # Funktion zum dauerhaften Überschreiben des aktuellen Zustands (neuer Thread wir aufgemacht)

    def Datenaktualisierung(self):

        self.fortlaufende_aktualisierung = True

        def uebderscheibungsfunktion(self):

            while self.fortlaufende_aktualisierung:
                for i in range(0, len(self.Sensorliste)):
                    Sensor = self.Sensorliste[i]
                    Sensorname = self.Sensornamen[i]

                    typ = type(Sensor).__name__

                    if typ == "GNSS":

                        x = Sensor.aktdaten.daten[0]
                        y = Sensor.aktdaten.daten[1]
                        hdop = Sensor.aktdaten.daten[2]
                        h = Sensor.aktdaten.daten[4]
                        gps_status = Sensor.aktdaten.daten[5]

                        self.AktuelleSensordaten = {Sensorname+"x": x, Sensorname+"y": y, Sensorname+"hdop": hdop, Sensorname+"h": h, Sensorname+"gps_status": gps_status}

                    if typ == "Distanzmesser":

                        dist = Sensor.aktdaten.deten[0]

                        self.AktuelleSensordaten = {Sensorname+"dist": dist}

                    if typ == "Echolot":

                        tiefe1 = Sensor.aktdaten.daten[0]
                        tiefe2 = Sensor.aktdaten.daten[1]

                        self.AktuelleSensordaten = {Sensorname+"tiefe1": tiefe1, Sensorname+"tiefe2": tiefe2}

                time.sleep(1)

        self.writing_process = threading.Thread(target=uebderscheibungsfunktion, args=(self, ), daemon=True)
        self.writing_process.start()

    def Hinderniserkennung(self):
        pass

    def Erkunden(self, Art_d_Gewaessers): # Art des Gewässers optional
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

# Zum Testen
if __name__=="__main__":

    Boot = Boot()