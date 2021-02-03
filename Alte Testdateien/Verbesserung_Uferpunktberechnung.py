import numpy

def Uferpunktberechnung_alt(Boot_x, Boot_y, dist, heading, Winkeloffset, Streckenoffset):

    """
    if not dist:  # Falls keine Distanz manuell angegeben wird (siehe self.DarstellungGUI) wird auf die Sensordaten zurückgegriffen
        dist = self.AktuelleSensordaten[3].daten
    x = self.AktuelleSensordaten[0].daten[0]
    y = self.AktuelleSensordaten[0].daten[1]
    heading = self.heading
    Winkeloffset = self.Winkeloffset_dist
    """
    #streckr = dist + self.Offset_GNSSmitte_Disto
    strecke = dist + Streckenoffset

    x = Boot_x
    y = Boot_y

    e = x + numpy.sin((heading + Winkeloffset) / (200 / numpy.pi)) * strecke
    n = y + numpy.cos((heading + Winkeloffset) / (200 / numpy.pi)) * strecke

    return [e, n]

def Uferpunktberechnung_neu(Boot_x, Boot_y, dist, heading, Winkeloffset, Streckenoffset):

    x = Boot_x
    y = Boot_y

    e = (x + numpy.sin(heading / (200 / numpy.pi)) * Streckenoffset) + numpy.sin((heading + Winkeloffset) / (200 / numpy.pi)) * dist
    n = (y + numpy.cos(heading / (200 / numpy.pi)) * Streckenoffset) + numpy.cos((heading + Winkeloffset) / (200 / numpy.pi)) * dist
    return [e, n]

Boot_x = 0
Boot_y = 0
dist = 100
heading = 0
Winkeloffset = 100
Streckenoffset = 0.5

alt = Uferpunktberechnung_alt(Boot_x, Boot_y, dist, heading, Winkeloffset, Streckenoffset)
neu = Uferpunktberechnung_neu(Boot_x, Boot_y, dist, heading, Winkeloffset, Streckenoffset)

print(alt,"\n",neu)