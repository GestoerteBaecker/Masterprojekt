import Sensoren
import numpy
from Boot import Flächenberechnung

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

    # Berechnet einen neuen Kurspunkt in 50m Entfernung
    def BerechneNeuenKurspunkt(self, entfernung=50):
        punkt = self.stuetzpunkt + (self.lamb + entfernung) * self.richtung
        return punkt

    def Profillaenge(self):
        return self.lamb - self.start_lambda

    # Punkt muss mind. Toleranz Meter auf dem Profil liegen für return True
    def PruefPunktAufProfil(self, punkt, toleranz=2):
        pass

    # Überprüft, ob das Profil, das aus den Argumenten initialisiert werden KÖNNTE, ähnlich zu dem self Profil ist (unter Angabe der Toleranz)
    # Toleranz ist das Verhältnis der Überdeckung beider Profilbreiten zu dem self-Profil; bei 0.3 dürfen max 30% des self-Profilstreifens mit dem neuen Profil überlagert sein
    # Profilbreite: Breite zu einer Seite (also Gesamtbreite ist profilbreite*2)
    def PruefProfilExistiert(self, richtung, stuetzpunkt, profilbreite=5, toleranz=0.3):
        if not self.aktuelles_profil:
            fläche = self.Profillaenge() * 2 * profilbreite
            x = []
            y = []
            # Clipping der neuen Profilfläche auf die alte

            überdeckung = Flächenberechnung(numpy.array(x), numpy.array(y))
            return (überdeckung / fläche) < toleranz
        else:
            raise Exception

    def ProfilAbschliessen(self):
        self.aktuelles_profil = False
        self.end_lambda = self.lamb

# richtung und stuetz sind jeweils die 2D Vektoren der Geraden, und punkt der zu testende Punkt
def abstand_punkt_gerade(richtung, stuetz, punkt):
    richtung = numpy.array([richtung[1], -richtung[0]])
    return numpy.dot(richtung, (punkt - stuetz))


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

    punkt = Bodenpunkt(1,2,3,0.5)
    print(type(punkt).__name__)