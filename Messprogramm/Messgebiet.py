import copy
import enum
import itertools
import matplotlib.pyplot as plt
plt.ion() # Aktivieren eines dynamischen Plots
import numpy
import pyvista as pv
import statistics
import threading
from scipy.spatial import KDTree

schloss = threading.RLock()

# Definition von Enums zur besseren Lesbarkeit
# Tracking Mode, das das Boot haben soll
class TrackingMode(enum.Enum):
    # ab hier soll Tracking und Ufererkennung erfolgen
    PROFIL = 0 # volles Tracking
    VERBINDUNG = 1 # auf Verbindungsstück zwischen zwei verdichtenden Profilen; ausgedünntes Tracking
    # ab hier soll kein Tracking erfolgen
    UFERERKENNUNG = 10 # kein Tracking, aber Ufererkennung
    # ab hier weder Ufererkennung noch Tracking
    BLINDFAHRT = 20

# Definition von Enums zur besseren Lesbarkeit
# dient dem Differenzieren des Anfahrens von Punkten bei den verdichtenden Kanten
class Verdichtungsmode(enum.Enum):
    # das Boot ist zurzeit noch mit dem Stern beschäftigt
    AUS = -1
    # Abfahren zwischen den Punkten einer verdichtenden Kante
    KANTEN = 0
    # Abfahren zwischen den Endpunkt eines Profils und dem Startpunkt des folgenden Profils
    VERBINDUNG = 1
    # Falls das Boot während einer Verbindungsfahrt ans Ufer gerät, soll es anderweitig über kleinere Umwege zu dem abzufahrenden Profil geführt werden
    WEGFÜHRUNG = 2

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

class Punkt:

    id = 0

    def __init__(self, x, y, z=None):
        self.id = Punkt.id
        Punkt.id += 1
        self.x = x
        self.y = y
        self.z = z
        self.zelle = self.Zellenzugehoerigkeit()

    def Zellenzugehoerigkeit(self):

        # gibt Rasterzelle des Punktes wieder; größe der Rasterzellen muss bekannt sein
        # oder Liste aller Rasterzellen iterieren und Methode enthaelt_punkt() verwenden
        pass

    def Abstand(self, pkt, zwei_dim=False):
        summe = (self.x - pkt.x)**2 + (self.y - pkt.y)**2
        if self.z is not None and pkt.z is not None and not zwei_dim:
            summe += (self.z - pkt.z)**2
        return numpy.sqrt(summe)

    def ZuNumpyPunkt(self, zwei_dim=False):
        if self.z is not None and not zwei_dim:
            punkt = numpy.array([self.x, self.y, self.z])
        else:
            punkt = numpy.array([self.x, self.y])
        return punkt

    def __str__(self):
        return "\"Punkt: " + str(self.x) + ", " + str(self.y) + ", " + str(self.z) + "\""

    def __add__(self, p2):
        if self.z is None or p2.z is None:
            z = None
        else:
            z = self.z + p2.z
        return Punkt(self.x+p2.x, self.y+p2.y, z)

    def __sub__(self, p2):
        if self.z is None or p2.z is None:
            z = None
        else:
            z = self.z - p2.z
        return Punkt(self.x-p2.x, self.y-p2.y, z)

    def __mul__(self, obj):
        if type(obj).__name__ == "Punkt": # Skalarprodukt
            if self.z is None or obj.z is None:
                z_teil = 0
            else:
                z_teil = self.z * obj.z
            return self.x * obj.x + self.y * obj.y + z_teil
        else:
            if self.z is None or obj.z is None:
                z = None
            else:
                z = self.z * obj
            return Punkt(self.x * obj, self.y * obj, z)

class Uferpunkt(Punkt):

    def __init__(self, x, y, z=None):
        super().__init__(x,y,z)


class Bodenpunkt(Punkt):

    def __init__(self, x, y, z, Sedimentstaerke= None):    # z muss angegeben werde, da Tiefe wichtg; Sedimentstaerke berechnet sich aus Differenz zwischen tiefe mit niedriger und hoher Messfrequenz
        super().__init__(x, y, z)
        self.Sedimentstaerke = Sedimentstaerke

    # Berechnet die Neigung zwischen dem
    # self und bodenpunkt; bei zurueck=True wird das Gefälle vom Bodenpunkt zum self-Punkt betrachtet (bodenpunkt liegt in Fahrtrichtung nach hinten)
    # Profilansicht. Fahrtrichtung nach rechts
    # bei zurueck=True gilt also:  Neigung ist negativ     |  bei zurueck=False gilt also:  Neigung ist negativ
    # bodenpunkt->  .                                      |  self ->  .
    #                \                                     |            \
    #                 \                                    |             \
    #                  .  <- self                          |              .  <- bodenpunkt
    def NeigungBerechnen(self, bodenpunkt, zurueck=True):
        strecke = self.Abstand(bodenpunkt, zwei_dim=True)
        if strecke < 0.1: # liegen die Punkte <10cm auseinander, sollte keine signifikante Steigung vorhanden sein
            return 0
        if zurueck:
            h_diff = self.z - bodenpunkt.z
        else:
            h_diff = bodenpunkt.z - self.z
        return h_diff / strecke

      
class TIN_Punkt(Punkt):

    def __init__(self, x, y, z, TIN_id):
        super().__init__(x,y,z)
        self.TIN_id = TIN_id

class TIN_Kante:

    def __init__(self, Anfangspunkt, Endpunkt, Dreiecke):
        self.Anfangspunkt= Anfangspunkt
        self.Endpunkt = Endpunkt
        self.Dreiecke = Dreiecke
        self.gewicht = 0
        self.Randkante = False

    def __str__(self):
        return "Mittelpunkt " + str(self.mitte())

    def laenge(self):
        return numpy.sqrt((self.Endpunkt.x-self.Anfangspunkt.x)**2+(self.Endpunkt.y-self.Anfangspunkt.y)**2+(self.Endpunkt.z-self.Anfangspunkt.z)**2)

    def mitte(self):
        x = (self.Anfangspunkt.x + self.Endpunkt.x) / 2
        y = (self.Anfangspunkt.y + self.Endpunkt.y) / 2
        z = (self.Anfangspunkt.z + self.Endpunkt.z) / 2

        mitte = Punkt(x,y,z)

        return (mitte)

    def winkel(self): # TODO: Winkelberechnung überprüfen

        n1_list = self.Dreiecke[0].Normalenvector.tolist()
        n2_list = self.Dreiecke[1].Normalenvector.tolist()

        n1 = numpy.array([n1_list[0], n1_list[1], n1_list[2]])
        n2 = numpy.array([n2_list[0], n2_list[1], n2_list[2]])

        if numpy.array_equal(n1,n2):  # Normalenvekroten sind paralel zueinander und arccos kann nicht berechnet werden
            alpha = 0
        else:
            alpha = numpy.arccos((numpy.linalg.norm(numpy.dot(n1,n2)))/(numpy.linalg.norm(n1)*numpy.linalg.norm(n2)))

        return alpha

class TIN_Dreieck:

    def __init__(self, Punkt1, Punkt2, Punkt3, Normalenvector, DreieckId):
        self.Dreieckspunkte = [Punkt1, Punkt2, Punkt3]
        self.Normalenvector = Normalenvector
        self.Nachbardreiecke = []
        self.DreieckId = DreieckId
        self.kanten = 0
        self.offen = True

class TIN:

    def __init__(self, Punktliste, Max_len = 0.0, nurTIN=False):

        self.Punktliste_array = numpy.zeros(shape=(len(Punktliste), 3))
        self.TIN_punkte = []
        self.Kantenliste = []
        self.Dreieckliste = []
        self.max_Kantenlaenge = 0


        # Punkte in Numpy-Array überführen
        for i, punkt in enumerate(Punktliste):

            punkt_in_liste = [punkt.x, punkt.y, punkt.z]
            self.Punktliste_array[i] = punkt_in_liste

        # Triangulation mit dem PyVista-Package
        cloud = pv.PolyData(self.Punktliste_array)

        if Max_len == 0.0:
            self.mesh = cloud.delaunay_2d()
        else:
            self.mesh = cloud.delaunay_2d(alpha=Max_len)

        # Punkt ID's belegen (nur, wenn dies gemacht werden soll, da die berechnung bei vielen Punkten sehr lange dauern kann)

        if not nurTIN:

            for i, koords in enumerate(self.mesh.points.tolist()):

                tin_punkt = TIN_Punkt(koords[0],koords[1],koords[2],i)
                self.TIN_punkte.append(tin_punkt)

            #Dreiecke aus mesh Extrhieren
            for i in range(0,self.mesh.faces.shape[0],4):
                dreieck_mesh = self.mesh.faces[i:i+4]
                dreieckpunkte = dreieck_mesh.tolist()
                dreieckpunkte.pop(0)

                Dreieckpunkte = []

                # Punkte in Punktliste suchen und Dreieckobjekt bilden
                for Punktindex in dreieckpunkte:
                    for punkt in self.TIN_punkte:
                        if punkt.TIN_id == Punktindex:

                            Dreieckpunkte.append(punkt)
                            if len(Dreieckpunkte)== 3: break

                DreieckId = int(i/4)
                normalenvektor = self.mesh.face_normals[DreieckId]

                dreieckobjekt = TIN_Dreieck(Dreieckpunkte[0],Dreieckpunkte[1],Dreieckpunkte[2],normalenvektor, int(DreieckId))

                # Nach Nachbardreiecken suchen

                for dreieckalt in self.Dreieckliste:
                    for punkt1 in dreieckalt.Dreieckspunkte:
                        if punkt1 in Dreieckpunkte:
                            for punkt2 in dreieckalt.Dreieckspunkte:
                                if punkt2 != punkt1 and punkt2 in Dreieckpunkte:

                                    # Abfrage, ob Kante in umgekehrter Form bereits existiert
                                    vorhanden = False
                                    for Kantealt in self.Kantenliste:
                                        if Kantealt.Anfangspunkt == punkt2 and Kantealt.Endpunkt == punkt1:
                                            vorhanden = True

                                    # Kante Bilden und abspeichern
                                    if not vorhanden:
                                        kante = TIN_Kante(punkt1,punkt2,[dreieckobjekt,dreieckalt])
                                        self.Kantenliste.append(kante)

                                        # Maximale Kantenlänge wird zum Normieren bei der Methode "Anzufahrende_Kanten" gebraucht

                                        if kante.laenge() > self.max_Kantenlaenge:
                                            self.max_Kantenlaenge = kante.laenge()
                                        dreieckobjekt.kanten += 1
                                        dreieckalt.kanten += 1
                                        if dreieckobjekt.kanten == 3: dreieckobjekt.offen = False
                                        if dreieckobjekt.kanten == 3: dreieckalt.offen = False

                self.Dreieckliste.append(dreieckobjekt)


    def Anzufahrende_Kanten(self,Anz,bootsposition,entfernungsgewicht):
        # Gibt eine Liste mit den Abzufahrenden kantenobjekten wieder.

        anzufahrende_Kanten = []

        for kante in self.Kantenliste:

            if kante.gewicht == 0:
                #Kantenlängen normieren(mit max Kantenlaenge)   TODO: gewichtung besprechen
                laenge_norm = kante.laenge()/self.max_Kantenlaenge
                kante.gewicht = laenge_norm*kante.winkel()*(1/(kante.mitte().Abstand(bootsposition)**(entfernungsgewicht))) # TODO: Gewichtung anpassen


            for i,kante_i in enumerate(anzufahrende_Kanten):
                if kante.gewicht > kante_i.gewicht:
                    anzufahrende_Kanten.insert(i,kante)
                    if len(anzufahrende_Kanten) > Anz:
                        anzufahrende_Kanten.pop()
                    break

            if len(anzufahrende_Kanten) < Anz and kante not in anzufahrende_Kanten:
                anzufahrende_Kanten.append(kante)



            if anzufahrende_Kanten == []:              # nur für ersten Durchgang benötigt
                anzufahrende_Kanten.append(kante)

        return anzufahrende_Kanten

    def plot(self):
        self.mesh.plot()

    def Vergleich_mit_Original(self,originalmesh):
        tree = KDTree(originalmesh.mesh.points)
        d, idx = tree.query(self.mesh.points)
        self.mesh["distances"] = d

        p = pv.Plotter()
        p.add_mesh(originalmesh.mesh, color=True, opacity=1, smooth_shading=True)
        p.add_mesh(self.mesh, scalars="distances", smooth_shading=True)

        p.show()


class Zelle:

    def __init__(self,cx, cy, w, h):    # Rasterzelle mit mittelpunkt, weite und Höhe definieren, siehe
        self.cx, self.cy = cx, cy
        self.mittelpunkt = Punkt(self.cx, self.cy)
        self.w, self.h = w, h
        self.west_kante, self.ost_kante = cx - w/2, cx + w/2
        self.nord_kante, self.sued_kante = cy - h/2, cy + h/2

        self.beinhaltet_uferpunkte = False
        self.beinhaltet_bodenpunkte = False

    def ebenenausgleichung(self):
        pass

    def enthaelt_punkt(self,Punkt):

        Punktart = type(Punkt).__name__
        punkt_x, punkt_y = Punkt.x, Punkt.y

        # Abfrage ob sich Punkt im Recheck befindet
        enthaelt_punkt = (punkt_x >= self.west_kante and punkt_x <  self.ost_kante and punkt_y >= self.nord_kante and punkt_y < self.sued_kante)


        if Punktart == "Uferpunkt": self.beinhaltet_uferpunkte = True
        if Punktart == "Bodenpunkt": self.beinhaltet_bodenpunkte = True

        return enthaelt_punkt           # Gibt True oder False zurück

    def gebiet_in_zelle(self, suchgebiet):
        return not (suchgebiet.west_kante > self.ost_kante or
                    suchgebiet.ost_kante < self.west_kante or
                    suchgebiet.nord_kante > self.sued_kante or
                    suchgebiet.sued_kante < self.nord_kante)

    def zeichnen(self,plt_suchgebiet):
        x1,y1=self.west_kante, self.nord_kante
        x2,y2=self.ost_kante, self.sued_kante
        plt_suchgebiet.set_xdata([x1, x2, x2, x1, x1])
        plt_suchgebiet.set_ydata([y1, y1, y2, y2, y1])

class Stern:

    # bei initial = True, ist der Startpunkt er Punkt, an dem die Messung losgeht (RTL), bei False ist der Stern ein zusätzlicher und startpunkt demnach die Mitte des neuen Sterns
    # winkelinkrement in gon
    # grzw_seitenlaenge in Meter, ab wann die auf entsprechender Seite ein verdichtender Stern platziert werden soll
    def __init__(self, startpunkt, heading, winkelinkrement=50, grzw_seitenlaenge=500, initial=True, profil_grzw_dichte_topo_pkt=0.1, profil_grzw_neigungen=50, ebene=0):
        self.profile = []
        self.aktuelles_profil = 0 # Index des aktuellen Profils bezogen auf self.aktueller_stern
        self.initial = initial # nur für den ersten Stern True; alle verdichtenden sollten False sein
        self.mittelpunkt = None
        self.stern_beendet = False # sagt nur aus, ob der self-Stern beendet ist, nicht, ob verdichtende Sterne fertuig sind
        self.weitere_sterne = []
        # der aktuelle Stern wird in dieser Variable gesichert, sodass die Methoden statt mit self von dieser Variablen aufgerufen werden (Steuerung von außen geschieht nämlich nur über den einen Init-Stern)
        self.aktueller_stern = self
        self.winkelinkrement = winkelinkrement
        self.grzw_seitenlaenge = grzw_seitenlaenge
        self.startpunkt = startpunkt # nur für initiales Profil
        self.heading = heading # nur für initiales Profil
        self.profil_grzw_dichte_topo_pkt = profil_grzw_dichte_topo_pkt
        self.profil_grzw_neigungen = profil_grzw_neigungen
        self.initialstern = self
        self.ebene = ebene
        self.median = None

    # muss zwingend nach der Initialisierung aufgerufen werden!
    def InitProfil(self):
        profil = Profil(self.heading, self.startpunkt, stuetz_ist_start=True, start_lambda=0, end_lambda=None, grzw_dichte_topo_pkt=self.profil_grzw_dichte_topo_pkt, grzw_neigungen=self.profil_grzw_neigungen)
        self.profile.append(profil)
        return profil.BerechneNeuenKurspunkt(2000, 0, punkt_objekt=True) # Punkt liegt in 2km Entfernung

    # fügt weitere Profile in gegebenen Winkelinkrementen ein, die anschließend befahren werden
    def SternFuellen(self):
        stern = self.aktueller_stern
        mitte = stern.mittelpunkt
        start_winkel = stern.profile[0].heading + stern.winkelinkrement
        winkel = start_winkel
        existierendeProfile = self.Profile()

        #rot_matrix = numpy.array([[numpy.cos(stern.winkelinkrement*numpy.pi/200), numpy.sin(stern.winkelinkrement*numpy.pi/200)], [-numpy.sin(stern.winkelinkrement*numpy.pi/200), numpy.cos(stern.winkelinkrement*numpy.pi/200)]])
        while winkel < start_winkel + 200 - 1.001*stern.winkelinkrement:
            #richtung = numpy.dot(rot_matrix, richtung)
            existiert = False
            for profil in existierendeProfile:
                if profil.ist_definiert != Profil.Definition.NUR_RICHTUNG: # hier werden die in den vorherigen Schleifen eingefügten Profile ignoriert, da sie selbst noch nicht gemessen wurden
                    if profil.PruefProfilExistiert(winkel,mitte, 10, 0.1):
                        existiert = True
            if not existiert:
                profil = Profil(winkel, mitte, stuetz_ist_start=False, start_lambda=0, end_lambda=None, grzw_dichte_topo_pkt=stern.profil_grzw_dichte_topo_pkt, grzw_neigungen=stern.profil_grzw_neigungen)
                stern.profile.append(profil)
            winkel += stern.winkelinkrement

    # durchläuft alle Profile aller Sterne und gibt diese wieder
    # kann von allen Sternen aufgerufen werden
    def Profile(self):
        exisitierndeProfile = []
        def sterne_durchlaufen(stern, exisitierndeProfile):
            for profil in stern.profile:
                exisitierndeProfile.append(profil)
            for gesch_stern in stern.weitere_sterne:
                sterne_durchlaufen(gesch_stern, exisitierndeProfile)
        sterne_durchlaufen(self.initialstern, exisitierndeProfile)
        return exisitierndeProfile

    # durchläuft alle Sterne und gibt diese wieder
    # von allen Sternen aufgerufen werden
    def Sterne(self):
        sterne = []
        def sterne_durchlaufen(stern, sterne):
            sterne.append(stern)
            for gesch_stern in stern.weitere_sterne:
                sterne_durchlaufen(gesch_stern, sterne)
        sterne_durchlaufen(self.initialstern, sterne)
        print(sterne)
        return sterne

    def Medianberechnung(self):
        sterne = self.initialstern.Sterne()
        laengen_ges = []

        def profillaenge_von_mitte(stern, profil, profilindex, liste_laengen):
            gesamtlänge = profil.Profillaenge(akt_laenge=False)
            profil.BerechneLambda(stern.mittelpunkt.ZuNumpyPunkt(zwei_dim=True))
            seitenlänge_vor_mitte = profil.Profillaenge(akt_laenge=True)  # Anfang bis Mitte
            seitenlänge_nach_mitte = gesamtlänge - seitenlänge_vor_mitte  # Mitte bis Ende
            liste_laengen[profilindex] = seitenlänge_vor_mitte
            liste_laengen[profilindex + len(stern.profile)] = seitenlänge_nach_mitte
            return liste_laengen

        for stern in sterne:
            laengen = [0] * (2 * len(stern.profile))
            for i, profil in enumerate(stern.profile):
                laengen_ges.extend(profillaenge_von_mitte(stern, profil, i, laengen))

        return statistics.mean(laengen_ges)

    # findet eine geschlossene Verbindung zusammenhängener Profile zwischen position und soll_endpunkt und gibt es als Liste zurück
    # wird von Initialstern aufgerufen
    def FindeVerbindung(self, position, soll_endpunkt):

        def verbindung_test(stern1, stern2):
            return abs(stern1.ebene - stern2.ebene) == 1

        alle_sterne = self.Sterne()
        weitere_profile = []
        if len(alle_sterne) < 2:
            sterne = alle_sterne
        else: # finde die zusammengehörenden Sterne und verbinde diese mit Profilen
            # finden der Sterne, die am nächsten an die zwei eingegebenen/anzufahrenden Punkte sind (größte Wahrscheinlichkeit, dass diese direkt ohne Ufer anfahrbar sind)
            dist_pos_test = numpy.inf
            start_stern = None
            dist_end_test = numpy.inf
            end_stern = None
            for stern in alle_sterne:
                dist_pos = position.Abstand(stern.mittelpunkt)
                dist_end = soll_endpunkt.Abstand(stern.mittelpunkt)
                if dist_pos < dist_pos_test:
                    dist_pos_test = dist_pos
                    start_stern = stern
                if dist_end < dist_end_test:
                    dist_end_test = dist_end
                    end_stern = stern
            if start_stern != end_stern:
                sterne = [start_stern, end_stern]
            else:
                sterne = [start_stern]
                alle_sterne = sterne

            # Test und Hinzufügen weiterer Sterne, sodass eine verbundene Strecke zwischen den Sternen vorliegt
            for i in range(len(alle_sterne)-2): # i ist die Anzahl zwischen Start- und Endstern einzufügender Sterne
                # Hinzufügen weiterer Sterne
                # Kartesisches Mengenprodukt über alle Sterne
                liste = []
                for _ in range(i):
                    liste.append(alle_sterne)
                for sterne_komb in itertools.product(*liste): # sterne_komb ist zunächst eine beliebige Kombination von i-Sternen aller existierenden Sterne
                    sterne_temp = copy.deepcopy(sterne) # wird kopiert, da getestet wird, ob die Kombination hinzugefügter Sterne auch alle verbunden sind
                    einzig = True
                    for stern in sterne_komb:
                        einzig = einzig and sterne_komb.count(stern) == 1 and not stern in sterne_temp # sagt aus, ob die einzufügenden Sterne jeweils einzeln vorkommen und nicht bereits Start- und Endstern sind
                    if einzig:
                        sterne_temp[1:1] = sterne_komb # ... nur dann sollen diese Sterne zwischen Start- und Endstern eingefügt werden

                        # Test, ob die Sterne untereinander verbunden sind
                        verbunden = False
                        for j in range(len(sterne_temp) - 1):  # hier wird getestet, ob die Sterne verbunden sind
                            verbunden = verbunden or verbindung_test(sterne[j], sterne[j + 1])
                        if verbunden: # wenn alle Sterne verbunden sind, sollen die Schleifen abgebrochen werden
                            sterne = sterne_temp
                            break
                else:
                    continue
                break

            # sobald die Sterne verbunden sind, sollen die zugehörigen verbindenden Profile ermittelt werden
            for i in range(len(sterne)-1):
                stern1 = sterne[i]
                stern2 = sterne[i+1]
                profil = Profil.ProfilAusZweiPunkten(stern1.mittelpunkt, stern2.mittelpunkt)
                #print("Verbindung zwischen den sternen",(stern1.mittelpunkt, stern2.mittelpunkt))
                weitere_profile.append(profil)

        anfang = Profil.ProfilAusZweiPunkten(position, alle_sterne[0].mittelpunkt)
        ende = Profil.ProfilAusZweiPunkten(alle_sterne[len(sterne)-1].mittelpunkt, soll_endpunkt)
        profile = [anfang, *weitere_profile]#[anfang, *weitere_profile, ende]
        print([str(profil) for profil in profile])
        return profile


    # test der Überschreitung des Grenzwerts der Länge eines Profils
    def TestVerdichten(self):

        def berechne_mitte(stern, profil, entfernung_vom_startpunkt):
            neue_mitte = profil.BerechneNeuenKurspunkt(entfernung_vom_startpunkt, punkt_objekt=True)
            # Sternmittelpunkt muss mind. 30 m von allen anderen Mittelpunkten entfernt sein!
            sterne = self.Sterne()
            stern_isoliert = True
            for akt_stern in sterne:
                distanz = neue_mitte.Abstand(akt_stern.mittelpunkt)
                if distanz < 30:
                    stern_isoliert = False
            if stern_isoliert:
                neuer_stern = Stern(profil.stuetzpunkt, profil.heading, stern.winkelinkrement, stern.grzw_seitenlaenge, initial=False, profil_grzw_dichte_topo_pkt=stern.profil_grzw_dichte_topo_pkt, profil_grzw_neigungen=stern.profil_grzw_neigungen, ebene=stern.ebene+1)
                neuer_stern.initialstern = stern.initialstern
                # nicht stern.init, da dieses Profil bereits vom übergeordneten Stern gemessen wurde; stattdessen soll dieses Profil als bereits gemessen übernommen werden
                neuer_stern.profile.append(profil)
                neuer_stern.mittelpunkt = neue_mitte
                neuer_stern.aktuelles_profil = 1
                neuer_stern.SternFuellen()
                return neuer_stern
            else:
                return

        def profillaenge_von_mitte(stern, profil, profilindex, liste_laengen):
            gesamtlänge = profil.Profillaenge(akt_laenge=False)
            profil.BerechneLambda(stern.mittelpunkt.ZuNumpyPunkt(zwei_dim=True))
            seitenlänge_vor_mitte = profil.Profillaenge(akt_laenge=True)  # Anfang bis Mitte
            seitenlänge_nach_mitte = gesamtlänge - seitenlänge_vor_mitte  # Mitte bis Ende
            liste_laengen[profilindex] = seitenlänge_vor_mitte
            liste_laengen[profilindex + len(stern.profile)] = seitenlänge_nach_mitte
            return liste_laengen

        stern = self.aktueller_stern
        if len(stern.weitere_sterne) == 0:
            neue_messung = False
            laengen = [0] * (2 *len(stern.profile))
            for i, profil in enumerate(stern.profile):
                laengen = profillaenge_von_mitte(stern, profil, i, laengen)
            stern.median = statistics.median(laengen)
            for i, laenge in enumerate(laengen):
                if laenge >= self.grzw_seitenlaenge or laenge >= 2*stern.median:
                    neue_messung = True
                    if i >= len(stern.profile): # dann liegt das neue Sternzentrum zwischen Mitte und Endpunkt
                        entfernung = laengen[i%len(stern.profile)] + laenge/2
                    else: # so liegt das neue Zentrum zwischen STart und Mitte
                        entfernung = laenge/2
                    neuer_stern = berechne_mitte(stern, stern.profile[i%len(stern.profile)], entfernung)
                    if neuer_stern is not None:
                        stern.weitere_sterne.append(neuer_stern)
            return neue_messung

    # sucht den aktuellen Stern (möglicherweise rekursiv, falls mehrere Sterne vorhanden sind)
    # diese Funktion sollte mindestens immer aufgerufen werden, wenn ein Stern abgeschlossen wurde!
    def AktuellerStern(self):
        if self.initial and not self.stern_beendet:
            self.aktueller_stern = self
            return True
        sterne = []
        def rek(self):
            for stern in self.weitere_sterne:
                if not stern.stern_beendet:
                    sterne.append(stern)
                rek(stern)
        rek(self)
        if len(sterne) > 0:
            self.aktueller_stern = sterne[0]
        else:
            self.aktueller_stern = None # alle Sterne sind gemessen

        #print("Aktueller Stern:", self.aktueller_stern)
        return self.aktueller_stern is not None # falls es keine Sterne mehr gibt, wird False ausgegeben

    # durchläuft alle Profile des aktuellen Sterns und gibt das aktuelle Profil aus (None, falls keins gefunden wurde)
    def AktuellesProfil(self):
        stern = self.aktueller_stern
        for i, profil in enumerate(stern.profile):
            if not profil.gemessenes_profil:
                self.aktuelles_profil = i
                return profil
        self.aktuelles_profil = -1
        return

    # beendet aktuelles Profil und sucht die bedeutsamen Punkte heraus und ordnet sie in der entsprechenden Liste des Profils hinzu
    def ProfilBeenden(self, punkt):
        stern = self.aktueller_stern
        profil = self.AktuellesProfil()
        profil.ProfilAbschliessenUndTopoPunkteFinden(punkt)
        if stern.aktuelles_profil == 0:
            stern.mittelpunkt = profil.BerechneNeuenKurspunkt(profil.Profillaenge(False)/2, punkt_objekt=True)
            self.SternFuellen()
        if stern.aktuelles_profil == len(stern.profile)-1:
            stern.stern_beendet = True
            # versuch weitere, verdichtende Sterne zu finden
            if self.TestVerdichten(): # bewirkt nur eine Verdichtung, wenn noch keine weiteren Sterne in stern vorliegen
                # Erst Zentrum vom fertigen Stern anfahren (geschieht nur, wenn das profil beendet ist)
                self.AktuellerStern()  # neuer Stern wird belegt
                return stern.mittelpunkt # alten Sternmittelpunkt anfahren! (nicht MittelpunktAnfahren, da jetzt der neue Stern angefahren würde (Zeile drüber))
                #return self.aktueller_stern.MittelpunktAnfahren()

            else:
                self.AktuellerStern()

            if self.aktueller_stern == None:
                return None
        stern.aktuelles_profil += 1
        return stern.MittelpunktAnfahren()

    # diese Methode immer aufrufen, sobald das Ufer angefahren wird ODER ein Punkt erreicht wird, der angefahren werden sollte
    # punkt: Endpunkt, an dem das Boot auf das Ufer trifft; mode: TrackingMode des Bootes
    # Rückgabe: Liste mit Punkt, der angefahren werden sollte und welche Tracking-Methode das Boot haben sollte
    # return punkt = None, wenn der Stern/ die Sterne fertig gemessen wurden
    def NaechsteAktion(self, punkt, mode):
        stern = self.aktueller_stern
        if mode == TrackingMode.PROFIL: # das Boot soll Messungen auf dem Profil vornehmen
            punkt = self.ProfilBeenden(punkt)
            mode = TrackingMode.BLINDFAHRT
        elif mode == TrackingMode.BLINDFAHRT: # das Boot soll keine Messungen vornehmen und zurück zur Sternmitte fahren
            # wenn das Boot an der Mitte ankommt und der Stern zwischenzeitlich nicht aktualisiert wurde (also gleich geblieben ist)
            if Zelle(stern.mittelpunkt.x, stern.mittelpunkt.y, 5, 5).enthaelt_punkt(punkt):
                punkt = stern.profile[stern.aktuelles_profil].BerechneNeuenKurspunkt(-2000, punkt_objekt=True)
                mode = TrackingMode.UFERERKENNUNG
                #print(self.aktueller_stern.mittelpunkt, "Profilerkundung starten")
                #return [punkt, mode]
            else:
                # wenn das Boot in der Mitte ankommt, aber einen anderen Stern anfangen soll, soll es zunächst zu dessen Mitte fahren
                punkt = stern.mittelpunkt
                mode = TrackingMode.BLINDFAHRT
                #return [stern.mittelpunkt, TrackingMode.BLINDFAHRT]
        elif mode == TrackingMode.UFERERKENNUNG:
            profil = stern.profile[stern.aktuelles_profil]
            profil.ProfilBeginnen(punkt)
            punkt = profil.BerechneNeuenKurspunkt(2000, punkt_objekt=True)
            mode = TrackingMode.PROFIL
            #print(self.aktueller_stern.mittelpunkt,"Profilmessung Starten")
        return [punkt, mode]

    def MittelpunktAnfahren(self):
        stern = self.aktueller_stern
        if stern.mittelpunkt:
            return stern.mittelpunkt

    # pflegt bereits Median-gefilterte Punkte in die entsprechende Liste des aktuellen Profils ein; punkt kann auch eine einziger Punkt sein
    def MedianPunkteEinlesen(self, punkte):
        stern = self.aktueller_stern
        stern.profile[stern.aktuelles_profil].MedianPunkteEinfuegen(punkte)
        #if type(punkte).__name__ != "list":
        #    punkte = [punkte]
        #for punkt in punkte:
        #    stern.profile[stern.aktuelles_profil].MedianPunktEinfuegen(punkt)

    # aus den einzelnen Profilen für das TIN
    def TopographischBedeutsamePunkteAbfragen(self):
        # auch wieder rekursiv aus allen Sternen und den Profilen darin
        topographisch_bedeutsame_punkte = []
        def sterne_durchlaufen(self, topographisch_bedeutsame_punkte):
            for profil in self.profile:
                topographisch_bedeutsame_punkte.extend(profil.topographisch_bedeutsame_punkte)
            for stern in self.weitere_sterne:
                sterne_durchlaufen(stern, topographisch_bedeutsame_punkte)
        sterne_durchlaufen(self, topographisch_bedeutsame_punkte)
        return topographisch_bedeutsame_punkte

class Profil:

    # gibt an, wie das Profil zurzeit definiert ist
    class Definition(enum.Enum):
        NUR_RICHTUNG = 0
        RICHTUNG_UND_START = 1
        START_UND_ENDPUNKT = 2

    # Richtung: Kursrichtung in Gon (im Uhrzeigersinn); stuetzpunkt: Anfangspunkt bei start_lambda=0; start_lambda:
    # startpunkt als Punkt-Objekt
    # end_lmbda ist bei den verdichtenden Profilen gegeben
    # grzw_dichte_topo_pkt: Soll-Punktdichte je Meter Profil; grzw_neigungen: grenzwert in gon, ab wann aufeinander folgende Gefälle einen topographisch bedeutsamenm Punkt verursachen
    def __init__(self, richtung, stuetzpunkt, stuetz_ist_start=True, start_lambda=0, end_lambda=None, grzw_dichte_topo_pkt=0.1, grzw_neigungen=50):
        self.heading = richtung
        self.richtung = numpy.array([numpy.sin(richtung*numpy.pi/200), numpy.cos(richtung*numpy.pi/200)]) # 2D Richtungsvektor in Soll-Fahrtrichtung
        self.stuetzpunkt = stuetzpunkt.ZuNumpyPunkt(zwei_dim=True) # Anfangspunkt, von dem die Profilmessung startet, wenn start_lambda=0
        self.startpunkt = None
        self.endpunkt = None
        self.lamb = start_lambda # aktuelles Lambda der Profilgeraden (da self.richtung normiert, ist es gleichzeitig die Entfernung vom Stuetzpunkt)
        self.start_lambda = start_lambda
        self.end_lambda = end_lambda
        self.gemessenes_profil = False # bei True ist dieses Profil fertig gemessen und ausgewertet worden
        self.median_punkte = [] # Median gefilterte Bodenpunkte
        self.topographisch_bedeutsame_punkte = []
        self.grzw_dichte_topo_pkt = grzw_dichte_topo_pkt # Mindestanzahl der topographisch interessanten Punkte pro Meter!
        self.grzw_neigungen = grzw_neigungen # Winkel in gon, die die nachfolgend zu betrachtende Seite von der aktuellen abweichen darf, um noch als Gerade betrachtet zu werden

        # Bestimmung der Profildefinition
        if stuetz_ist_start:
            self.startpunkt = stuetzpunkt
            if self.end_lambda is None:
                self.ist_definiert = Profil.Definition.RICHTUNG_UND_START
            else:
                self.ist_definiert = Profil.Definition.START_UND_ENDPUNKT
                self.endpunkt = self.BerechneNeuenKurspunkt(self.Profillaenge(akt_laenge=False), punkt_objekt=True)
        else:
            self.ist_definiert = Profil.Definition.NUR_RICHTUNG

    def __str__(self):
        if self.ist_definiert == Profil.Definition.START_UND_ENDPUNKT:
            return "Richtung: " + str(self.heading) + ", Start- und Endpunkt: " + str(self.startpunkt) + "; " + str(self.endpunkt)
        else:
            return "Richtung: " + str(self.heading) + ", Stützpunkt: " + str(self.stuetzpunkt)

    @classmethod
    def VerdichtendesProfil(cls, dreieckskante, grzw_dichte_topo_pkt=0.1, grzw_neigungen=50):
        p1 = dreieckskante.Anfangspunkt
        p2 = dreieckskante.Endpunkt
        temp_profil = cls.ProfilAusZweiPunkten(p1, p2)
        abstand = temp_profil.Profillaenge(akt_laenge=False)/2
        start = temp_profil.BerechneNeuenKurspunkt(abstand, quer_entfernung=-abstand, punkt_objekt=True)
        end = temp_profil.BerechneNeuenKurspunkt(abstand, quer_entfernung=abstand, punkt_objekt=True)
        profil = cls.ProfilAusZweiPunkten(start, end, grzw_dichte_topo_pkt, grzw_neigungen)
        print("Anfangspunt bei Profilberechnung:", start,"Endpunt bei Profilberechnung:", end)
        return profil

    # definiert ein Profil aus 2 Puntken
    @classmethod
    def ProfilAusZweiPunkten(cls, p1, p2, grzw_dichte_topo_pkt=0.1, grzw_neigungen=50):
        heading = Headingberechnung(None, p2, p1)
        abstand = p1.Abstand(p2)
        profil = cls(heading, p1, stuetz_ist_start=True, start_lambda=0, end_lambda=abstand, grzw_dichte_topo_pkt=grzw_dichte_topo_pkt, grzw_neigungen=grzw_neigungen)
        return profil

    # wenn das Boot im Stern von der Mitte am Ufer ankommt und mit der Messung entlang des Profils beginnen soll (punkt ist der gefundene Punkt am Ufer)
    def ProfilBeginnen(self, punkt):
        if self.ist_definiert == Profil.Definition.NUR_RICHTUNG:
            # Projektion des neuen Stuetzvektors (punkt) auf die vorhandene Gerade
            richtung = numpy.array([self.richtung[1], -self.richtung[0]])
            punkt = punkt.ZuNumpyPunkt(zwei_dim=True)
            self.stuetzpunkt = punkt - richtung * (numpy.dot((punkt - self.stuetzpunkt), richtung))
            self.ist_definiert = Profil.Definition.RICHTUNG_UND_START
            if self.startpunkt is None:
                self.startpunkt = Punkt(self.stuetzpunkt[0], self.stuetzpunkt[1])
            self.start_lambda = 0

    # sofern Start und Endpunkt gegeben sind, werden die beiden Punkte ausgetauscht
    def Flip(self):
        if self.ist_definiert == Profil.Definition.START_UND_ENDPUNKT:
            temp = self.startpunkt
            self.stuetzpunkt = self.endpunkt.ZuNumpyPunkt(zwei_dim=True)
            self.startpunkt = self.endpunkt
            self.endpunkt = temp
            self.richtung = -1 * self.richtung
            self.heading = (self.heading+200) % 400

    def MedianPunkteEinfuegen(self, punkte):
        if self.ist_definiert.value > 0:
            if type(punkte).__name__ == "list":
                for punkt in punkte:
                    self.median_punkte.append(punkt)
            else:
                self.median_punkte.append(punkte)
        else:
            raise Exception("Das Profil wurde noch nicht initialisiert (Startpunkt fehlt; Methode ProfilBeginnen muss aufgerufen werden).") # (Boot müsste auf dem Weg zum Startpunkt des Profils sein)

    # Berechnet die Entfernung des angeg. Punkts entlang des Profils bis zum Stuetzpunkt (der ab Profil.Definition > 0 auch der Startpunkt ist)
    def BerechneLambda(self, punkt):
        self.lamb = numpy.dot((punkt - self.stuetzpunkt), self.richtung)
        return self.lamb

    # Berechnet einen neuen Kurspunkt von Start-Lambda (länge der Fahrtrichtung) und quer dazu (in Fahrtrichtung rechts ist positiv)
    def BerechneNeuenKurspunkt(self, laengs_entfernung, quer_entfernung=0, punkt_objekt=False):
        quer_richtung = numpy.array([self.richtung[1], -self.richtung[0]])
        punkt = self.stuetzpunkt + (self.start_lambda + laengs_entfernung) * self.richtung + quer_entfernung * quer_richtung
        if punkt_objekt:
            punkt = Punkt(punkt[0], punkt[1])
        return punkt

    # Berechnet Punkte mit gleichmäßigem Abstand
    def BerechneZwischenpunkte(self, abstand=5):
        if self.ist_definiert == Profil.Definition.START_UND_ENDPUNKT:
            punktliste = []
            lamb = self.start_lambda
            while lamb < self.end_lambda:
                punkt = self.BerechneNeuenKurspunkt(lamb, punkt_objekt=True)
                punktliste.append(punkt)
                lamb += abstand
            else:
                punkt = self.BerechneNeuenKurspunkt(self.end_lambda, punkt_objekt=True)
                punktliste.append(punkt)
            return punktliste

    # fügt einen neuen Endpunkt ein
    # Achtung! Projiziert position auf die Richtung der aktuellen Definition des Profils
    def NeuerEndpunkt(self, position):
        if position is None:
            raise Exception("Es muss ein Endpunkt des Profils angegeben werden.")
        self.end_lambda = self.BerechneLambda(position.ZuNumpyPunkt(zwei_dim=True))
        self.endpunkt = self.BerechneNeuenKurspunkt(self.end_lambda, punkt_objekt=True)
        self.ist_definiert = Profil.Definition.START_UND_ENDPUNKT

    # aktuell gefahrenen Profillänge, falls Profil abgeschlossen ist, ist es die Gesamtlänge
    def Profillaenge(self, akt_laenge=True):
        if akt_laenge:
            return self.lamb - self.start_lambda
        else: # Länge, wenn end_lambda bekannt
            return self.end_lambda - self.start_lambda

    # Punkt muss mind. Toleranz Meter auf dem Profil liegen für return True
    def PruefPunktAufProfil(self, punkt, toleranz=2):
        if type(punkt).__name__ != "ndarray":
            punkt = punkt.ZuNumpyPunkt()
        abstand = abstand_punkt_gerade(self.richtung, self.stuetzpunkt, punkt)
        return abs(abstand) < toleranz

    # prüft, ob ein geg Punkt innerhalb des Profils liegt (geht nur, wenn self.gemessenes_profil = True ODER wenn self.end_lambda != None
    def PruefPunktInProfil(self, punkt, profilpuffer=20):
        if self.ist_definiert == Profil.Definition.START_UND_ENDPUNKT:
            if type(punkt).__name__ != "ndarray":
                punkt = punkt.ZuNumpyPunkt()
            if self.PruefPunktAufProfil(punkt, profilpuffer):
                lamb = numpy.dot(self.richtung, (punkt - self.stuetzpunkt))
                return self.start_lambda-profilpuffer <= lamb <= self.end_lambda+profilpuffer
            else:
                return False

    # Überprüft, ob das Profil, das aus den Argumenten initialisiert werden KÖNNTE, ähnlich zu dem self Profil ist (unter Angabe der Toleranz)
    # Toleranz ist das Verhältnis der Überdeckung beider Profilbreiten zu dem self-Profil; bei 0.3 dürfen max 30% des self-Profilstreifens mit dem neuen Profil überlagert sein
    # Profilbreite: Breite zu einer Seite (also Gesamtbreite ist profilbreite*2)
    # bei return True sollte das Profil also nicht gemessen werden
    # lambda_intervall: bei None, soll das neue Profil unendlich lang sein, bei Angabe eben zwischen den beiden Lambdas liegen (als Liste, zB [-20,20] bei lamb 0 ist der Geradenpunkt gleich dem Stützpunkt)
    def PruefProfilExistiert(self, richtung, stuetzpunkt, profilbreite=5, toleranz=0.3, lambda_intervall=None):
        if type(stuetzpunkt).__name__ == "Punkt":
            stuetzpunkt = stuetzpunkt.ZuNumpyPunkt(zwei_dim=True)
        if self.ist_definiert == Profil.Definition.START_UND_ENDPUNKT:
            quer_lambda_intervall = [0, 2*profilbreite]
            test_profil_unendlich = not lambda_intervall # bestimmt, ob das neu zu rechnende Profil unendlich lang ist oder von Vornherein beschränkt ist
            self.lamb = 0
            if test_profil_unendlich:
                fläche = (self.end_lambda-self.start_lambda) * 2 * profilbreite # ist zwar nicht so gut, aber sagt zumindest aus, dass vom self Profil fast alles getroffen wird
            else:
                fläche = (lambda_intervall[1] - lambda_intervall[0]) * 2 * profilbreite
            x = []
            y = []

            ### Clipping der neuen Profilfläche auf die alte ###
            # Berechnung der Eckpunkte des self-Profils
            eckpunkte = []
            lamb_temp = self.start_lambda
            for i in range(4):
                faktor = -1
                if i % 3 == 0:
                    faktor = 1
                punkt = self.BerechneNeuenKurspunkt(lamb_temp, faktor * profilbreite)
                eckpunkte.append(punkt)
                if i == 1:
                    lamb_temp = self.end_lambda

            # Berechnung der Eckpunkte und Richtungsvektoren des neu zu prüfenden Profils
            pruef_richtung = numpy.array([numpy.sin(richtung * numpy.pi / 200), numpy.cos(richtung * numpy.pi / 200)])
            pruef_richtung_fix = pruef_richtung
            pruef_stuetz = [] # Stützpunkte der beiden parallelen zunächst unendlich langen Geraden der Begrenzung des neu zu prüfenden Profils ODER die Eckpunkte des neuen Profils
            richtung = numpy.array([numpy.sin(richtung * numpy.pi / 200), numpy.cos(richtung * numpy.pi / 200)])
            if test_profil_unendlich: # hier nur 2 "Eckpunkte" einführen
                temp_pruef_quer_richtung = numpy.array([richtung[1], -richtung[0]])
                pruef_stuetz.append(stuetzpunkt - profilbreite * temp_pruef_quer_richtung)
                pruef_stuetz.append(stuetzpunkt + profilbreite * temp_pruef_quer_richtung)
            else: # hier werden alle Eckpunkte eingeführt
                for i in range(4):
                    if i % 3 == 0:
                        pruef_lambda = lambda_intervall[0]
                    else:
                        pruef_lambda = lambda_intervall[1]
                    faktor = 1
                    if i <= 1:
                        faktor = -1
                    quer_richtung = numpy.array([pruef_richtung[1], -pruef_richtung[0]])
                    punkt = stuetzpunkt + (pruef_lambda) * pruef_richtung + (profilbreite * quer_richtung * faktor)
                    pruef_stuetz.append(punkt)

            # Prüft, ob der angeg Eckpunkt des self Profils in dem neuen Profil enthalten ist
            def pruef_eckpunkt_in_neuem_profil(eckpunkt, test_profil_unendlich, pruef_richtung, pruef_stuetz):
                if test_profil_unendlich:
                    abst_g1 = abstand_punkt_gerade(pruef_richtung, pruef_stuetz[0], eckpunkt)
                    abst_g2 = abstand_punkt_gerade(pruef_richtung, pruef_stuetz[1], eckpunkt)
                    drinnen = (abst_g1 < 0 and abst_g2 > 0) or (abst_g1 > 0 and abst_g2 < 0)
                    return drinnen
                else:
                    pruef_temp = pruef_richtung
                    abst_g1 = abstand_punkt_gerade(pruef_temp, pruef_stuetz[0], eckpunkt)
                    abst_g3 = abstand_punkt_gerade(pruef_temp, pruef_stuetz[2], eckpunkt)
                    pruef_temp = numpy.array([pruef_temp[1], -pruef_temp[0]])
                    abst_g2 = abstand_punkt_gerade(pruef_temp, pruef_stuetz[1], eckpunkt)
                    abst_g4 = abstand_punkt_gerade(pruef_temp, pruef_stuetz[3], eckpunkt)
                    drinnen_1 = (abst_g1 < 0 and abst_g3 > 0) or (abst_g1 > 0 and abst_g3 < 0)
                    drinnen_2 = (abst_g2 < 0 and abst_g4 > 0) or (abst_g2 > 0 and abst_g4 < 0)
                    return drinnen_1 and drinnen_2

            # Schleife über alle Eckpunkte des self Profils
            test_richtung = numpy.array([-self.richtung[1], self.richtung[0]])  # Richtung der aktuell betrachteten Kante des self Profils
            for i, eckpunkt in enumerate(eckpunkte):
                if test_profil_unendlich:
                    n = 2 # Anzahl der durchzulaufenden Punkte des neuen Profils
                else:
                    n = 4
                # Schleife über alle Stützpunkte des neuen Profils
                for j in range(n):
                    pruef_eckpunkt = pruef_stuetz[j]
                    # Lambda-Intervalle anpassen (je nach Kante)
                    if i % 2 == 0:
                        test_intervall = quer_lambda_intervall
                    else:
                        test_intervall = [self.start_lambda, self.end_lambda]
                    if test_profil_unendlich:
                        pruef_intervall = lambda_intervall
                    else:
                        if j % 2 == 0:
                            pruef_intervall = lambda_intervall
                        else:
                            pruef_intervall = quer_lambda_intervall
                    schnittpunkt = schneide_geraden(test_richtung, eckpunkt, pruef_richtung, pruef_eckpunkt, test_intervall, pruef_intervall)
                    if schnittpunkt is not None:
                        if not test_profil_unendlich and self.PruefPunktInProfil(pruef_eckpunkt, profilbreite):
                            x.append(pruef_eckpunkt[0])
                            y.append(pruef_eckpunkt[1])
                        x.append(schnittpunkt[0])
                        y.append(schnittpunkt[1])
                    naechster_eckpunkt = eckpunkte[(i + 1) % 4]
                    if pruef_eckpunkt_in_neuem_profil(naechster_eckpunkt, test_profil_unendlich, pruef_richtung_fix, pruef_stuetz):
                        x.append(naechster_eckpunkt[0])
                        y.append(naechster_eckpunkt[1])
                    if not test_profil_unendlich:
                        pruef_richtung = numpy.array([pruef_richtung[1], -pruef_richtung[0]])
                test_richtung = numpy.array([test_richtung[1], -test_richtung[0]])

            if len(x) >= 3:
                überdeckung = Flächenberechnung(numpy.array(x), numpy.array(y))
                return (überdeckung / fläche) > toleranz
            else:
                return False
        else:
            raise Exception("Das Profil wurde noch nicht vollständig definiert.")

    # end_punkt: Punkt, an dem das Boot sagt, hier ist Ufer oder der zuvor definierte Endpunkt ist erreicht;
    def ProfilAbschliessenUndTopoPunkteFinden(self, end_punkt=None):
        if not self.gemessenes_profil:
            self.gemessenes_profil = True
            if self.ist_definiert != Profil.Definition.START_UND_ENDPUNKT:
                self.NeuerEndpunkt(end_punkt)

            # ab hier berechnen der topographisch bedeutsamen Punkte (der allererste und -letzte Medianpunkt werden nach jetztigem Schema nie eingefügt)
            mind_anzahl_topo_punkte = int(round(self.grzw_dichte_topo_pkt * self.Profillaenge(), 0))
            grzw_winkel_rad = self.grzw_neigungen/200*numpy.pi
            if len(self.median_punkte) > mind_anzahl_topo_punkte:
                #print(len(self.median_punkte))
                index_zugefügter_medianpunkte = []  # hier stehen die Indizes der Medianpunkte (bezogen auf self.median_punkte) drin, die als topographisch bedeutsam gefunden wurden
                steigung_zurück = numpy.arctan(self.median_punkte[1].NeigungBerechnen(self.median_punkte[0]))
                for i in range(1, len(self.median_punkte) - 1):
                    p1 = self.median_punkte[i]
                    p2 = self.median_punkte[i+1]
                    steigung_vor = numpy.arctan(p1.NeigungBerechnen(p2, zurueck=False))
                    winkel = steigung_vor - steigung_zurück
                    if abs(winkel) >= grzw_winkel_rad:
                        index_zugefügter_medianpunkte.append(i)
                    steigung_zurück = steigung_vor
                #print(index_zugefügter_medianpunkte)
                # weitere Punkte einfügen, falls nicht genügend Median Punkte gefunden wurden
                while len(index_zugefügter_medianpunkte) < mind_anzahl_topo_punkte:
                    größter_abstand = -1
                    index = None
                    # durchlaufen aller "Geraden", die durch zwei der bereits gefundenen topographisch bedeutsamen Punkte gebildet werden
                    test_indizes = [0, *index_zugefügter_medianpunkte, len(self.median_punkte)-1] # damit die "Geraden", die vom Start und zum Endpunkt gehen mit berücksichtigt werden
                    for i in range(len(test_indizes)-1):
                        #print(test_indizes,i)
                        median_index_start = test_indizes[i] # index, die auch in index_zugefügter_medianpunkte drin stehen
                        median_index_ende = test_indizes[i+1]
                        stuetz = self.median_punkte[median_index_start].ZuNumpyPunkt(zwei_dim=True)
                        richtung = self.median_punkte[median_index_ende].ZuNumpyPunkt(zwei_dim=True) - stuetz
                        richtung = richtung / numpy.linalg.norm(richtung)
                        print("BerechneRichtung zur Runtimewarning")
                        # durchlaufen aller Punkte zwischen den beiden "Geraden"-definierenden Punkten
                        for median_index in range(median_index_start+1, median_index_ende):
                            abstand = abs(abstand_punkt_gerade(richtung, stuetz, self.median_punkte[median_index].ZuNumpyPunkt(zwei_dim=True)))

                            if größter_abstand <= abstand:
                                größter_abstand = abstand
                                index = median_index
                    if index != None:
                        index_zugefügter_medianpunkte.append(index)
                        break
                    index_zugefügter_medianpunkte.sort()

                # hinzufügen aller so gefundenen Punkte als topographisch bedeutsame Punkte
                for index in index_zugefügter_medianpunkte:
                    self.topographisch_bedeutsame_punkte.append(self.median_punkte[index])
            else:
                self.topographisch_bedeutsame_punkte = self.median_punkte

# richtung und stuetz sind jeweils die 2D Vektoren der Geraden, und punkt der zu testende Punkt
# richtung muss normiert sein!!
def abstand_punkt_gerade(richtung, stuetz, punkt):
    if richtung.shape[0] == 2: # falls die Vektoren 2D sind
        richtung = numpy.array([richtung[1], -richtung[0]])
    else: # falls die Vektoren 3D sind
        richtung = punkt - numpy.dot(punkt, richtung) * richtung
        richtung = richtung / numpy.linalg.norm(richtung)
    return numpy.dot(richtung, (punkt - stuetz))

# Gerade 1 sollte bei Verwendung innerhalb der Klasse Profil die Kante des self Profils sein
def schneide_geraden(richtung1, stuetz1, richtung2, stuetz2, lamb_intervall_1=None, lamb_intervall_2=None):
    det = -1 * (richtung1[0]*richtung2[1]-richtung2[0]*richtung1[1])
    if abs(det) < 0.0000001: # falls kein oder sehr schleifender Schnitt existiert
        return None
    inverse = numpy.matrix([[-richtung2[1], richtung2[0]], [-richtung1[1], richtung1[0]]]) / det
    diff_stuetz = stuetz2 - stuetz1
    lambdas = numpy.array(inverse.dot(diff_stuetz))[0]
    if lamb_intervall_1 is not None and lamb_intervall_2 is not None:
        if not ((lamb_intervall_1[0] <= lambdas[0] <= lamb_intervall_1[1]) and (lamb_intervall_2[0] <= lambdas[1] <= lamb_intervall_2[1])):
            return None
    elif lamb_intervall_1 is not None:
        if not (lamb_intervall_1[0] <= lambdas[0] <= lamb_intervall_1[1]):
            return None
    punkt = stuetz1 + lambdas[0] * richtung1
    return punkt

def Headingberechnung(boot=None, richtungspunkt=None, position=None):
    if boot is not None:
        with schloss:
            if not boot.AktuelleSensordaten[0]:
                print("self.heading ist None")
                return None

            gnss1 = boot.AktuelleSensordaten[0]
            gnss2 = boot.AktuelleSensordaten[1]
            x_richtung = gnss2.daten[0]
            y_richtung = gnss2.daten[1]
            x_position = gnss1.daten[0]
            y_position = gnss1.daten[1]
    else:
        x_position = position.x
        y_position = position.y

    if richtungspunkt is not None:
        x_richtung = richtungspunkt.x
        y_richtung = richtungspunkt.y

    # Heading wird geodätisch (vom Norden aus im Uhrzeigersinn) berechnet und in GON angegeben
    heading_rad = numpy.arctan((x_richtung - x_position) / (y_richtung - y_position))

    # Quadrantenabfrage

    if x_richtung > x_position:
        if y_richtung > y_position:
            q_zuschl = 0  # Quadrant 1
        else:
            q_zuschl = numpy.pi  # Quadrant 2
    else:
        if y_richtung > y_position:
            q_zuschl = 2 * numpy.pi  # Quadrant 4
        else:
            q_zuschl = numpy.pi  # Quadrant 3

    heading_rad += q_zuschl
    heading_gon = heading_rad * (200 / numpy.pi)

    return heading_gon

class Uferpunktquadtree:

    def __init__(self, zelle, max_punkte_pro_zelle = 2, ebene = 0, max_ebenen=8):
        self.zelle = zelle                                # Rechteck, was das den Umfang des Quadtreeelements definiert
        self.max_punkte_pro_zelle = max_punkte_pro_zelle    # Maximale Anzahl der Punkte pro Zelle
        self.ebene = ebene                                  # Ferfeinerungsgrad des Quadtrees
        self.uferpunkte =[]
        self.max_ebenen= max_ebenen
        self.geteilt = False                                # Schalter der anzeigt, ob die Zelle geteilt wurde

    def teilen(self):                                       # Eine Zelle wird beim Überschreiten der Maximalpunktzahl in vier kleiner Zellen unterteilt

        cx, cy = self.zelle.cx, self.zelle.cy
        w_neu, h_neu = self.zelle.w / 2, self.zelle.h / 2

        # Neue Zellen erstellen
        self.nw = Uferpunktquadtree(Zelle(cx - w_neu/2, cy - h_neu/2, w_neu, h_neu),self.max_punkte_pro_zelle, self.ebene + 1)
        self.no = Uferpunktquadtree(Zelle(cx + w_neu/2, cy - h_neu/2, w_neu, h_neu),self.max_punkte_pro_zelle, self.ebene + 1)
        self.so = Uferpunktquadtree(Zelle(cx + w_neu/2, cy + h_neu/2, w_neu, h_neu),self.max_punkte_pro_zelle, self.ebene + 1)
        self.sw = Uferpunktquadtree(Zelle(cx - w_neu/2, cy + h_neu/2, w_neu, h_neu),self.max_punkte_pro_zelle, self.ebene + 1)
        self.kinderquadtrees = [self.nw, self.no, self.so, self.sw]

        # Punkte von alter Zelle auf die neuen Zellen verteilen
        for punkt in self.uferpunkte:
            for kindquadtree in self.kinderquadtrees:
                if kindquadtree.zelle.enthaelt_punkt(punkt):
                    kindquadtree.uferpunkte.append(punkt)

        self.uferpunkte = []
        self.geteilt = True

    def punkt_einfuegen(self, punkt):

        # Prüfen ob Punkt im Quadtree liegt
        if not self.zelle.enthaelt_punkt(punkt):
            #Punkt liegt nicht im Quadtree, Methode wird abgebrochen
            return False

        # Prüfen ob noch platz in dem Quadtree für den Punkt ist und ob die Zelle schon geteilt wurde und ob die letzte ebene erreicht wurde
        if len(self.uferpunkte) < self.max_punkte_pro_zelle:
            if not self.geteilt:
                self.uferpunkte.append(punkt)
                return True

        if self.ebene == self.max_ebenen:       # In der letzten ebene werden alle Punkte abgespeichert und nicht weiter geteilt
            self.uferpunkte.append(punkt)
            return True

        # Wenn die Methode nicht durch die beiden oberen Returns abgebrochen wurde, muss der Quadtree geteilt werden und der Punkt in einem der unterquadtrees untergebracht werden

        if not self.geteilt and self.ebene < self.max_ebenen:
            self.teilen()

        for kindquadtree in self.kinderquadtrees:
            einfuegen = kindquadtree.punkt_einfuegen(punkt)
            if einfuegen:
                return True

    def ebene_von_punkt(self, punkt):           # Gibt an, auf welcher Ebene ein Quadtree an einem bestimmten Punkt ist

        quadtree = self
        for i in range(0,self.max_ebenen+1):
            if quadtree.geteilt:
                for kindquadtree in quadtree.kinderquadtrees:
                    wert  = kindquadtree.zelle.enthaelt_punkt(punkt)
                    if wert:
                        quadtree = kindquadtree
            else:
                return quadtree.ebene


    def linienabfrage(self, profil):

        max_ebene = self.max_ebenen - 1
        Pruefpunkte = profil.BerechneZwischenpunkte() #TODO: Anpassung der Auflösung nach kleinster Zelle

        for punkt in Pruefpunkte:
            ebene = self.ebene_von_punkt(punkt)
            if not ebene: # wenn None zurückgegeben wird, was passiert, wenn der Punkt nicht ins Quadtree fällt
                ebene = 0
            if ebene >= max_ebene:
                return punkt                        # Bei True liegt das Profil auf einem Quadtree in einer Ebene, wo ein Ufer sehr wahrscheinlich ist

        return None # == False

    # Testet, ob zumindest der Startpunkt anfahrbar ist; falls nicht wird der Endpunkt geprüft und ggf. beide Punkte getauscht
    def TestPunkteAnfahrbar(self, profil):
        pkt_ausserhalb_quadtree = self.zelle.mittelpunkt + Punkt(0, self.zelle.h)
        temp_profil = Profil.ProfilAusZweiPunkten(profil.startpunkt, pkt_ausserhalb_quadtree)
        if not self.linienabfrage(temp_profil): # beide Punkte müssen bei hinreichend gut erfasstem Ufer außerhalb des Sees liegen; Startpunkt ist nicht erreichbar
            temp_profil = Profil.ProfilAusZweiPunkten(profil.endpunkt, pkt_ausserhalb_quadtree)
            if not self.linienabfrage(temp_profil): # auch der Endpunkt ist nicht erreichbar
                return False
            else:
                profil.Flip() # Jetzt ist der Startpunkt (vormals Endpunkt) erreichbar
                return True
        else:
            return True


    def abfrage(self, suchgebiet,gefundene_punkte = None):

        if gefundene_punkte == None:
            gefundene_punkte = []
        if not suchgebiet.gebiet_in_zelle(suchgebiet):
            return False

        for punkt in self.uferpunkte:
            if suchgebiet.enthaelt_punkt(punkt):
                gefundene_punkte.append(punkt)

        if self.geteilt:
            self.nw.abfrage(suchgebiet,gefundene_punkte)
            self.no.abfrage(suchgebiet,gefundene_punkte)
            self.so.abfrage(suchgebiet,gefundene_punkte)
            self.sw.abfrage(suchgebiet,gefundene_punkte)

        return gefundene_punkte

    def zeichnen(self, ax):
        self.zelle.zeichnen(ax)
        #TODO: welche Variante?
        #if not self.geteilt:
        #    self.zelle.draw(ax)
        if self.geteilt:
            self.nw.zeichnen(ax)
            self.no.zeichnen(ax)
            self.so.zeichnen(ax)
            self.sw.zeichnen(ax)

        ax.scatter([p.x for p in self.uferpunkte], [p.y for p in self.uferpunkte], s=1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.invert_yaxis()

        if self.ebene == 0:
            plt.tight_layout()
            plt.savefig('search-quadtree.png', DPI=72)
            plt.show()

# Klasse, die Daten der Messung temporär speichert
class Messgebiet:

    def __init__(self, initale_position_x, initale_position_y, hoehe = 2000, breite = 2000):
        """
        :param initale_position: Mittige Position des zu vermessenden Gebiets (in utm), um das sich der Quadtree legen soll
        :param initiale_ausdehnung: grobe Ausdehnung in Meter
        :param auflösung:
        """
        Initialrechteck = Zelle(initale_position_x, initale_position_y, hoehe, breite)
        self.Uferquadtree = Uferpunktquadtree(Initialrechteck)
        self.topographische_punkte = []
        self.tin = None
        self.profile = []
        self.stern = None
        self.aktuelles_profil = -1
        self.verdichtungsmethode = Verdichtungsmode.AUS
        self.punkt_ausserhalb = Punkt(initale_position_x, initale_position_y + hoehe) # dieser Punkt soll sicher außerhalb des Sees liegen
        self.anzufahrende_kanten = [] # nur zum Plotten auf der Karte
        self.nichtbefahrbareProfile=[]

    # Punkte in das TIN einfügen
    def TIN_berechnen(self, punkte=None):
        if punkte is not None:
            self.PunkteEinlesen(punkte) #TODO: ist es möglich in dem Package pyvista das TIN nur in der Region, wo neue Punkte eingefügt werden, neu zu rechnen und den Rest ohne Neuberechnung zu übernehmen? (Rechenzeit einsparen)
        self.tin = TIN(self.topographische_punkte) # Zum Vermeiden der Bildung von Dreiecken, die außerhalb des Sees liegen (bei Knickpunkten) #TODO ggf. variabel gestalten
        return self.tin

    def Verdichtungsmode(self, mode=None):
        if mode is not None:
            self.verdichtungsmethode = mode
        return self.verdichtungsmethode

    # sucht die nächste anzufahrende Kante und testet, ob die Punkte anfahrbar sind und ob der Weg dahin schiffbar ist
    def NaechsterPunkt(self, position, ufer, entfernungsgewicht):
        if self.verdichtungsmethode == Verdichtungsmode.VERBINDUNG: # Boot ist gerade zum Startpunkt eines Profils gefahren
            if ufer: # Unterbrechung der Messung durch Auflaufen ans Ufer
                #profil = self.profile[self.aktuelles_profil]
                soll_endpunkt = self.profile[self.aktuelles_profil+1].endpunkt
                #print("Sollendpunkt: ", soll_endpunkt)
                self.aktuelles_profil += 1
                #profil.NeuerEndpunkt(position)
                profile = self.stern.FindeVerbindung(position, soll_endpunkt) # hier stehen alle Profile drin, die das Boot abfahren muss, um über zu den verdichtenden Profil zu kommen
                #print("Finde Verbindung",[str(profil) for profil in profile])
                self.profile[self.aktuelles_profil:self.aktuelles_profil] = profile
                punkt = profile[0].endpunkt
                methode = Verdichtungsmode.WEGFÜHRUNG
            else:
                self.aktuelles_profil += 1  # Index liegt jetzt auf dem endgültigen, verdichtenden Profil
                punkt = self.profile[self.aktuelles_profil].endpunkt
                #print("jetzt soll (natürlich dasselbe wie eben) profil angefahren werden", self.profile[self.aktuelles_profil])
                methode = Verdichtungsmode.KANTEN
        elif self.verdichtungsmethode == Verdichtungsmode.KANTEN: # Boot ist gerade auf einem verdichtenden Profil gefahren
            if ufer: # Unterbrechung der Messung durch Auflaufen ans Ufer
                pass # da das Profil bereits zuvor beendet worden ist
                #profil = self.profile[self.aktuelles_profil]
                #profil.NeuerEndpunkt(position)
            self.TIN_berechnen()
            kanten = self.tin.Anzufahrende_Kanten(10,position,entfernungsgewicht)
            #print(kanten, "in nächster Punkt")
            self.anzufahrende_kanten = copy.deepcopy(kanten)
            naechstesProfil = None
            verbindungsprofil = None
            print("Anzahl Kanten", len(kanten))
            zaehler = 0
            for kante in kanten:
                zaehler += 1
                print(zaehler)
                profil = Profil.VerdichtendesProfil(kante)
                print("folgendes Profil berechnet:", profil)
                bestehendeProfile = self.profile+self.nichtbefahrbareProfile
                for existierendesProfil in bestehendeProfile:
                    verbindungsprofil = Profil.ProfilAusZweiPunkten(position,profil.startpunkt)  # das Verbindungsprofil zum Anfahren des verdichtenden Sollprofils
                    if existierendesProfil.PruefProfilExistiert(profil.heading, profil.stuetzpunkt, profilbreite=5, toleranz=0.4, lambda_intervall=[profil.start_lambda, profil.end_lambda]) or existierendesProfil.PruefPunktInProfil(profil.startpunkt,5): #TODO: Parameter aus Attributen der Klasse einfügen
                        if existierendesProfil.PruefProfilExistiert(verbindungsprofil.heading, verbindungsprofil.stuetzpunkt, profilbreite=5, toleranz=0.8, lambda_intervall=[verbindungsprofil.start_lambda, verbindungsprofil.end_lambda]) or existierendesProfil.PruefPunktInProfil(verbindungsprofil.startpunkt,2):
                            break
                else:
                        # TODO: wenn das letzte zu fahrende Profil mit der Lage ins Ufer fällt, sollte es anderweitig angefahren werden (über Umweg); so wie jetzt impl. würde es gar nicht angefahren werden
                    print("Profil zum Anfahren gefunden")

                    anfahrbar = self.Uferquadtree.linienabfrage(verbindungsprofil)  # Punkt, an dem Ufer erreicht oder None, falls kein Ufer dazwischen liegt
                    startpunkt_in_see = self.Uferquadtree.TestPunkteAnfahrbar(profil)
                    print("anfahrbar",anfahrbar,"  Startpunkt im See",startpunkt_in_see)
                    if startpunkt_in_see:  # wenn die Lage des Profils nicht innerhalb des Ufers liegen könnte anfahrbar is None and
                        print("=========")
                        print("dieses verbinsungsprofilprofil messen", verbindungsprofil, "dieses profil messen", profil)
                        naechstesProfil = profil
                        break

            if naechstesProfil is None: # keine zu messenden Profile mehr gefunden bzw. alle Profile fallen außerhalb des Sees
                punkt = None
            else:
                e_start = position.Abstand(naechstesProfil.startpunkt)
                e_end = position.Abstand(naechstesProfil.endpunkt)
                if e_start > e_end:
                    naechstesProfil.Flip()
                punkt = naechstesProfil.startpunkt

                self.profile.append(verbindungsprofil)
                self.profile.append(naechstesProfil)
                self.aktuelles_profil += 1 # Index liegt zunächst auf dem Verbindungsprofil
            methode = Verdichtungsmode.VERBINDUNG
        else: # verbindungsmethode == WEGFÜHRUNG; Boot soll über Umwege zum verdichtenden Profil geführt werden
            # kein Test auf Ufer, da das nicht vorkommen sollte (es werden nur Profile befahren, die bereits befahren wurden)
            self.aktuelles_profil += 1
            punkt = self.profile[self.aktuelles_profil].endpunkt
            if self.aktuelles_profil == len(self.profile)-1:
                methode = Verdichtungsmode.KANTEN
            else:
                methode = Verdichtungsmode.WEGFÜHRUNG
        self.verdichtungsmethode = methode
        return punkt

    # beendet das aktuelle Profil und bestimmt die topographisch bedeutsamen Punkte und liest diese ins Messgebiet ein
    def AktuellesProfilBeenden(self, position, median_punkte):
        profil = self.profile[self.aktuelles_profil]
        profil.NeuerEndpunkt(position)
        profil.MedianPunkteEinfuegen(median_punkte)
        profil.ProfilAbschliessenUndTopoPunkteFinden() # finden der topographisch bedeutsamen Punkte
        self.PunkteEinlesen(profil.topographisch_bedeutsame_punkte)

    # Einfügen von Profilen, die bereits gemessen wurden!
    def ProfileEinlesen(self, profile):
        if type(profile).__name__ != "list":
            profile = [profile]
        for profil in profile:
            self.profile.append(profil)
            self.aktuelles_profil += 1


    # liest die angegebenen Punkte in die Liste der topographisch bedeutsamen Punkte ein
    # nur innerhalb dieser Klasse nutzen! Von außen sollten nur die Profile beendet werden
    def PunkteEinlesen(self, punkte):
        if type(punkte).__name__ != "list":
            punkte = [punkte]
        for punkt in punkte:
            self.topographische_punkte.append(punkt)

    def Uferpunkt_abspeichern(self, punkt):
        self.Uferquadtree.punkt_einfuegen(punkt)

if __name__=="__main__":
    """
    richtung = 50
    stuetz = numpy.array([0,0])

    test_richtung = 0
    test_stuetz = numpy.array([10,0])

    profil = Profil(richtung, stuetz)
    profil.end_lambda = 20
    profil.lamb = 20
    profil.start_lambda = 0
    profil.aktuelles_profil = False

    #quer_richtung = numpy.array([profil.richtung[1], -profil.richtung[0]])
    #punkt = profil.stuetzpunkt + (profil.lamb + 0) * profil.richtung + 5 * quer_richtung

    print(profil.PruefProfilExistiert(test_richtung, test_stuetz, profilbreite=5, toleranz=0.3, lambda_intervall=[0,50]))
    
    # Test Geradenschnitt
    richtung1 = numpy.array([1,1])
    richtung1 = richtung1 / numpy.linalg.norm(richtung1)
    richtung2 = numpy.array([0,1])
    stuetz1 = numpy.array([0,0])
    stuetz2 = numpy.array([5,0])
    print("========")
    print(schneide_geraden(richtung1, stuetz1, richtung2, stuetz2, [0,5], [0,10]))
    
    # Test Quadtree

    startzeit = time.time()

    # Quadtree von DHM berechnen
    testdaten = open("Testdaten_DHM_Tweelbaeke.txt", "r",encoding='utf-8-sig') # ArcGIS Encoding :)
    lines=csv.reader(testdaten,delimiter=";")
    id_testdaten=[]
    x_testdaten=[]
    y_testdaten=[]
    tiefe_testdaten=[]

    # Lesen der Datei
    for line in lines:
        id_testdaten.append(int(line[0]))
        x_testdaten.append(float(line[1]))
        y_testdaten.append(float(line[2]))
        tiefe_testdaten.append(float(line[3]))
    testdaten.close()

    xmin=min(x_testdaten)-10
    xmax=max(x_testdaten)+10
    ymin=min(y_testdaten)-10
    ymax=max(y_testdaten)+10

    xdiff = xmax - xmin
    ydiff = ymax - ymin
    xzentrum = xmin + xdiff / 2
    yzentrum = ymin + ydiff / 2

    initialrechteck = Zelle(xzentrum,yzentrum,xdiff,ydiff)
    Testdaten_quadtree = Uferpunktquadtree(initialrechteck)


    # Generieren des Quadtree
    for i in range(len(id_testdaten)):
        x=x_testdaten[i]
        y=y_testdaten[i]
        tiefe=tiefe_testdaten[i]

        p=Bodenpunkt(x,y,tiefe)

        Testdaten_quadtree.punkt_einfuegen(p)

    fig = plt.figure()
    ax = plt.subplot()
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    plt.gca().set_aspect('equal', adjustable='box')
    #Testdaten_quadtree.zeichnen(ax)

    ax.scatter(x_testdaten, y_testdaten, s=1)
    ax.set_xticks([])
    ax.set_yticks([])

    # Punkte innerhalb eines Suchgebietes finden
    boot_position, = ax.plot([], [], marker='o', markersize=3, color='blue')
    plt_gefundene_punkte, = ax.plot([],[], marker='o', markersize=5,color='red',lw=0)
    plt_suchgebiet,=ax.plot([],[],c='r',lw=1)

    xpos=451880
    ypos=5884944
    pkt = Punkt(xpos, ypos)
    xsuch=5
    ysuch=5
    richtung=50+random.random()
    testprofil=Profil(richtung, pkt, True, 0, 100)
    testprofil.ist_definiert = Profil.Definition.START_UND_ENDPUNKT
    profilpunkte=testprofil.BerechneZwischenpunkte(2)

    for punkt in profilpunkte:
        gefundene_punkte = []
        plt.pause(0.01)
        xpos=punkt.x
        ypos=punkt.y
        boot_position.set_xdata(xpos)
        boot_position.set_ydata(ypos)
        suchgebiet = Zelle(xpos, ypos, xsuch, ysuch)
        suchgebiet.zeichnen(plt_suchgebiet)
        Testdaten_quadtree.abfrage(suchgebiet, gefundene_punkte)
        plt_gefundene_punkte.set_xdata([p.x for p in gefundene_punkte])
        plt_gefundene_punkte.set_ydata([p.y for p in gefundene_punkte])

        time.sleep(0.1)

    #plt.show()


    
    for i in range(0,10000):
        x = random.randint(-1000, 1000)
        y = random.randint(-1000, 1000)

        p = Uferpunkt(x,y)

        Testquadtree.punkt_einfuegen(p)

    print("Quadtree angelegt")
    Testquadtree.zeichnen()

    for i in range(0,1000):
        x = random.randint(-1000, 1000)
        y = random.randint(-1000, 1000)

        p = Uferpunkt(x, y)

        wert = Testquadtree.ebene_von_punkt(p)
        print(i, wert)

    endzeit = time.time()
    zeitdifferenz = endzeit-startzeit
    print(zeitdifferenz)


    # Testdaten für Mesh


    punkt1 = Bodenpunkt(0, 0, 0)
    punkt2 = Bodenpunkt(0, 10, 0)
    punkt3 = Bodenpunkt(15, 10, 0)
    punkt4 = Bodenpunkt(15, 0, 0)
    punkt5 = Bodenpunkt(7.5, 5, 5)
   
    x_koordinaten = []
    y_koordinaten = []
    Testdaten_txt = open("Test_DHM.txt", "r")
    Topographisch_bedeutsame_Bodenpunkte = []
    Datenzeile = Testdaten_txt.readline().replace("\n", "").split(";")
    laenge = 0
    anfangszeit = time.time()
    while laenge < 200:
    #while Datenzeile != ['']:
        tin_punkt = Bodenpunkt(float(Datenzeile[1]), float(Datenzeile[2]), float(Datenzeile[3]))
        punkt_in_liste = [float(Datenzeile[1]), float(Datenzeile[2]), float(Datenzeile[3])]

        x_koordinaten.append(float(Datenzeile[1]))
        y_koordinaten.append(float(Datenzeile[2]))

        Topographisch_bedeutsame_Bodenpunkte.append(tin_punkt)
        # Punktliste_arry.insert(punkt_in_liste)

        print(laenge)

        Datenzeile = Testdaten_txt.readline().replace("\n", "").split(";")
        laenge += 1



    tin = TIN(Topographisch_bedeutsame_Bodenpunkte,10.0)

    endzeit = time.time()

    print(endzeit-anfangszeit)
    naechsteKanten = tin.Anzufahrende_Kanten(5)

    maximalesKantengewicht = 0
    for kante in tin.Kantenliste:
        if kante.gewicht > maximalesKantengewicht: maximalesKantengewicht = kante.gewicht

    x = []
    y = []
    grauwerte = []
    for kante in tin.Kantenliste:
        x1, y1 = kante.Anfangspunkt.x, kante.Anfangspunkt.y
        x2, y2 = kante.Endpunkt.x, kante.Endpunkt.y
        x.append(x1)
        x.append(x2)
        y.append(y1)
        y.append(y2)
        grauwert = kante.gewicht/maximalesKantengewicht
        grauwerte.append((-grauwert+1))

    fig, ax = plt.subplots()

    def connectpoints(x, y, p1, p2, g):
        x1, x2 = x[p1], x[p2]
        y1, y2 = y[p1], y[p2]
        ax.plot([x1, x2], [y1, y2], color= g)


    for i in range(0,len(x),2):
        g = (i)//2
        connectpoints(x,y,i,i+1, str(grauwerte[g]))

    def plot_mat():
        plt.ioff()
        plt.show()
    def plot_tin():
        tin.plot()


    ax.plot(x_koordinaten, y_koordinaten, 'r+')
    #plot_tin()
    plot_mat()

    #threading.Thread(target=plot_mat(), args=(), daemon=True)
    #threading.Thread(target=plot_tin(), args=(), daemon=True)

    #print(time.time()-endzeit)

    print("Break")
    """
