import Sensoren
import numpy
import random
import time
import csv
import matplotlib.pyplot as plt
plt.ion() # Aktivieren eines dynamischen Plots

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
        if z:
            self.z = z
        self.zelle = self.Zellenzugehoerigkeit()

    def Zellenzugehoerigkeit(self):

        # gibt Rasterzelle des Punktes wieder; größe der Rasterzellen muss bekannt sein
        # oder Liste aller Rasterzellen iterieren und Methode enthaelt_punkt() verwenden
        pass


class Uferpunkt(Punkt):

    def __init__(self, x, y, z=None):
        super().__init__(x,y,z)


class Bodenpunkt(Punkt):

    def __init__(self, x, y, z, Sedimentstaerke= None):    # z muss angegeben werde, da Tiefe wichtg; Sedimentstaerke berechnet sich aus Differenz zwischen tiefe mit niedriger und hoher Messfrequenz
        super().__init__(x, y, z)
        self.Sedimentstaerke = Sedimentstaerke


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

    def __init__(self, startpunkt, heading):
        self.profile = []


    def InitProfil(self):
        pass

    def SternFuellen(self):
        pass

    def TestVerdichten(self):
        pass



class Profil:

    # Richtung: Kursrichtung in Gon (im Uhrzeigersinn); stuetzpunkt: Anfangspunkt bei start_lambda=0; start_lambda:
    # end_lmbda ist bei den verdichtenden Profilen gegeben
    def __init__(self, richtung, stuetzpunkt, start_lambda=0, end_lambda=None):
        self.richtung = numpy.array([numpy.sin(richtung*numpy.pi/200), numpy.cos(richtung*numpy.pi/200)]) # 2D Richtungsvektor in Soll-Fahrtrichtung
        self.stuetzpunkt = stuetzpunkt # Anfangspunkt, von dem die Profilmessung startet, wenn start_lambda=0
        self.lamb = start_lambda # aktuelles Lambda der Profilgeraden (da self.richtung normiert, ist es gleichzeitig die Entfernung vom Stuetzpunkt)
        self.start_lambda = start_lambda
        self.end_lambda = end_lambda
        self.aktuelles_profil = True # bei False ist diese Profil bereits gemessen worden
        self.ist_sternprofil = (self.end_lambda is None) # explizit testen, dass es nicht None ist, da es auch 0 sein kann (was als False interpretiert wird)

    # sollte während der Erkundung für das aktuelle Profil immer aufgerufen werden!!!
    def BerechneLambda(self, punkt):
        self.lamb = numpy.dot((punkt - self.stuetzpunkt), self.richtung)

    # Berechnet einen neuen Kurspunkt von Start-Lambda (länge der Fahrtrichtung) und quer dazu (in Fahrtrichtung rechts ist positiv)
    def BerechneNeuenKurspunkt(self, laengs_entfernung, quer_entfernung=0):
        quer_richtung = numpy.array([self.richtung[1], -self.richtung[0]])
        punkt = self.stuetzpunkt + (self.start_lambda + laengs_entfernung) * self.richtung + quer_entfernung * quer_richtung
        return punkt

    # Berechnet Punkte mit gleichmäßigem Abstand
    def BerechneZwischenpunkte(self, abstand=5):
        if self.end_lambda is not None:
            punktliste = []
            lamb = self.start_lambda
            while lamb < self.end_lambda:
                punkt = self.BerechneNeuenKurspunkt(lamb)
                punkt = Punkt(punkt[0], punkt[1])
                punktliste.append(punkt)
                lamb += abstand
            else:
                punkt = self.BerechneNeuenKurspunkt(self.end_lambda)
                punkt = Punkt(punkt[0], punkt[1])
                punktliste.append(punkt)
            return punktliste

    # aktuell gefahrenen Profillänge
    def Profillaenge(self):
        return self.lamb - self.start_lambda

    # Punkt muss mind. Toleranz Meter auf dem Profil liegen für return True
    def PruefPunktAufProfil(self, punkt, toleranz=2):
        abstand = abstand_punkt_gerade(self.richtung, self.stuetzpunkt, punkt)
        return abs(abstand) < toleranz

    # prüft, ob ein geg Punkt innerhalb des Profils liegt (geht nur, wenn self.aktuelles_profil = False ODER wenn self.end_lambda != None
    def PruefPunktInProfil(self, punkt, profilbreite=5):
        if (not self.aktuelles_profil) or (self.end_lambda is not None):
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
        if not self.aktuelles_profil:
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
            raise Exception

    def ProfilAbschliessen(self):
        self.aktuelles_profil = False
        self.end_lambda = self.lamb

# richtung und stuetz sind jeweils die 2D Vektoren der Geraden, und punkt der zu testende Punkt
def abstand_punkt_gerade(richtung, stuetz, punkt):
    richtung = numpy.array([richtung[1], -richtung[0]])
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
        if self.geteilt:
            self.nw.zeichnen(ax)
            self.no.zeichnen(ax)
            self.so.zeichnen(ax)
            self.sw.zeichnen(ax)


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
    """
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
    stuetzpunkt=(xpos,ypos)
    xsuch=5
    ysuch=5
    richtung=50+random.random()
    testprofil=Profil(richtung, stuetzpunkt, 0, 1000)
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

    for i in range(0,1000):
        x = random.randint(-1000, 1000)
        y = random.randint(-1000, 1000)

        p = Uferpunkt(x, y)

        wert = Testquadtree.ebene_von_punkt(p)
        print(i, wert)
    """

    endzeit = time.time()
    zeitdifferenz = endzeit-startzeit
    print(zeitdifferenz)
