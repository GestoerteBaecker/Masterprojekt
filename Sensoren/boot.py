import Sensoren
import datetime
import threading

x = Sensoren.GNSS("COM10",115200,0,0.2)
class Boot:

    def __init__(self,GNSS1_COM = False, GNSS1_baud = False, GNSS1_timeout = 0, GNSS1_takt = 0.2, GNSS2_COM = False, GNSS2_baud = False, GNSS2_timeout = 0, GNSS2_takt = 0.2, ECHO_COM = False, ECHO_baud = False, ECHO_timeout = 0, ECHO_takt = 0.2, Dist_COM = False, Dist_baud = False, Dist_timeout = False, Dist_takt = False):

        self.Sensorliste = []
        self.AktuelleSensordaten = {} # hier stehen die Daten-Objekte mit den jeweiligen Sensorennamen (wie GNSS1) als Schlüssekwörter drin

        if GNSS1_COM:
            self.GNSS1 = Sensoren.GNSS(GNSS1_COM, GNSS1_baud, GNSS1_timeout, GNSS1_takt)
            self.Sensorliste.append(self.GNSS1)
        if GNSS2_COM:
            self.GNSS2 = Sensoren.GNSS(GNSS2_COM, GNSS2_baud, GNSS2_timeout, GNSS2_takt)
            self.Sensorliste.append(self.GNSS2)
        if ECHO_COM:
            self.Echo = Sensoren.Echolot(ECHO_COM, ECHO_baud, ECHO_timeout, ECHO_takt)
            self.Sensorliste.append(self.Echo)
        if Dist_COM:
            self.Dist = Sensoren.Distanzmesser(Dist_COM, Dist_baud, Dist_timeout, Dist_takt)
            self.Sensorliste.append(Dist_COM)


    def Verbinden_mit_DB(self):
        date = "`"+str((datetime.datetime.fromtimestamp(time.time())))+"`"

        for Sensor in self.Sensorliste:
            Sensor.connect_to_db(Sensor.__name__,date)

    def Punktanfahren(self, E, N):
        pass

    def Datenaufnehmen(self):
        pass

    def Hinderniserkennung(self):
        pass

    def Erkunden(self, Art_d_Gewaessers): # Art des Gewässers optional
        pass

    def Wegberechnung(self):
        pass

    def Gewaesseraufnahme(self):
        pass

    def Trennen(self):
        pass

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

