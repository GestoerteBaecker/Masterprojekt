import Boot
import csv
import json
import Messgebiet
import numpy
import Sensoren
import shapely.geometry as shp
import shapely
shapely.speedups.disable()
import statistics
import threading
import time
import matplotlib.pyplot as plt
plt.ion()


class Boot_Simulation(Boot.Boot):

    def __init__(self):

        super().__init__()
        ################################# S I M U L A T I O N ##########################################################
        #SIMULATIONSPARAMETER
        # Einlesen der Parameter aus JSON Datei

        self.akt_takt = self.akt_takt / self.Faktor #Faktor zum Beschleunigen oder verlangsamen der Simulation ... Bei echter messung auf 1 setzten
        self.db_takt = self.akt_takt

        datei = open("boot_init.json", "r")
        json_daten = json.load(datei)
        datei.close()

        xpos1_start_sim = json_daten["Boot"]["simulation_start_x"]
        ypos1_start_sim = json_daten["Boot"]["simulation_start_y"]
        self.position = Messgebiet.Punkt(xpos1_start_sim, ypos1_start_sim)
        self.position_sim = Messgebiet.Punkt(xpos1_start_sim, ypos1_start_sim)
        self.heading = json_daten["Boot"]["simulation_start_heading"]
        self.heading_sim = json_daten["Boot"]["simulation_start_heading"]
        self.suchbereich = json_daten["Boot"]["simulation_suchbereich"]
        datengrundlage = json_daten["Boot"]["referenzmodell"] # "original", "transportkoerper", "container"

        self.PixHawk.verbindungsversuch = False

        # EINLESEN DES MODELLS ALS QUADTREE
        testdaten = open("Referenz_Tweel_ges.txt", "r", encoding='utf-8-sig')  # ArcGIS Encoding XD
        lines = csv.reader(testdaten, delimiter=";")
        x_testdaten = []
        y_testdaten = []
        tiefe_testdaten = []
        z_id = 2
        if datengrundlage == "original":
            z_id = 2
        elif datengrundlage == "transportkoerper":
            z_id = 3
        elif datengrundlage == "container":
            z_id = 4

        # Lesen der Datei für manipulierte Datei
        for line in lines:
            x_testdaten.append(float(line[0]))
            y_testdaten.append(float(line[1]))
            tiefe_testdaten.append(float(line[z_id]))
        testdaten.close()

        testdaten_xmin = min(x_testdaten) - 10
        testdaten_xmax = max(x_testdaten) + 10
        testdaten_ymin = min(y_testdaten) - 10
        testdaten_ymax = max(y_testdaten) + 10

        xdiff = testdaten_xmax - testdaten_xmin
        ydiff = testdaten_ymax - testdaten_ymin
        xzentrum = testdaten_xmin + xdiff / 2
        yzentrum = testdaten_ymin + ydiff / 2

        # Einlesen der Testdaten
        initialrechteck = Messgebiet.Zelle(xzentrum, yzentrum, xdiff, ydiff)
        self.Testdaten_quadtree = Messgebiet.Uferpunktquadtree(initialrechteck)

        Punktliste = []
        # Generieren des Quadtree
        for i in range(len(x_testdaten)):
            x = x_testdaten[i]
            y = y_testdaten[i]
            tiefe = tiefe_testdaten[i]

            p = Messgebiet.Bodenpunkt(x, y, tiefe)
            Punktliste.append(p)

            self.Testdaten_quadtree.punkt_einfuegen(p)

        # Anlegen der Referenzoberfläche
        self.originalmesh = Messgebiet.TIN(Punktliste, 10, nurTIN=True)
        self.originalmesh.mesh.save("Originalmesh.ply")

        # EINLESEN DES TEST POLYGONS
        testdaten_path = open("Testdaten_Polygon.txt", "r")
        lines = csv.reader(testdaten_path, delimiter=";")
        testdaten = []

        # Lesen der Datei
        for line in lines:
            testdaten.append(tuple([float(komp) for komp in line]))
        testdaten_path.close()
        self.ufer_polygon = shp.LinearRing(testdaten)
        self.umrandung = shp.Polygon(testdaten)
        ### TEST ###
        self.test = 0

        ################################################################################################################
        ################################################################################################################

    # wird im self.akt_takt aufgerufen und überschreibt self.AktuelleSensordaten mit den neusten Sensordaten
    def Datenaktualisierung(self):

        if not self.auslesen:
            self.Sensorwerte_auslesen()

        self.fortlaufende_aktualisierung = True

        def simulation(self):
            while self.fortlaufende_aktualisierung and self.boot_lebt:
                t = time.time()
                ########## S I M U L A T I O N #############################################################
                with Messgebiet.schloss:
                    position = self.position_sim
                    heading = self.heading_sim
                suchgebiet = Messgebiet.Zelle(position.x, position.y, self.suchbereich, self.suchbereich)
                tiefenpunkte = self.Testdaten_quadtree.abfrage(suchgebiet)
                tiefe = statistics.mean([pkt.z for pkt in tiefenpunkte])
                gnss2 = PolaresAnhaengen(position, heading, dist=1)
                kurs = PolaresAnhaengen(position, heading, dist=1000)

                p1, p2 = numpy.array([position.x, position.y]), numpy.array([kurs.x, kurs.y])
                strahl = shp.LineString([(position.x, position.y), (kurs.x, kurs.y)])
                # Prüfen ob Punkt in Umringspolygon liegt
                #impolygon = shp.Point(self.position.x,self.position.y).within(self.umrandung)

                schnitt = self.ufer_polygon.intersection(strahl)

                if type(schnitt).__name__ == "MultiPoint":
                    schnitt = [numpy.array([pkt.x, pkt.y]) for pkt in schnitt]
                else:
                    try:
                        schnitt = [numpy.array([schnitt.x, schnitt.y])]
                    except:
                        print('Schnittpunkt nicht bestimmbar')
                        continue
                # Finden des Punkts, der das Ufer als erstes schneidet
                ufer_punkt = None
                diff = p2 - p1
                skalar = numpy.inf
                for pkt in schnitt:
                    diff_pkt = pkt - p1
                    skalar_test = diff_pkt[0] * diff[0] + diff_pkt[1] * diff[1]
                    if skalar_test >= 2: # näher als 2 * Strecke zwischen
                        if skalar_test < skalar:
                            skalar = skalar_test
                            ufer_punkt = pkt
                if ufer_punkt is None:
                    distanz = 1000
                else:
                    #TODO: Abfangen, dass die Distanz mal nicht gegeben sein kann
                    distanz = ((ufer_punkt[0] - p1[0]) ** 2 + (ufer_punkt[1] - p1[1]) ** 2) ** 0.5

                with Messgebiet.schloss:
                    self.AktuelleSensordaten[0] = Sensoren.Daten(0, [position.x, position.y, 0, 0, 4], time.time())
                    self.AktuelleSensordaten[1] = Sensoren.Daten(0, [gnss2.x, gnss2.y, 0, 0, 4], time.time())
                    self.AktuelleSensordaten[2] = Sensoren.Daten(0, [tiefe, tiefe], time.time())
                    self.AktuelleSensordaten[3] = Sensoren.Daten(0, distanz, time.time())
                schlafen = max(0, (self.akt_takt/2) - (time.time() - t))
                time.sleep(schlafen)
                ###########################################################################################

        threading.Thread(target=simulation, args=(self,), daemon=True).start()

        def Ueberschreibungsfunktion(self):

            Letzte_Bodenpunkte = []
            while self.fortlaufende_aktualisierung and self.boot_lebt:
                t = time.time()
                self.test += 1

                # auslesen der geteilten Variablen
                with Messgebiet.schloss:

                    gnss1 = self.AktuelleSensordaten[0]
                    gnss2 = self.AktuelleSensordaten[1]
                    echolot = self.AktuelleSensordaten[2]
                    disto = self.AktuelleSensordaten[3]
                    track_mode = self.tracking_mode.value

                # Abgeleitete Daten berechnen und überschreiben
                Bodenpunkt = None
                position = None

                # wenn ein aktueller Entfernungsmesswert besteht, soll ein Uferpunkt berechnet werden
                if gnss1 and gnss2 and disto:  # Uferpunktberechnung
                    position = Messgebiet.Punkt(gnss1.daten[0], gnss1.daten[1])
                    uferpunkt = self.Uferpunktberechnung()
                    if self.messgebiet != None:
                        self.messgebiet.Uferpunkt_abspeichern(uferpunkt)

                # Tiefe berechnen und als Punktobjekt abspeichern (die letzten 10 Messwerte mitteln)
                if gnss1 and echolot:
                    Bodendaten = (gnss1, echolot)
                    Letzte_Bodenpunkte.append(Bodendaten)

                    if len(Letzte_Bodenpunkte) > self.anz_Bodenpunkte:
                        Bodenpunkt = self.Bodenpunktberechnung(Letzte_Bodenpunkte)
                        Letzte_Bodenpunkte = []

                # aktuelles Heading berechnen und zum Boot abspeichern
                if self.AktuelleSensordaten[0] and self.AktuelleSensordaten[1]:         # Headingberechnung
                    self.heading = self.Headingberechnung()


                # setzen der geteilten Variablen
                with Messgebiet.schloss:

                    if position is not None:
                        self.position = position

                    # Letzte zwei Bodenpunkte zur Extrapolation zur Ufererkennung
                    if Bodenpunkt is not None:
                        self.Bodenpunkte.append(Bodenpunkt)
                        if len(self.Bodenpunkte) > 2:
                            self.Bodenpunkte.pop(0)
                        # je nach Tracking Mode sollen die Median Punkte mitgeführt werden oder aus der Liste gelöscht werden (da sie ansonsten bei einem entfernt liegenden Profil mit berücksichtigt werden würden)
                        if track_mode < 2:
                            self.median_punkte.append(Bodenpunkt)
                            self.median_punkte_alle.append(Bodenpunkt)

                schlafen = max(0, (self.akt_takt - (time.time() - t)))
                time.sleep(schlafen)

        threading.Thread(target=Ueberschreibungsfunktion, args=(self, ), daemon=True).start()

        time.sleep(0.2)
        if not self.PixHawk.homepoint:
            with Messgebiet.schloss:
                punkt = Messgebiet.Punkt(self.AktuelleSensordaten[0].daten[0], self.AktuelleSensordaten[0].daten[1])
                self.PixHawk.homepoint = punkt


    # nicht mehr anpacken, läuft
    def Punkt_anfahren(self, punkt, geschw=5.0):  # Utm-Koordinaten und Gechwindigkeit setzen
        self.punkt_anfahren = True
        with Messgebiet.schloss:
            self.heading_sim = self.Headingberechnung(punkt)

        distanz = self.position.Abstand(punkt)
        testprofil = Messgebiet.Profil(self.heading_sim, self.position, True, 0, distanz+10)
        testprofil.ist_definiert = Messgebiet.Profil.Definition.START_UND_ENDPUNKT
        profilpunkte = testprofil.BerechneZwischenpunkte(0.25)    #(geschw*(self.akt_takt*self.Faktor))

        def inkrementelles_anfahren(self, profilpunkte, index=0):
            while self.punkt_anfahren and self.boot_lebt:
                alte_position = self.position
                with Messgebiet.schloss:
                    self.position_sim = profilpunkte[index]
                    index += 1
                    entfernung = self.position_sim.Abstand(alte_position)
                    self.gefahreneStrecke += entfernung
                time.sleep(self.akt_takt/2)
        threading.Thread(target=inkrementelles_anfahren, args=(self, profilpunkte), daemon=True).start()

        punkt_box = Messgebiet.Zelle(punkt.x, punkt.y, self.anfahrtoleranz, self.anfahrtoleranz)

        def punkt_anfahren_test(self):
            if self.tracking_mode.value <= 10:
                self.Ufererkennung(self.heading)
            self.punkt_anfahren = True
            while self.punkt_anfahren and self.boot_lebt:
                test = punkt_box.enthaelt_punkt(self.position)
                if test:
                    self.punkt_anfahren = False
                time.sleep(self.akt_takt/20)
        thread = threading.Thread(target=punkt_anfahren_test, args=(self, ), daemon=True)
        thread.start()


def PolaresAnhaengen(position, heading, dist):

    e = position.x + numpy.sin(heading / (200 / numpy.pi)) * dist
    n = position.y + numpy.cos(heading / (200 / numpy.pi)) * dist

    return Messgebiet.Punkt(e, n)