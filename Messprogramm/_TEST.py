import numpy
import time
import Messgebiet

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