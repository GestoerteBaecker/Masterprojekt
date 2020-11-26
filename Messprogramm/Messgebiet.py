import numpy
import random
import time
import csv
import matplotlib.pyplot as plt
plt.ion() # Aktivieren eines dynamischen Plots
import enum
import copy
import numpy as np
import pyvista as pv

# Definition von Enums zur besseren Lesbarkeit
# Tracking Mode, das das Boot haben soll
class TrackingMode(enum.Enum):
    PROFIL = 0
    VERBINDUNG = 1 # auf Verbindungsstück zwischen zwei verdichtenden Profilen
    AUS = 2

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


class Uferpunkt(Punkt):

    def __init__(self, x, y, z=None):
        super().__init__(x,y,z)


class Bodenpunkt(Punkt):

    def __init__(self, x, y, z, Sedimentstaerke= None):    # z muss angegeben werde, da Tiefe wichtg; Sedimentstaerke berechnet sich aus Differenz zwischen tiefe mit niedriger und hoher Messfrequenz
        super().__init__(x, y, z)
        self.Sedimentstaerke = Sedimentstaerke

    # Berechnet die Neigung zwischen dem self und bodenpunkt; bei zurueck=True wird das Gefälle vom Bodenpunkt zum self-Punkt betrachtet (bodenpunkt liegt in Fahrtrichtung nach hinten)
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

    def leange(self):
        pass

    def mitte(self):
        x = (self.Anfangspunkt.x + self.Endpunkt.x) / 2
        y = (self.Anfangspunkt.y + self.Endpunkt.y) / 2
        z = (self.Anfangspunkt.z + self.Endpunkt.z) / 2

        mitte = Punkt(x,y,z)

        return (mitte)

    def winkel(self):

        n1_list = self.Dreiecke[0].Normalenvector.tolist()
        n2_list = self.Dreiecke[1].Normalenvector.tolist()

        n1 = numpy.array([n1_list[0], n1_list[1], n1_list[2]])
        n2 = numpy.array([n2_list[0], n2_list[1], n2_list[2]])

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

    def __init__(self, Punktliste, Max_len = 0.0):

        self.Punktliste_array = np.zeros(shape=(len(Punktliste), 3))
        self.TIN_punkte = []
        self.Kantenliste = []
        self.Dreieckliste = []


        # Punkte in Numpy-Array überführen
        for i, punkt in enumerate(Punktliste):
            punkt_in_liste = [punkt.x, punkt.y, punkt.z]
            self.Punktliste_array[i] = punkt_in_liste

        # Triangulation mit dem PyVista-Package
        cloud = pv.PolyData(self.Punktliste_array)

        if Max_len == 0.0:
            self.mesh = cloud.delaunay_2d()
        else:
            self.mesh = cloud.delaunay_2d(Max_len)

        # Punkt ID's belegen

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
                                    if Kantealt.Anfangspunkt == punkt2:
                                        vorhanden = True

                                # Kante Bilden und abspeichern
                                if not vorhanden:
                                    kante = TIN_Kante(punkt1,punkt2,[dreieckobjekt,dreieckalt])
                                    self.Kantenliste.append(kante)
                                    dreieckobjekt.kanten += 1
                                    dreieckalt.kanten += 1
                                    if dreieckobjekt.kanten == 3: dreieckobjekt.offen = False
                                    if dreieckobjekt.kanten == 3: dreieckalt.offen = False

            self.Dreieckliste.append(dreieckobjekt)


    def Anzufahrende_Kanten(self):
        pass

    def plot(self):
        self.mesh.plot()


class Zelle:

    def __init__(self,cx, cy, w, h):    # Rasterzelle mit mittelpunkt, weite und Höhe definieren, siehe
        self.cx, self.cy = cx, cy
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
    def __init__(self, startpunkt, heading, winkelinkrement=50, grzw_seitenlaenge=500, initial=True, profil_grzw_dichte_topo_pkt=0.1, profil_grzw_neigungen=50):
        self.profile = []
        self.aktuelles_profil = 0 # Index des aktuellen Profils bezogen auf self.aktueller_stern
        self.initial = initial # nur für den ersten Stern True; alle verdichtenden sollten False sein
        self.mittelpunkt = None
        self.mittelpunktfahrt = False # sagt aus, ob das Boot gerade Richtung Mittelpunkt fährt
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

    # muss zwingend nach der Initialisierung aufgerufen werden!
    def InitProfil(self):
        profil = Profil(self.heading, self.startpunkt, stuetz_ist_start=True, start_lambda=0, end_lambda=None, grzw_dichte_topo_pkt=self.profil_grzw_dichte_topo_pkt, grzw_neigungen=self.profil_grzw_neigungen)
        self.profile.append(profil)
        return profil.BerechneNeuenKurspunkt(2000, 0, punkt_objekt=True) # Punkt liegt in 2km Entfernung

    # fügt weitere Profile in gegebenen Winkelinkrementen ein, die anschließend befahren werden
    def SternFuellen(self): #TODO: testen
        stern = self.aktueller_stern
        mitte = stern.mittelpunkt
        start_winkel = stern.profile[0].heading + stern.winkelinkrement
        winkel = start_winkel
        #rot_matrix = numpy.array([[numpy.cos(stern.winkelinkrement*numpy.pi/200), numpy.sin(stern.winkelinkrement*numpy.pi/200)], [-numpy.sin(stern.winkelinkrement*numpy.pi/200), numpy.cos(stern.winkelinkrement*numpy.pi/200)]])
        while winkel < start_winkel + 200 - 1.001*stern.winkelinkrement:
            #richtung = numpy.dot(rot_matrix, richtung)
            profil = Profil(winkel, mitte, stuetz_ist_start=False, start_lambda=0, end_lambda=None, grzw_dichte_topo_pkt=stern.profil_grzw_dichte_topo_pkt, grzw_neigungen=stern.profil_grzw_neigungen)
            stern.profile.append(profil)
            winkel += stern.winkelinkrement

    # test der Überschreitung des Grenzwerts der Länge eines Profils
    def TestVerdichten(self):

        def berechne_mitte(stern, profil, entfernung_vom_startpunkt):
            neue_mitte = profil.BerechneNeuenKurspunkt(entfernung_vom_startpunkt, punkt_objekt=True)
            neuer_stern = Stern(neue_mitte, profil.heading, stern.winkelinkrement, stern.grzw_seitenlaenge, initial=False, profil_grzw_dichte_topo_pkt=stern.profil_grzw_dichte_topo_pkt, profil_grzw_neigungen=stern.profil_grzw_neigungen)
            # nicht stern.init, da dieses Profil bereits vom übergeordneten Stern gemessen wurde; stattdessen soll dieses Profil als bereits gemessen übernommen werden
            neuer_stern.profile.append(copy.deepcopy(stern.profile[0]))
            return neuer_stern

        stern = self.aktueller_stern
        if len(stern.weitere_sterne) == 0:
            neue_messung = False
            for profil in stern.profile:
                gesamtlänge = profil.Profillaenge(akt_laenge=False)
                profil.BerechneLambda(stern.mittelpunkt.ZuNumpyPunkt(zwei_dim=True))
                seitenlänge_vor_mitte = profil.Profillaenge(akt_laenge=True) #Anfang bis Mitte
                seitenlänge_nach_mitte = gesamtlänge - seitenlänge_vor_mitte # Mitte bis Ende
                if seitenlänge_vor_mitte > stern.grzw_seitenlaenge:
                    neue_messung = True
                    entfernung = seitenlänge_vor_mitte/2
                elif seitenlänge_nach_mitte > stern.grzw_seitenlaenge:
                    neue_messung = True
                    entfernung = seitenlänge_vor_mitte + seitenlänge_nach_mitte / 2
                else:
                    continue
                neuer_stern = berechne_mitte(stern, profil, entfernung)
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
        return self.aktueller_stern is not None # falls es keine Sterne mehr gibt, wird False ausgegeben

    # durchläuft alle Profile und gibt das aktuelle Profil aus (None, falls keins gefunden wurde)
    #TODO: deprecated
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
            self.TestVerdichten() # bewirkt nur eine Verdichtung, wenn noch keine weiteren Sterne in stern vorliegen
            aktueller_stern = self.AktuellerStern()
            if not aktueller_stern:
                return None
            else:
                self.aktueller_stern.aktuelles_profil = 0
                return self.aktueller_stern.MittelpunktAnfahren()
        stern.aktuelles_profil += 1
        return stern.MittelpunktAnfahren()

    # diese Methode immer aufrufen, sobald das Ufer angefahren wird ODER ein Punkt erreicht wird, der angefahren werden sollte
    # punkt: Endpunkt, an dem das Boot auf das Ufer trifft; mode: TrackingMode des Bootes
    # Rückgabe: Liste mit Punkt, der angefahren werden sollte und welche Tracking-Methode das Boot haben sollte
    def NaechsteAktion(self, punkt, mode):
        stern = self.aktueller_stern
        if mode == TrackingMode.PROFIL: # das Boot soll Messungen auf dem Profil vornehmen
            punkt = stern.ProfilBeenden(punkt)
            mode = TrackingMode.AUS
            stern.mittelpunktfahrt = True
        elif mode == TrackingMode.AUS and stern.mittelpunktfahrt: # das Boot soll keine Messungen vornehmen und zurück zur Sternmitte fahren
            punkt = stern.profile[stern.aktuelles_profil].BerechneNeuenKurspunkt(-2000, punkt_objekt=True)
            mode = TrackingMode.AUS
            stern.mittelpunktfahrt = False
        elif mode == TrackingMode.AUS and not stern.mittelpunktfahrt:
            profil = stern.profile[stern.aktuelles_profil]
            profil.ProfilBeginnen(punkt)
            punkt = profil.BerechneNeuenKurspunkt(2000, punkt_objekt=True)
            mode = TrackingMode.PROFIL
        if punkt is None: # dann ist der Stern / die Sterne abgeschlossen
            return
        return [punkt, mode]

    def MittelpunktAnfahren(self):
        stern = self.aktueller_stern
        if stern.mittelpunkt:
            return stern.mittelpunkt

    # pflegt bereits Median-gefilterte Punkte in die entsprechende Liste des aktuellen Profils ein; punkt kann auch eine einziger Punkt sein
    def MedianPunkteEinlesen(self, punkte):
        stern = self.aktueller_stern
        if type(punkte).__name__ != "list":
            punkte = [punkte]
        for punkt in punkte:
            stern.profile[stern.aktuelles_profil].MedianPunktEinfuegen(punkt)

    # aus den einzelnen Profilen für das TIN
    def TopographischBedeutsamePunkteAbfragen(self):
        # auch wieder rekursiv aus allen Sternen und den Profilen darin
        topographisch_bedeutsame_punkte = []
        def sterne_durchlaufen(self):
            for profil in self.profile:
                topographisch_bedeutsame_punkte.extend(profil.topographisch_bedeutsame_punkte)
            for stern in self.weitere_sterne:
                sterne_durchlaufen(stern)
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
            if self.end_lambda is None:
                self.ist_definiert = Profil.Definition.RICHTUNG_UND_START
            else:
                self.ist_definiert = Profil.Definition.START_UND_ENDPUNKT
        else:
            self.ist_definiert = Profil.Definition.NUR_RICHTUNG

    @classmethod
    def VerdichtendesProfil(cls, dreieckskante):
        #TODO: implementieren
        # dreieckskante ist ein TIN_Kante-Objekt (besitzt Start und Entpunkt)
        # hier soll eine Dreieckskante eingesetzt werden (wie auch immer definiert) und ein Profil ausgegeben werden, das so direkt abgefahren werden kann
        # switch Start- und Endpunkt als Methode einführen, da einer der Punkte evtl außerhalb des Gebiets liegen kann und der jeweils andere angefahren werden sollte
        profil = cls(...)
        return profil


    # wenn das Boot im Stern von der Mitte am Ufer ankommt und mit der Messung entlang des Profils beginnen soll (punkt ist der gefundene Punkt am Ufer)
    def ProfilBeginnen(self, punkt):
        if self.ist_definiert == Profil.Definition.NUR_RICHTUNG:
            # Projektion des neuen Stuetzvektors (punkt) auf die vorhandene Gerade
            richtung = numpy.array([self.richtung[1], -self.richtung[0]])
            punkt = punkt.ZuNumpyPunkt(zwei_dim=True)
            self.stuetzpunkt = punkt - richtung * (numpy.dot((punkt - self.stuetzpunkt), richtung))
            self.ist_definiert = Profil.Definition.RICHTUNG_UND_START
            self.start_lambda = 0

    def MedianPunktEinfuegen(self, punkt):
        if self.ist_definiert.value > 0:
            self.median_punkte.append(punkt)
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

    # aktuell gefahrenen Profillänge, falls Profil abgeschlossen ist, ist es die Gesamtlänge
    def Profillaenge(self, akt_laenge=True):
        if akt_laenge:
            return self.lamb - self.start_lambda
        else: # Länge, wenn end_lambda bekannt
            return self.end_lambda - self.start_lambda

    # Punkt muss mind. Toleranz Meter auf dem Profil liegen für return True
    def PruefPunktAufProfil(self, punkt, toleranz=2):
        abstand = abstand_punkt_gerade(self.richtung, self.stuetzpunkt, punkt)
        return abs(abstand) < toleranz

    # prüft, ob ein geg Punkt innerhalb des Profils liegt (geht nur, wenn self.gemessenes_profil = True ODER wenn self.end_lambda != None
    def PruefPunktInProfil(self, punkt, profilbreite=5):
        if self.ist_definiert == Profil.Definition.START_UND_ENDPUNKT:
            if self.PruefPunktAufProfil(punkt, profilbreite):
                lamb = numpy.dot(self.richtung, (punkt - self.stuetzpunkt))
                return self.start_lambda <= lamb <= self.end_lambda
            else:
                return False

    # Überprüft, ob das Profil, das aus den Argumenten initialisiert werden KÖNNTE, ähnlich zu dem self Profil ist (unter Angabe der Toleranz)
    # Toleranz ist das Verhältnis der Überdeckung beider Profilbreiten zu dem self-Profil; bei 0.3 dürfen max 30% des self-Profilstreifens mit dem neuen Profil überlagert sein
    # Profilbreite: Breite zu einer Seite (also Gesamtbreite ist profilbreite*2)
    # bei return True sollte das Profil also nicht gemessen werden
    # lambda_intervall: bei None, soll das neue Profil unendlich lang sein, bei Angabe eben zwischen den beiden Lambdas liegen (als Liste, zB [-20,20] bei lamb 0 ist der Geradenpunkt gleich dem Stützpunkt)
    def PruefProfilExistiert(self, richtung, stuetzpunkt, profilbreite=5, toleranz=0.3, lambda_intervall=None):
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
                if end_punkt is None:
                    raise Exception("Es muss ein Endpunkt des Profils angegeben werden.")
                self.end_lambda = self.BerechneLambda(end_punkt.ZuNumpyPunkt(zwei_dim=True))
                self.ist_definiert = Profil.Definition.START_UND_ENDPUNKT

            # ab hier berechnen der topographisch bedeutsamen Punkte (der allererste und -letzte Medianpunkt werden nach jetztigem Schema nie eingefügt)
            mind_anzahl_topo_punkte = int(round(self.grzw_dichte_topo_pkt * self.Profillaenge(), 0))
            grzw_winkel_rad = self.grzw_neigungen/200*numpy.pi
            if len(self.median_punkte) > mind_anzahl_topo_punkte:
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

                # weitere Punkte einfügen, falls nicht genügend Median Punkte gefunden wurden
                while len(index_zugefügter_medianpunkte) < mind_anzahl_topo_punkte:
                    größter_abstand = 0
                    index = None
                    # durchlaufen aller "Geraden", die durch zwei der bereits gefundenen topographisch bedeutsamen Punkte gebildet werden
                    test_indizes = [0, *index_zugefügter_medianpunkte, len(index_zugefügter_medianpunkte)-1] # damit die "Geraden", die vom Start und zum Endpunkt gehen mit berücksichtigt werden
                    for i in range(len(test_indizes)-1):
                        median_index_start = test_indizes[i] # index, die auch in index_zugefügter_medianpunkte drin stehen
                        median_index_ende = test_indizes[i+1]
                        stuetz = self.median_punkte[median_index_start].ZuNumpyPunkt()
                        richtung = self.median_punkte[median_index_ende].ZuNumpyPunkt() - stuetz
                        richtung = richtung / numpy.linalg.norm(richtung)
                        # durchlaufen aller Punkte zwischen den beiden "Geraden"-definierenden Punkten
                        for median_index in range(median_index_start+1, median_index_ende):
                            abstand = abs(abstand_punkt_gerade(richtung, stuetz, self.median_punkte[median_index]))
                            if größter_abstand < abstand:
                                größter_abstand = abstand
                                index = median_index
                    index_zugefügter_medianpunkte.append(index)
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
        Pruefpunkte = profil.BerechneZwischenpunkte()

        for punkt in Pruefpunkte:
            ebene = self.ebene_von_punkt(punkt)
            if ebene >= max_ebene:
                return True                         # Bei True liegt das Profil auf einem Quadtree in einer Ebene, wo ein Ufer sehr wahrscheinlich ist

        return False

    def abfrage(self, suchgebiet, gefundene_punkte):
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
        self.TIN = None

    def TIN_berechnen(self):
        pass

    def daten_einspeisen(self, punkt, datenpaket):
        pass

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
    """
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


    """
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
        """
    """

    endzeit = time.time()
    zeitdifferenz = endzeit-startzeit
    print(zeitdifferenz)
    """

    # Testdaten für Mesh

    punkt1 = Bodenpunkt(0, 0, 0)
    punkt2 = Bodenpunkt(0, 10, 0)
    punkt3 = Bodenpunkt(15, 10, 0)
    punkt4 = Bodenpunkt(15, 0, 0)
    punkt5 = Bodenpunkt(7.5, 5, 0 )

    Topographisch_bedeutsame_Bodenpunkte = [punkt1, punkt2, punkt3, punkt4, punkt5]

    tin = TIN(Topographisch_bedeutsame_Bodenpunkte)

    for kante in tin.Kantenliste:
        print(kante.winkel())

    print("Break")