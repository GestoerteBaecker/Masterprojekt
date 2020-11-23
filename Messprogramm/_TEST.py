import numpy
import time
import Messgebiet

"""
t = time.time()
start_punkt = Messgebiet.Bodenpunkt(0,0,0)
profil = Messgebiet.Profil(50, start_punkt, True, 0, 100, 0, 50)

for pkt in range(10):
    if pkt < 5:
        z = 10*pkt
    else:
        z = 0
    punkt = Messgebiet.Bodenpunkt(10*pkt, 10*pkt, z)
    profil.MedianPunktEinfuegen(punkt)

profil.ProfilAbschliessen()
topo = profil.topographisch_bedeutsame_punkte
for pkt in topo:
    print(pkt)
print(time.time()-t)
"""

def Test(richtung, inkr):
    liste = []
    winkel = 0
    rot_matrix = numpy.array([[numpy.cos(inkr*numpy.pi/200), numpy.sin(inkr*numpy.pi/200)], [-numpy.sin(inkr*numpy.pi/200), numpy.cos(inkr*numpy.pi/200)]])
    while (400-winkel-inkr) > inkr/10:
        richtung = rot_matrix.dot(richtung)
        liste.append(richtung)
        winkel += inkr
    return liste

richtungen = Test(numpy.array([0, 1]), 50)
for r in richtungen:
    print(r)
