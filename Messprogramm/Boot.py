import Sensoren
import Messgebiet
import datetime
import json
import Pixhawk
import pyodbc
import statistics
import threading
import time
import numpy
import enum

# Definition von Enums zur besseren Lesbarkeit
class UferPosition(enum.Enum):
    IM_WASSER = 0
    NAH_AM_UFER = 1
    AM_UFER = 2

# Klasse, die alle Funktionalitäten des Bootes umfasst
# self.auslesen > self.fortlaufende_aktualisierung > self.datenbankbeschreiben
# -> d.h. damit zB self. datenbankbeschreiben True ist müssen mind. die anderen beiden auch True sein
class Boot:

    #TODO: GNSS muss beim Trennen rot werden; Datenbankschreiben hört bei unterbrochenem Echolot auf, Abfangen von Parsefehler in der Karte; GNSS1 Signalverlust in Datenbank abfangen ; Häufung von Datenverlusten manuell Signal abbrechen; Trennfunktion berichtigen
    #TODO: sleep Zeiten Probe lesen

    def __init__(self):

        # Einlesen der Parameter aus JSON Datei
        datei = open("boot_init.json", "r")
        json_daten = json.load(datei)
        datei.close()

        self.stern_winkelinkrement = json_daten["Boot"]["stern_winkelinkrement"] # Winkel der konvergenten Strahlen des Sterns
        self.stern_grzw_seitenlaenge = json_daten["Boot"]["stern_grzw_seitenlaenge"] # Länge einer Seite des Sterns, ab wann ein weiterer verdichtender Stern eingefügt wird
        self.profil_grzw_dichte_topographischer_punkte = json_daten["Boot"]["profil_grzw_dichte_topographischer_punkte"] # Solldichte in Punkte / m längs eines Profil
        self.profil_grzw_neigungen_topographischer_punkte = json_daten["Boot"]["profil_grzw_neigungen_topographischer_punkte"] # Neigung in gon aufeinander folgende Abschnitte entlang des Profils, sodass der dazwischen liegende Punkt als topographisch bedeutsam eingefügt wird
        self.messgebiet_ausdehnung = json_daten["Boot"]["messgebiet_ausdehnung"] # Breite und Höhe in m
        self.auslesen = False                           # Schalter, ob die Sensoren dauerhaft ausgelesen werden
        self.fortlaufende_aktualisierung = False        # Schalter, ob das Dict mit den aktuellen Sensordaten permanent aktualisiert wird
        self.datenbankbeschreiben = False               # Schalter, ob die Datenbank mit Sensordaten beschrieben wird
        self.Sensorliste = []                           # hier sind die Sensor-Objekte drin
        self.AktuelleSensordaten = []                   # hier stehen die Daten-Objekte drin
        self.Sensornamen = ["GNSS1","GNSS2","Echolot","Distanz"]                           # hier sind die Namen der Sensoren in der Reihenfolge wie in self.Sensorliste drin
        self.aktualisierungsprozess = None              # Thread mit Funktion, die die Sensordaten innerhalb dieser Klasse speichert
        self.datenbankbeschreiben_thread = None
        self.db_verbindung = None
        self.db_zeiger = None
        self.db_database = None
        self.db_table = None
        self.heading = None
        self.Offset_GNSSmitte_Disto = json_daten["Boot"]["offset_gnss_echolot"]   # TODO: Tatsächliches Offset messen und ergänzen
        self.Winkeloffset_dist = json_daten["Boot"]["offset_achsen_distometer_gnss"]          # TODO: Winkeloffset kalibrieren und angeben IN GON !!
        self.Faktor = json_daten["Boot"]["Simulationsgeschwindigkeit"]
        self.Bodenpunkte = [] # hier stehen nur die letzten 2 Median gefilterten Punkte drin (für Extrapolation der Tiefe / Ufererkennung)
        self.median_punkte = [] # hier stehen die gesammelten Bodenpunkte während der gesamten Messdauer drin (Median gefiltert)
        self.Offset_GNSS_Echo = 0       # TODO. Höhenoffset zwischen GNSS und Echolot bestimmen
        self.db_id = 0
        self.todoliste = []                 # TODO: Aufgaben die sich das Boot merken muss
        self.messgebiet = None
        self.ist_am_ufer = [UferPosition.IM_WASSER, False] # für Index 1: False: Bewegun vom Ufer weg oder gleichbleibende Tiefe/Entfernung zum Ufer; True: Bewegung zum Ufer hin (Tiefe/Entfernung zum Ufer verringert sich)
        self.boot_lebt = True
        self.stern_beendet = False
        self.geschwindigkeit = 2 # in km/h
        self.tracking_mode = Messgebiet.TrackingMode.BLINDFAHRT
        self.punkt_anfahren = False
        self.position = Messgebiet.Punkt(0,0,0) # Punkt des Bootes
        self.ufererkennung_aktiv = False
        self.Topographisch_bedeutsame_Bodenpunkte = [] # TODO: automatisch bedeutsame Bodenpunkte finden und einpflegen
        self.gefahreneStrecke = 0

        self.PixHawk = Pixhawk.Pixhawk(json_daten["Pixhawk"]["COM"])
        takt = []
        sensorklassen = [Sensoren.GNSS, Sensoren.GNSS, Sensoren.Echolot, Sensoren.Distanzmesser]

        for i, sensorname in enumerate(self.Sensornamen):
            if sensorname in json_daten:
                takt.append(json_daten[sensorname]["takt"])
                com = json_daten[sensorname]["COM"]
                baud = json_daten[sensorname]["baud"]
                timeout = json_daten[sensorname]["timeout"]
                taktzeit = json_daten[sensorname]["takt"]
                bytesize = json_daten[sensorname]["bytesize"]
                parity = json_daten[sensorname]["parity"]
                simulation = json_daten[sensorname]["simulation"]
                sensor = sensorklassen[i](com, baud, timeout, taktzeit, bytesize, parity, simulation)
                self.Sensorliste.append(sensor)

        self.AktuelleSensordaten = len(self.Sensorliste) * [False]
        self.db_takt = 0.2 #min(*takt)
        self.akt_takt = (self.db_takt)/ self.Faktor #Faktor zum Beschleunigen oder verlangsamen der Simulation ... Bei echter messung auf 1 setzten


    # muss einmalig angestoßen werden und verbleibt im Messzustand, bis self.auslesen auf False gesetzt wird
    def Sensorwerte_auslesen(self):

        if not self.auslesen:
            self.auslesen = True
            for sensor in self.Sensorliste:
                if sensor:
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
                db_text = "INSERT INTO " + self.db_database + "." + self.db_table + " VALUES ("
                while self.datenbankbeschreiben and self.boot_lebt:
                    t = time.time()
                    zeiten = []
                    db_temp = ""
                    db_schreiben = True
                    for i, daten in enumerate(self.AktuelleSensordaten):
                        if daten and self.Sensorliste[i].verbindung_hergestellt: # wenn Daten vorliegen
                            zeiten.append(daten.timestamp) #TODO: Testen , ob die Zeitpunkte nicht zu weit auseinander liegen?
                            db_temp = db_temp + ", " + self.Sensorliste[i].make_db_command(daten, id_zeit=False)
                        else:
                            db_schreiben = False
                        #    print("aktuelle Daten in DB, sensor", self.Sensorliste[i], daten, i)
                        #    db_temp = db_temp + ", " + self.Sensorliste[i].make_db_command(None, id_zeit=False, fehler=True)
                    if db_schreiben: #nur wenn alle Sensoren Daten haben
                        zeit_mittel = statistics.mean(zeiten)
                        self.db_id += 1
                        db_text = db_text + str(self.db_id) + ", " + str(zeit_mittel) + db_temp + ");"
                        #print(db_text)
                        self.db_zeiger.execute(db_text)
                        self.db_zeiger.commit()
                    schlafen = max(0, self.db_takt - (time.time() - t))
                    time.sleep(schlafen)

            if not self.datenbankbeschreiben:
                self.datenbankbeschreiben = True
                self.datenbankbeschreiben_thread = threading.Thread(target=Datenbank_Boot, args=(self, ), daemon=True)
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
                if sensor: # wenn es den Sensor gibt (also nicht simuliert wird)
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

    # wird im self.akt_takt aufgerufen und überschreibt self.AktuelleSensordaten mit den neusten Sensordaten
    def Datenaktualisierung(self):

        if not self.auslesen:
            self.Sensorwerte_auslesen()

        self.fortlaufende_aktualisierung = True

        def Ueberschreibungsfunktion(self):

            Letzte_Bodenpunkte = []
            while self.fortlaufende_aktualisierung and self.boot_lebt:
                t = time.time()

                position_vor_Aktualisierung = Messgebiet.Punkt(self.AktuelleSensordaten[0].daten[0],self.AktuelleSensordaten[0].daten[1])

                # Aktualisierung des Attributs self.AktuelleSensordaten
                for i in range(0, len(self.Sensorliste)):
                    if self.Sensorliste[i]:
                        sensor = self.Sensorliste[i]
                        if sensor.aktdaten:
                            self.AktuelleSensordaten[i] = sensor.aktdaten

                aktuelle_Position = Messgebiet.Punkt(self.AktuelleSensordaten[0].daten[0],self.AktuelleSensordaten[0].daten[1])
                entfernung = aktuelle_Position.Abstand(position_vor_Aktualisierung)
                self.gefahreneStrecke += entfernung

                # Abgeleitete Daten berechnen und überschreiben

                # aktuelles Heading berechnen und zum Boot abspeichern
                if self.AktuelleSensordaten[0] and self.AktuelleSensordaten[1]:         # Headingberechnung
                    self.heading = self.Headingberechnung()

                # wenn ein aktueller Entfernungsmesswert besteht, soll ein Uferpunkt berechnet werden
                if self.AktuelleSensordaten[0] and self.AktuelleSensordaten[1] and self.AktuelleSensordaten[3]:     #Uferpunktberechnung
                    uferpunkt = self.Uferpunktberechnung()
                    if self.messgebiet != None:
                        self.messgebiet.Uferpunkt_abspeichern(uferpunkt)

                # Tiefe berechnen und als Punktobjekt abspeichern (die letzten 10 Messwerte mitteln)
                if self.AktuelleSensordaten[0] and self.AktuelleSensordaten[2]:
                    Bodendaten = (self.AktuelleSensordaten[0], self.AktuelleSensordaten[2])
                    Letzte_Bodenpunkte.append(Bodendaten)

                    if len(Letzte_Bodenpunkte) > 10:
                        Bodenpunkt = self.Bodenpunktberechnung(Letzte_Bodenpunkte)
                        self.Bodenpunkte.append(Bodenpunkt)
                        if len(self.Bodenpunkte) > 2:
                            self.Bodenpunkte.pop(0)
                        # je nach Tracking Mode sollen die Median Punkte mitgeführt werden oder aus der Liste gelöscht werden (da sie ansonsten bei einem entfernt liegenden Profil mit berücksichtigt werden würden)
                        if self.tracking_mode.value < 2:
                            self.median_punkte.append(Bodenpunkt)
                        #else:
                        #    if len(self.median_punkte) > 0:
                        #        time.sleep(0.5) #TODO: vllt nicht nötig
                        #        self.median_punkte = []
                        Letzte_Bodenpunkte = []

                schlafen = max(0, self.akt_takt - (time.time() - t))
                time.sleep(schlafen)

        self.aktualisierungsprozess = threading.Thread(target=Ueberschreibungsfunktion, args=(self, ), daemon=True)
        self.aktualisierungsprozess.start()

        time.sleep(0.1)
        if not self.PixHawk.homepoint:
            punkt = Messgebiet.Punkt(self.AktuelleSensordaten[0].daten[0], self.AktuelleSensordaten[0].daten[1])
            self.PixHawk.homepoint = punkt

    def Uferpunktberechnung(self, dist=False):

        with Messgebiet.schloss:
            if not dist:  # Falls keine Distanz manuell angegeben wird (siehe self.DarstellungGUI) wird auf die Sensordaten zurückgegriffen
                dist = self.AktuelleSensordaten[3].daten
            x = self.AktuelleSensordaten[0].daten[0]
            y = self.AktuelleSensordaten[0].daten[1]
            heading = self.heading

        strecke = dist + self.Offset_GNSSmitte_Disto

        e = x + numpy.sin((heading + self.Winkeloffset_dist) / (200 / numpy.pi)) * strecke
        n = y + numpy.cos((heading + self.Winkeloffset_dist) / (200 / numpy.pi)) * strecke

        return Messgebiet.Uferpunkt(e, n)

    def Bodenpunktberechnung(self, Bodendaten = False):

        if Bodendaten:
            z_werte = []   #Liste, da nicht mittelwert, sondern Median berechnet wird
            Punkte = []
            summe_sedimentdicken = 0
            for messung in Bodendaten:
                gnss_datenobjekt, echo_datenobjekt = messung

                z_boden = gnss_datenobjekt.daten[3] - self.Offset_GNSS_Echo + echo_datenobjekt.daten[0]
                z_werte.append(z_boden)

                punkt = Messgebiet.Bodenpunkt(gnss_datenobjekt.daten[0], gnss_datenobjekt.daten[1], z_boden)
                Punkte.append(punkt)

                summe_sedimentdicken += abs(echo_datenobjekt.daten[0]-echo_datenobjekt.daten[1])

            mitte = (len(Bodendaten)//2)  # TODO: Prüfen
            z_werte.sort()

            if mitte != len(Bodendaten)/2:      # Die Liste hat eine ungerade länge
                z_median = z_werte[mitte]
                z_median_geradeliste = False
            else:
                z_median_geradeliste = (z_werte[mitte-1]+z_werte[mitte])/2 # -1, da mitte immer der obere Wert vom Median ist, z.B. 6//2 = 3 => 2. und 3. Index einer 6 einträge langen Liste müssen benutzt werden
                z_median = z_werte[mitte] # Auf variable zum suchen des zugehörigen Punktes

            sedimentdicke_mittel = summe_sedimentdicken / len(Bodendaten)
            for punkt in Punkte:
                if punkt.z == z_median:
                    if z_median_geradeliste:
                        return Messgebiet.Bodenpunkt(punkt.x,punkt.y,z_median_geradeliste)
                    else:
                        return punkt

        else:

            x, y = self.AktuelleSensordaten[0].daten[0], self.AktuelleSensordaten[0].daten[1]
            zgnss = self.AktuelleSensordaten[0].daten[3]
            Sedimentdicke = abs(self.AktuelleSensordaten[2].daten[0] - self.AktuelleSensordaten[2].daten[1])

            z_boden = zgnss - self.Offset_GNSS_Echo- self.AktuelleSensordaten[2].daten[0]

            Bodenpunkt = Messgebiet.Bodenpunkt(x,y,z_boden,Sedimentdicke)

            return Bodenpunkt

    def Headingberechnung(self, sollpunkt=None):
        return Messgebiet.Headingberechnung(self, sollpunkt, None)

    # prüft durchgehend, ob das Boot nah am Ufer kommt (über Dimetix und Echolot)
    # Entfernungswerte tracken und mit vorherigen Messungen abgleichen
    # Tiefenwerte tracken und mit vorherigen Messwerten vergleichen
    # self.ufererkennung_aktiv wird auf False gesetzt falls das Ufer erreicht wurde
    def Ufererkennung(self, sollheading):
        self.ufererkennung_aktiv = True
        #TODO: in Realität testen, ob das Boot zB über den Mittelpunkt drüber gefahren ist (wenn entsprechendes Tracking aktiv) oder dass das Heading des Boots in die Richtung weist, in die es soll
        #time.sleep(1) # warten, dass das Boot von dem gerade erfassten Ufer weg fährt

        def ufererkennung_thread(self): #TODO: extrapolation beruht auf alten Daten und kann daher bei dem U-Turn fehlerhaft AM_UFER und True ausgeben, sodass die Ufererkennung erst nach ein paar Sekunden ausgestoßen werden sollte, wenn sich die Bodenpunkte neu gefüllt haben (10 neue Werte = 2 sek + ein bisschen)
            while not abs(sollheading-self.heading) < 20: # Boot soll sich zumindest in Richtung des neuen Punkts drehen
                time.sleep(self.akt_takt)
            while self.boot_lebt and self.ufererkennung_aktiv:
                t = time.time()
                time.sleep(self.akt_takt)
                if self.tracking_mode != Messgebiet.TrackingMode.BLINDFAHRT: # len(self.Bodenpunkte) >= 2 and #TODO: ist das so ok? bei TrackingMode BLINDFAHRT fährt das Boot zwar nur auf Strecken, die es als sicher erachtet hat, da bereits einmal befahren, aber das Boot könnte trotzdem leicht vom Kurs abkommen und dann unbemertk auf Grund laufen
                    try:
                        p1, p2 = self.Bodenpunkte[-2], self.Bodenpunkte[-1]
                        steigung = p2.NeigungBerechnen(p1)
                        extrapolation = abs(p2.z + (steigung * self.geschwindigkeit * self.akt_takt)) # voraussichtliche Tiefe in self.akt_takt Sekunden
                    except:
                        extrapolation = 10 # Falls profile sehr kurz sind, kann die Extrapolation nicht berechnet werden
                        steigung = 0
                    entfernung = self.AktuelleSensordaten[3].daten # zum Ufer
                    tiefe = abs(self.AktuelleSensordaten[2].daten[0]) #TODO: Richtige Frequenz wählen
                    #TODO: Gewichten wann welche Kategorie gewählt werden soll
                    #print("tiefe", round(tiefe, 5) , "entfernung", round(entfernung, 5), "extrapolation", round(extrapolation, 5))
                    if tiefe < 2 or entfernung < 20 or extrapolation < 1.5:
                        if entfernung < 20 or steigung > 0:
                            #print("tiefe", tiefe, "entfernung", entfernung, "extrapolation", extrapolation, "steigung", steigung)
                            self.ist_am_ufer = [UferPosition.AM_UFER, True]  # "direkt" am Ufer und Boot guckt Richtung Ufer
                            print(entfernung, tiefe, steigung, extrapolation)
                            self.ufererkennung_aktiv = False
                            self.Bodenpunkte = []
                        else:
                            self.ist_am_ufer = [UferPosition.AM_UFER, False]  # "direkt" am Ufer, aber Boot guckt vom Ufer weg
                    elif tiefe < 5 or entfernung < 50 or extrapolation < 7:
                        if entfernung < 50 or steigung > 0:
                            self.ist_am_ufer = [UferPosition.NAH_AM_UFER, True]  # sehr kurz davor und Boot guckt Richtung Ufer
                        else:
                            self.ist_am_ufer = [UferPosition.NAH_AM_UFER, False]  # sehr kurz davor, aber Boot guckt vom Ufer weg
                    else:
                        self.ist_am_ufer = [UferPosition.IM_WASSER, False] # weit entfernt
                schlafen = max(0, (self.akt_takt) - (time.time() - t))
                time.sleep(schlafen)
                #time.sleep(self.akt_takt)
        thread = threading.Thread(target=ufererkennung_thread, args=(self, ), daemon=True)
        thread.start()


    def Erkunden(self):   # Art des Gewässers (optional)
        self.tracking_mode = Messgebiet.TrackingMode.PROFIL
        def erkunden_extern(self):

            # Messgebiet mit Profilen, Sternen, Topographisch bedeutsamen Punkte, TIN und Uferpunktquadtree anlegen
            self.erkundung_gestartet = True
            self.messgebiet = Messgebiet.Messgebiet(self.AktuelleSensordaten[0].daten[0], self.AktuelleSensordaten[0].daten[1], self.messgebiet_ausdehnung[1], self.messgebiet_ausdehnung[0])

            # Anlegen eines Sterns mit zeitgleicher Messung (Funktion "Erkunden" ist für die Dauer der Messung gefroren)
            self.SternAbfahren(self.position, self.heading, initial=True)
            self.messgebiet.stern = self.stern
            self.messgebiet.topographische_punkte = self.stern.TopographischBedeutsamePunkteAbfragen()

            # Definition der Profile und topographisch bedeutsamer Punkte
            self.messgebiet.ProfileEinlesen(self.stern.Profile())

            # der Name sagts
            self.VerdichtendeFahrten()

            self.fortlaufende_aktualisierung = False
            self.boot_lebt = False
            
            print(self.gefahreneStrecke)
            #self.originalmesh.plot()
            #tin.plot()
            self.messgebiet.tin.Vergleich_mit_Original(self.originalmesh) # Nur im Simualtor möglich
            self.messgebiet.tin.mesh.save("gemessenePunktwolke.ply")
            
            #self.messgebiet.tin.plot()

            self.messgebiet.profile = self.stern.Profile()
            #(self.messgebiet.profile)
        threading.Thread(target=erkunden_extern, args=(self, ), daemon=True).start()

    def VerdichtendeFahrten(self):
        self.tracking_mode = Messgebiet.TrackingMode.VERBINDUNG
        self.messgebiet.Verdichtungsmode(Messgebiet.Verdichtungsmode.KANTEN)
        self.punkt_anfahren = False
        print("///////////////////////////////////////////////")
        while self.boot_lebt:
            abbruch_durch_ufer = (self.ist_am_ufer[0] == UferPosition.AM_UFER and self.ist_am_ufer[1])
            if abbruch_durch_ufer or not self.punkt_anfahren:
                self.punkt_anfahren = False  # falls das Boot am Ufer angekommen ist, soll das Boot nicht weiter fahren
                self.ufererkennung_aktiv = False
                time.sleep(self.akt_takt * 2)  # warten, bis der Thread zum Ansteuern eines Punktes terminiert

                # Medianpunkte ins aktuelle Profil einlesen, um daraus (auch in diesem Schritt) die topographisch bedeutsamen Punkte zu ermitteln
                if self.tracking_mode == Messgebiet.TrackingMode.PROFIL or self.tracking_mode == Messgebiet.TrackingMode.VERBINDUNG:
                    self.messgebiet.AktuellesProfilBeenden(self.position, self.median_punkte)
                    self.median_punkte = []

                # Abfragen des neuen Punkts (TIN berechnen, neue Kanten finden und bewerten, anzufahrenden Punkt ausgeben)
                neuer_punkt = self.messgebiet.NaechsterPunkt(self.position, abbruch_durch_ufer)

                if neuer_punkt is None:
                    break
                self.punkt_anfahren = True
                self.Punkt_anfahren(neuer_punkt)
                time.sleep(self.akt_takt * 10)  # beide Sleeps sind identisch mit denen in SternAbfahren()
            time.sleep(self.akt_takt/2)

    # gibt alle weiteren anzufahrenden Kanten aus
    def KantenPlotten(self):
        if self.messgebiet is None:
            return []
        else:
            return self.messgebiet.anzufahrende_kanten

    def GeschwindigkeitSetzen(self, geschw):
        self.PixHawk.Geschwindigkeit_setzen(geschw)

    # TODO: evtl Rechteck abhängig von Geschw. oder direkt Rechteck um das Boot legen
    # TODO: toleranz muss auf die Pixhawk interne Toleranz passen (Pixhawk-Toleranz muss kleiner gleich toleranz sein)
    def Punkt_anfahren(self, punkt, geschw =2.0, toleranz=10):  # Utm-Koordinaten und Gechwindigkeit setzen
        self.PixHawk.Geschwindigkeit_setzen(geschw)
        self.PixHawk.Wegpunkt_anfahren(punkt.x, punkt.y)
        self.punkt_anfahren = True
        #print("Fahre Punkt mit Koordinaten E:", punkt.x, "N:", punkt.y, "an")
        punkt_box = Messgebiet.Zelle(punkt.x, punkt.y, toleranz, toleranz)
        sollheading = self.Headingberechnung(punkt)

        def punkt_anfahren_test(self):
            if self.tracking_mode.value <= 10:
                self.Ufererkennung(sollheading)
            self.punkt_anfahren = True
            while self.punkt_anfahren and self.boot_lebt:
                t = time.time()
                test = punkt_box.enthaelt_punkt(self.position)
                if test:
                    self.punkt_anfahren = False
                schlafen = max(0, (self.akt_takt / 2) - (time.time() - t))
                time.sleep(schlafen)
        thread = threading.Thread(target=punkt_anfahren_test, args=(self, ), daemon=True)
        thread.start()

    def Wegberechnung(self):
        pass

    def SternAbfahren(self, startpunkt, heading, initial=True):
        self.Ufererkennung(heading)
        self.stern = Messgebiet.Stern(startpunkt, heading, self.stern_winkelinkrement, self.stern_grzw_seitenlaenge, initial, self.profil_grzw_dichte_topographischer_punkte, self.profil_grzw_neigungen_topographischer_punkte)
        self.tracking_mode = Messgebiet.TrackingMode.PROFIL
        punkt = self.stern.InitProfil()
        self.Punkt_anfahren(punkt)
        while self.boot_lebt:
            if (self.ist_am_ufer[0] == UferPosition.AM_UFER and self.ist_am_ufer[1] and self.tracking_mode.value <= 10) or not self.punkt_anfahren:
                print("in Stern abfahren: self position", self.position, "self.heading", self.heading, "ist_am_ufer", self.ist_am_ufer, "tracking", self.tracking_mode, "self.punt anfahren", self.punkt_anfahren)
                #print("Stern abfahren nächste aktion")
                self.punkt_anfahren = False # falls das Boot am Ufer angekommen ist, soll das Boot nicht weiter fahren
                self.ufererkennung_aktiv = False
                time.sleep(self.akt_takt) # warten, bis der Thread zum Ansteuern eines Punktes terminiert
                #if len(self.median_punkte) > 1:
                if self.tracking_mode == Messgebiet.TrackingMode.PROFIL or self.tracking_mode == Messgebiet.TrackingMode.VERBINDUNG:
                    self.stern.MedianPunkteEinlesen(self.median_punkte)
                self.median_punkte = []
                [neuer_kurspunkt, neues_tracking] = self.stern.NaechsteAktion(self.position, self.tracking_mode)
                #print("in Stern abfahren: neuer kurspunkt und neues tracking", neuer_kurspunkt, neues_tracking)
                #print("==== ENDE DER PRINTS IN STERN ABFAHREN ====")
                self.tracking_mode = neues_tracking
                if neuer_kurspunkt is None:
                    break
                self.punkt_anfahren = True
                self.Punkt_anfahren(neuer_kurspunkt)
                #TODO: warum muss hier 10*self.akt_takt stehen? (5fach reicht nicht, hat das was mit der Datengrundlage zu tun (dass also Ufer erkannt wird wenn zu früh gestartet wird oder müssen die anderen Threads wirklich erst anlaufen?)
                time.sleep(self.akt_takt*10) # die Threads zum Anfahren müssen erstmal anlaufen, sonst wird direkt oben wieder das if durchlaufen
            time.sleep(self.akt_takt/2)
        self.stern_beendet = True
        self.median_punkte = []

    def Gewaesseraufnahme(self):
        pass

    def Boot_stoppen(self):

        self.Punkt_anfahren(self.AktuelleSensordaten[0].daten[0], self.AktuelleSensordaten[0].daten[1], 0.5)
        print("Notstopp! Letzte Posotion wird langsam angefahren")

        #todo: Notstopp richtig implementieren

    def Trennen(self):

        for sensor in self.Sensorliste:
            sensor.kill()
        self.datenbankbeschreiben = False
        time.sleep(0.2)
        if self.db_verbindung:
            self.db_zeiger.close()
            self.db_verbindung.close()

        if self.PixHawk.verbindung_hergestellt:
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

    # Berechnet das Gefälle unterhalb des Bootes
    # sollte höchstens alle paar Sekunden aufgerufen werden, spätestens bei der Profilberechnung
    def Hydrographische_abfrage(self, punkt):
        """
        :param punkt: Punkt des Bootes
        :return: Liste mit Vektor der größten Steigung (Richtung gemäß Vektor und für Betrag gilt: arcsin(betrag) = Steigungswinkel) und Angabe, ob flächenhaft um das Boot herum gesucht wurde (True) oder ob nur 1-dim Messungen herangezogen wurden (False)
        """
        punkte = self.Daten_abfrage(punkt)
        fläche = Messgebiet.Flächenberechnung(punkte[0], punkte[1])

        if fläche < 5: # dann sind nur Punkte enthalten, die vermutlich aus den momentanen Messungen herrühren

            # Ausgleichsgerade und Gradient auf Kurs projizieren (<- Projektion ist implizit, da die zuletzt aufgenommenen Punkte auf dem Kurs liegen müssten)
            n_pkt = int(len(punkte[0]))  # Anzahl Punkte
            p1 = numpy.array([punkte[0][0], punkte[1][0], punkte[2][0]])
            p2 = numpy.array([punkte[0][-1], punkte[1][-1], punkte[2][-1]])
            r0 = p2 - p1
            d12 = numpy.linalg.norm(r0)
            r0 = r0 / d12 # Richtungsvektor
            st0 = p1 - numpy.dot(r0, p1) * r0 # Stützvektor, senkrecht auf Richtungsvektor
            L = []
            temp = numpy.matrix(numpy.array([1, 0, 0] * n_pkt)).getT()  # Erste Spalte der A-Matrix
            A = temp  # A-Matrix ist folgendermaßen aufgebaut: Unbekannte in Spalten: erst 3 Komp. des Stützvektors, dann alle lambdas
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

            # "Standardabweichung": Mittlerer Abstand der Punkte von der Geraden, aber nur in z-Richtung!
            v = []
            n_u = len(punkte[0][0] - len(lambdas))
            for i, lamb in enumerate(lambdas):
                z_ist = punkte[2][i]
                z_ausgl = X_dach[2, 0] + lamb * r0[2]
                v.append(z_ist - z_ausgl)
            v = numpy.array(v)
            s0 = numpy.linalg.norm(v) / n_u

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
            v = punkte[2] - (x_dach[0, 0]*punkte[0] + x_dach[0, 1]*punkte[1] + x_dach[0, 2]) # L - (alle_x_als_vec * a + alle_y_als_vec * b + c), abc als Unbekannte in x_dach
            s0 = numpy.linalg.norm(v) / (numpy.sqrt(len(punkte[0])) - 3)
        return [max_steigung, flächenhaft, s0]


    # Fragt Daten aus der DB im "Umkreis" (Bounding Box) von radius Metern des punktes (Boot) ab
    # ST_Distance ist nicht sargable! (kann nicht zusammen mithilfe eines Index beschleunigt werden)
    # https://stackoverflow.com/questions/35093608/spatial-index-not-being-used
    # für Beschleunigung über PostGIS (PostgreSQL): https://gis.stackexchange.com/questions/123911/st-distance-doesnt-use-index-for-spatial-query
    # https://dba.stackexchange.com/questions/214268/mysql-geo-spatial-query-is-very-slow-although-index-is-used)
    def Daten_abfrage(self, punkt, radius=20):
        x = []
        y = []
        tiefe = []
        gnss_pkt = self.Sensornamen[0] + "_punkt" # Name des DB-Feldes des Punkts der ersten GNSS-Antenne
        echolot_tiefe = "`" + self.Sensornamen[2] + "_tiefe1`"
        p1 = [punkt[0] - radius / 2, punkt[1] - radius / 2]
        p2 = [punkt[0] + radius / 2, punkt[1] + radius / 2]
        db_string = "SELECT ST_X(" + self.db_table + "." + gnss_pkt + "), ST_Y(" + self.db_table + "." + gnss_pkt + "), " + echolot_tiefe + " FROM " + self.db_database + ".`" + self.db_table + "` WHERE MbrContains(ST_GeomFromText('LINESTRING(" + str(p1[0]) + " " + str(p1[1]) + ", " + str(p2[0]) + " " + str(p2[1]) + ")', 25832), " + self.db_table + "." + gnss_pkt + ");"
        self.db_zeiger.execute(db_string)
        self.db_zeiger.commit()
        for pkt in self.db_zeiger.fetchall():
            x.append(pkt[0])
            y.append(pkt[1])
            tiefe.append(pkt[2])
        return [numpy.array(x), numpy.array(y), numpy.array(tiefe)]


# Zum Testen
if __name__=="__main__":

    Boot = Boot()

    Boot.Sensorwerte_auslesen()
    time.sleep(5)

    Boot.Datenbank_beschreiben()
    time.sleep(10)

    Boot.Trennen()
