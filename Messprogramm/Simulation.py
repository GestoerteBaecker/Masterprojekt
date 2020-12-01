import Boot
import csv
import json
import Messgebiet
import numpy
import random
import Sensoren
import shapely.geometry as shp
import shapely
shapely.speedups.disable()
import statistics
import sympy
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
        datei = open("boot_init.json", "r")
        json_daten = json.load(datei)
        datei.close()

        xpos1_start_sim = json_daten["Boot"]["simulation_start_x"]
        ypos1_start_sim = json_daten["Boot"]["simulation_start_y"]
        self.position = Messgebiet.Punkt(xpos1_start_sim, ypos1_start_sim)
        self.heading = json_daten["Boot"]["simulation_start_heading"]
        self.suchbereich = json_daten["Boot"]["simulation_suchbereich"]
        self.akt_takt = json_daten["Boot"]["simulation_aktualisierungstakt"]

        # EINLESEN DES MODELLS ALS QUADTREE
        testdaten = open("Testdaten_DHM_Tweelbaeke.txt", "r", encoding='utf-8-sig')  # ArcGIS Encoding XD
        lines = csv.reader(testdaten, delimiter=";")
        id_testdaten = []
        x_testdaten = []
        y_testdaten = []
        tiefe_testdaten = []

        # Lesen der Datei
        for line in lines:
            id_testdaten.append(int(line[0]))
            x_testdaten.append(float(line[1]))
            y_testdaten.append(float(line[2]))
            tiefe_testdaten.append(float(line[3]))
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

        # Generieren des Quadtree
        for i in range(len(x_testdaten)):
            x = x_testdaten[i]
            y = y_testdaten[i]
            tiefe = tiefe_testdaten[i]

            p = Messgebiet.Bodenpunkt(x, y, tiefe)

            self.Testdaten_quadtree.punkt_einfuegen(p)

        # EINLESEN DES TEST POLYGONS
        testdaten_path = open("Testdaten_Polygon.txt", "r")
        lines = csv.reader(testdaten_path, delimiter=";")
        testdaten = []

        # Lesen der Datei
        for line in lines:
            testdaten.append(tuple([float(komp) for komp in line]))
        testdaten_path.close()
        self.ufer_polygon = shp.LinearRing(testdaten)

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
                    position = self.position
                    heading = self.heading
                suchgebiet = Messgebiet.Zelle(position.x, position.y, self.suchbereich, self.suchbereich)
                tiefenpunkte = self.Testdaten_quadtree.abfrage(suchgebiet)
                #print("erstes print", time.time()-t)
                #t_test = time.time()
                tiefe = statistics.mean([pkt.z for pkt in tiefenpunkte])

                gnss2 = PolaresAnhaengen(position, heading, dist=1)
                kurs = PolaresAnhaengen(position, heading, dist=1000)

                p1, p2 = numpy.array([position.x, position.y]), numpy.array([kurs.x, kurs.y])
                strahl = shp.LineString([(position.x, position.y), (kurs.x, kurs.y)])
                #print("zweites print", time.time()-t_test)
                #t_test = time.time()
                schnitt = self.ufer_polygon.intersection(strahl)
                if type(schnitt).__name__ == "MultiPoint":
                    schnitt = [numpy.array([pkt.x, pkt.y]) for pkt in schnitt]
                else:
                    schnitt = [numpy.array([schnitt.x, schnitt.y])]
                #print("drittes print", time.time() - t_test)
                #t_test = time.time()
                # Finden des Punkts, der das Ufer als erstes schneidet
                ufer_punkt = None
                diff = p2 - p1
                skalar = numpy.inf
                for pkt in schnitt:
                    #pkt = numpy.array([schnitt[i][0], schnitt[i][1]])
                    diff_pkt = pkt - p1
                    skalar_test = diff_pkt[0] * diff[0] + diff_pkt[1] * diff[1]
                    if skalar_test >= 2: # näher als 2 * Strecke zwischen
                        if skalar_test < skalar:
                            skalar = skalar_test
                            ufer_punkt = pkt
                if ufer_punkt is None:
                    distanz = 1000
                    print("Ausnahme bei der Distanz. self.heading ist ", self.heading)
                    print("position", self.position, "strahl", strahl, "polygon", self.ufer_polygon)
                else:
                    #print("schnittpunkte", schnitt)
                    #TODO: Anfangen, dass die Distanz mal nicht gegeben sein kann
                    distanz = ((ufer_punkt[0] - p1[0]) ** 2 + (ufer_punkt[1] - p1[1]) ** 2) ** 0.5
                    distanz = random.gauss(distanz, 0.1)
                #print("viertes print", time.time()-t_test)
                with Messgebiet.schloss:
                    self.AktuelleSensordaten[0] = Sensoren.Daten(0, [position.x, position.y, 0, 0, 4], time.time())
                    self.AktuelleSensordaten[1] = Sensoren.Daten(0, [gnss2.x, gnss2.y, 0, 0, 4], time.time())
                    self.AktuelleSensordaten[2] = Sensoren.Daten(0, [tiefe, tiefe], time.time())
                    self.AktuelleSensordaten[3] = Sensoren.Daten(0, distanz, time.time())

                schlafen = max(0, self.akt_takt - (time.time() - t))
                #print("self.position simulation", position, "benötigte Zeit", time.time() - t, "schlafen", schlafen, "self.test", self.test, "threadname", threading.get_ident(), "zeit", time.time())
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

                # aktuelles Heading berechnen und zum Boot abspeichern
                #heading = self.Headingberechnung()

                # wenn ein aktueller Entfernungsmesswert besteht, soll ein Uferpunkt berechnet werden
                if gnss1 and gnss2 and disto:  # Uferpunktberechnung
                    #print("bootsmitte", [gnss1.daten[0], gnss1.daten[1]])
                    position = Messgebiet.Punkt(gnss1.daten[0], gnss1.daten[1])
                    uferpunkt = self.Uferpunktberechnung()
                    if self.Messgebiet != None:
                        Messgebiet.Uferpunkt_abspeichern(uferpunkt)

                # Tiefe berechnen und als Punktobjekt abspeichern (die letzten 10 Messwerte mitteln)
                if gnss1 and echolot:
                    Bodendaten = (gnss1, echolot)
                    Letzte_Bodenpunkte.append(Bodendaten)

                    if len(Letzte_Bodenpunkte) > 10:
                        Bodenpunkt = self.Bodenpunktberechnung(Letzte_Bodenpunkte)
                        Letzte_Bodenpunkte = []

                # setzen der geteilten Variablen
                with Messgebiet.schloss:
                    #if heading is not None:
                    #    self.heading = heading
                    #print("aktualisiertes heading", self.heading)

                    if position is not None:
                        self.position = position

                    if Bodenpunkt is not None:
                        self.Bodenpunkte.append(Bodenpunkt)
                        if len(self.Bodenpunkte) > 2:
                            self.Bodenpunkte.pop(0)
                        # je nach Tracking Mode sollen die Median Punkte mitgeführt werden oder aus der Liste gelöscht werden (da sie ansonsten bei einem entfernt liegenden Profil mit berücksichtigt werden würden)
                        if track_mode < 2:
                            print("medianpunkt", Bodenpunkt)
                            self.median_punkte.append(Bodenpunkt)

                    #print("self.position", self.position, "benötigte Zeit", time.time() - t, "self.test", self.test, "threadname", threading.get_ident(), "zeit", time.time())

                schlafen = max(0, self.akt_takt - (time.time() - t))
                time.sleep(schlafen)

        threading.Thread(target=Ueberschreibungsfunktion, args=(self, ), daemon=True).start()

        time.sleep(2)
        if not self.PixHawk.homepoint:
            with Messgebiet.schloss:
                punkt = Messgebiet.Punkt(self.AktuelleSensordaten[0].daten[0], self.AktuelleSensordaten[0].daten[1])
                self.PixHawk.homepoint = punkt


    #TODO: nicht mehr anpacken, läuft
    def Punkt_anfahren(self, punkt, geschw=5.0, toleranz=10):  # Utm-Koordinaten und Gechwindigkeit setzen

        self.punkt_anfahren = True
        with Messgebiet.schloss:
            self.heading = self.Headingberechnung(punkt)
        print("Fahre Punkt mit Koordinaten E:", punkt.x, "N:", punkt.y, "an")

        distanz = self.position.Abstand(punkt)
        testprofil = Messgebiet.Profil(self.heading, self.position, True, 0, distanz)
        testprofil.ist_definiert = Messgebiet.Profil.Definition.START_UND_ENDPUNKT
        profilpunkte = testprofil.BerechneZwischenpunkte(geschw*(self.akt_takt/2))

        #print("Liste der anzufahrenden Punkte auf dem Profil", len(profilpunkte), [str(punkt) for punkt in profilpunkte])

        def inkrementelles_anfahren(self, profilpunkte, index=0):
            while self.punkt_anfahren:
                with Messgebiet.schloss:
                    self.position = profilpunkte[index]
                    index += 1
                    #print("hier wird self.position geändert", self.position, "threadname", threading.get_ident())
                time.sleep(self.akt_takt/2)
        threading.Thread(target=inkrementelles_anfahren, args=(self, profilpunkte), daemon=True).start()

        punkt_box = Messgebiet.Zelle(punkt.x, punkt.y, toleranz, toleranz)

        def punkt_anfahren_test(self):
            if self.tracking_mode.value <= 10:
                self.Ufererkennung(self.heading)
            self.punkt_anfahren = True
            while self.punkt_anfahren:
                test = punkt_box.enthaelt_punkt(self.position)
                #print("hier wird self.position benutzt, ufererkennung", self.position, "threadname", threading.get_ident())
                if test:
                    self.punkt_anfahren = False
                time.sleep(self.akt_takt/2)
        thread = threading.Thread(target=punkt_anfahren_test, args=(self, ), daemon=True)
        thread.start()


def PolaresAnhaengen(position, heading, dist):

    e = position.x + numpy.sin(heading / (200 / numpy.pi)) * dist
    n = position.y + numpy.cos(heading / (200 / numpy.pi)) * dist

    return Messgebiet.Punkt(e, n)


if __name__ == "__main__":
    # EINLESEN DES TEST POLYGONS
    testdaten_path = open("Testdaten_Polygon.txt", "r")
    lines = csv.reader(testdaten_path, delimiter=";")
    testdaten_poly = []

    # Lesen der Datei
    for line in lines:
        testdaten_poly.append(sympy.Point(tuple([float(komp) for komp in line])))
    testdaten_path.close()
    ufer_polygon = sympy.Polygon(*testdaten_poly)

    p1, p2 = sympy.Point(451914.7237857745, 26869983909136309080730271 / 4565964803450000000-2), sympy.Point(451914.7237857745, 26869983909136309080730271 / 4565964803450000000)
    line = sympy.Line(p1, p2)

    schnitt = line.intersection(ufer_polygon)

    # EINLESEN DES MODELLS ALS QUADTREE
    testdaten = open("Testdaten_DHM_Tweelbaeke.txt", "r", encoding='utf-8-sig')  # ArcGIS Encoding XD
    lines = csv.reader(testdaten, delimiter=";")
    id_testdaten = []
    x_testdaten = []
    y_testdaten = []
    tiefe_testdaten = []

    # Lesen der Datei
    for line in lines:
        id_testdaten.append(int(line[0]))
        x_testdaten.append(float(line[1]))
        y_testdaten.append(float(line[2]))
        tiefe_testdaten.append(float(line[3]))

    testdaten.close()
    figure, ax = plt.subplots()
    ax.plot([451914.7237857745, 451914.7237857745], [26869983909136309080730271 / 4565964803450000000-2, 26869983909136309080730271 / 4565964803450000000], lw=1)
    ax.scatter([x_testdaten], [y_testdaten])
    ax.scatter([451880], [5884944], marker='o')
    ax.plot()

    x=[]
    y=[]


    x_poly = []
    y_poly = []
    for polypunkt in testdaten_poly:
        x_poly.append(polypunkt.x)
        y_poly.append(polypunkt.y)



    schnitt_poly,=ax.plot([],[],marker='o',lw=0)

    ax.plot(x_poly,y_poly,lw=2)

    while True:

        for schnittpunkt in schnitt:
            x.append(schnittpunkt.x)
            y.append(schnittpunkt.y)

            schnitt_poly.set_xdata(x)
            schnitt_poly.set_ydata(y)

            plt.pause(0.5)



    i=0