import Sensoren
import numpy

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


class Profil:

    # Richtung: Kursrichtung in Gon (im Uhrzeigersinn); stuetzpunkt: Anfangspunkt bei start_lambda=0; start_lambda:
    def __init__(self, richtung, stuetzpunkt, start_lambda=0):
        self.richtung = numpy.array([numpy.sin(richtung*numpy.pi/200), numpy.cos(richtung*numpy.pi/200)]) # 2D Richtungsvektor in Soll-Fahrtrichtung
        self.stuetzpunkt = stuetzpunkt # Anfangspunkt, von dem die Profilmessung startet, wenn start_lambda=0
        self.lamb = start_lambda # aktuelles Lambda der Profilgeraden (da self.richtung normiert, ist es gleichzeitig die Entfernung vom Stuetzpunkt)
        self.start_lambda = start_lambda
        self.end_lambda = None
        self.aktuelles_profil = True # bei False ist diese Profil bereits gemessen
        self.ist_sternprofil = True # Klasse wird auch für die parallelen Profile verwendet
        self.getrackte_neigungen = [] # während der Erkundung erfasste Neigungen des Seegrunds, die für die spätere Profildichte interessant wird

    # sollte während der Erkundung für das aktuelle Profil immer aufgerufen werden!!!
    def BerechneLambda(self, punkt):
        self.lamb = numpy.dot((punkt - self.stuetzpunkt), self.richtung)

    # Berechnet einen neuen Kurspunkt in 50m Entfernung (länge der Fahrtrichtung) und quer dazu (in Fahrtrichtung rechts ist positiv)
    def BerechneNeuenKurspunkt(self, laengs_entfernung=50, quer_entfernung=0):
        quer_richtung = numpy.array([self.richtung[1], -self.richtung[0]])
        punkt = self.stuetzpunkt + (self.lamb + laengs_entfernung) * self.richtung + quer_entfernung * quer_richtung
        return punkt

    def Profillaenge(self):
        return self.lamb - self.start_lambda

    # Punkt muss mind. Toleranz Meter auf dem Profil liegen für return True
    def PruefPunktAufProfil(self, punkt, toleranz=2):
        abstand = abstand_punkt_gerade(self.richtung, self.stuetzpunkt, punkt)
        return abs(abstand) < toleranz

    # Überprüft, ob das Profil, das aus den Argumenten initialisiert werden KÖNNTE, ähnlich zu dem self Profil ist (unter Angabe der Toleranz)
    # Toleranz ist das Verhältnis der Überdeckung beider Profilbreiten zu dem self-Profil; bei 0.3 dürfen max 30% des self-Profilstreifens mit dem neuen Profil überlagert sein
    # Profilbreite: Breite zu einer Seite (also Gesamtbreite ist profilbreite*2)
    def PruefProfilExistiert(self, richtung, stuetzpunkt, profilbreite=5, toleranz=0.3):
        if not self.aktuelles_profil:
            self.lamb = 0
            richtung = richtung / numpy.linalg.norm(richtung)
            fläche = (self.end_lambda-self.start_lambda) * 2 * profilbreite
            x = []
            y = []
            # Clipping der neuen Profilfläche auf die alte
            eckpunkte = [] # Eckpunkte des self-Profils
            for i in range(4):
                faktor = -1
                if i % 3 == 0:
                    faktor = 1
                punkt = self.BerechneNeuenKurspunkt(0, faktor * profilbreite)
                eckpunkte.append(punkt)
                if i == 1:
                    self.lamb = self.end_lambda
            pruef_stuetz = [] # Stützpunkte der beiden parallelen zunächst unendlich langen Geraden der Begrenzung des neu zu prüfenden Profils
            temp_pruef_quer_richtung = numpy.array([richtung[1], -richtung[0]])
            pruef_stuetz.append(stuetzpunkt - profilbreite * temp_pruef_quer_richtung)
            pruef_stuetz.append(stuetzpunkt + profilbreite * temp_pruef_quer_richtung)
            test_richtung = numpy.array([-self.richtung[1], self.richtung[0]]) # Richtung der aktuell betrachteten Kante des self Profils
            for i, eckpunkt in enumerate(eckpunkte):
                # Test, ob Eckpunkt innerhalb des neuen Profils liegt und falls ja, hinzufügen
                abst_g1 = abstand_punkt_gerade(richtung, pruef_stuetz[0], eckpunkt)
                abst_g2 = abstand_punkt_gerade(richtung, pruef_stuetz[1], eckpunkt)
                if (abst_g1 < 0 and abst_g2 > 0) or (abst_g1 > 0 and abst_g2 < 0):
                    x.append(eckpunkt[0])
                    y.append(eckpunkt[1])
                p1 = schneide_geraden(test_richtung, eckpunkt, richtung, pruef_stuetz[0])
                p2 = schneide_geraden(test_richtung, eckpunkt, richtung, pruef_stuetz[1])
                if p1 is None and p2 is None: # wenn es keine oder nur sehr schleifende Schnittpunkte gibt, muss anders getestet werden
                    abst_g1 = abstand_punkt_gerade(test_richtung, eckpunkt, pruef_stuetz[0])# Abstand des Stützvektors der Geraden 1 des zu testenden Profils
                    abst_g2 = abstand_punkt_gerade(test_richtung, eckpunkt, pruef_stuetz[1])
                    if (abst_g1 < 0 and abst_g2 > 0) or (abst_g1 > 0 and abst_g2 < 0):
                        p1 = eckpunkt
                        p2 = eckpunkte[(i+1)%4]
                if p1 is not None and p2 is not None:
                    abst_stuetz_p1 = numpy.linalg.norm(p1 - eckpunkt)
                    abst_stuetz_p2 = numpy.linalg.norm(p2 - eckpunkt)
                    if abst_stuetz_p1 <= abst_stuetz_p2:
                        x.append(p1[0])
                        x.append(p2[0])
                        y.append(p1[1])
                        y.append(p2[1])
                    else:
                        x.append(p2[0])
                        x.append(p1[0])
                        y.append(p2[1])
                        y.append(p1[1])
                test_richtung = numpy.array([test_richtung[1], -test_richtung[0]])
            # entfernen der Schnittpunkte, die außerhalb des Profils liegen
            for eckpunkt in eckpunkte:
                for i in range(len(x) - 1, -1, -1):
                    test_punkt = numpy.array([x[i], y[i]])
                    abstand= abstand_punkt_gerade(test_richtung, eckpunkt, test_punkt)
                    if abstand < -0.001:
                        x.pop(i)
                        y.pop(i)
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
    a = numpy.dot(richtung, (punkt - stuetz))
    return a

# Überprüfung, dass sich die Geraden schneiden, muss außerhalb der Funktion getestet werden!
def schneide_geraden(richtung1, stuetz1, richtung2, stuetz2):
    det = richtung1[0]*richtung2[1]-richtung2[0]*richtung1[1]
    if abs(det) < 0.0000001: # falls kein oder sehr schleifender Schnitt existiert
        return None
    faktor = 1 / det
    # betrachten der Komponenten nur für die erste Gerade
    diff_stuetz_x = stuetz2[0] - stuetz1[0]
    lamb = (richtung2[1]*faktor*diff_stuetz_x - richtung2[0]*faktor*diff_stuetz_x)
    punkt = stuetz1 + lamb * richtung1
    return punkt


# Klasse, die Daten der Messung temporär speichert
class Messgebiet:

    def __init__(self, initale_position, initiale_ausdehnung, auflösung):
        """
        :param initale_position: Mittige Position des zu vermessenden Gebiets (in utm), um das sich der Quadtree legen soll
        :param initiale_ausdehnung: grobe Ausdehnung in Meter
        :param auflösung:
        """
        self.quadtree = None
        self.uferlinie = None

    def daten_einspeisen(self, punkt, datenpaket):
        pass

    def daten_abfrage(self, punkt):
        pass

    def Zellenraster_erzeugen(self):
        self.zellenraster = False

    def Punkt_abspeichern(self):
        #Punkt zu einer Zelle zuordnen und in zelle abspeichern
        pass

if __name__=="__main__":

    richtung = 50
    stuetz = numpy.array([0,0])

    test_richtung = numpy.array([0,1])
    test_stuetz = numpy.array([20,0])

    profil = Profil(richtung, stuetz)
    profil.end_lambda = 20
    profil.lamb = 20
    profil.aktuelles_profil = False

    quer_richtung = numpy.array([profil.richtung[1], -profil.richtung[0]])
    punkt = profil.stuetzpunkt + (profil.lamb + 0) * profil.richtung + 5 * quer_richtung

    print(profil.PruefProfilExistiert(test_richtung, test_stuetz))
