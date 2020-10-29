import Sensoren

class Messprogramm:

    def __init__(self, initale_position, initiale_ausdehnung, auflösung):
        """
        :param initale_position: Mittige Position des zu vermessenden Gebiets (in utm), um das sich der Quadtree legen soll
        :param initiale_ausdehnung: grobe Ausdehnung in Meter
        :param auflösung:
        """
        self.quadtree = None

    def daten_einspeisen(self, punkt, datenpaket):
        pass

    def daten_abfrage(self, punkt):
        pass