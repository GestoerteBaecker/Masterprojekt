import Messgebiet as MG
import numpy
import scipy

Punkt1 = MG.Punkt(0,0)
Punkt2 = MG.Punkt(100,0)
Punkt3 = MG.Punkt(2,0)
Punkt4 = MG.Punkt(10,40)
"""
Profil1 = MG.Profil.ProfilAusZweiPunkten(Punkt1,Punkt2)
Profil2 = MG.Profil.ProfilAusZweiPunkten(Punkt3,Punkt4)

wert = Profil1.PruefProfilExistiert(Profil2.heading,Profil2.stuetzpunkt,5,0.5,[Profil2.start_lambda,Profil2.end_lambda])
print(wert)


stern = MG.Stern.SterneBilden([Punkt1, Punkt2, Punkt3, Punkt4])
print(stern.ebene)
print(stern.weitere_sterne[0].ebene)
print(stern.weitere_sterne[0].weitere_sterne[0].ebene)
print(stern.weitere_sterne[0].weitere_sterne[0].weitere_sterne[0].ebene)

profil = MG.Profil.ProfilAusZweiPunkten(Punkt1,Punkt2, 0)

profil.gemessenes_profil = False
punkte = []
for x in range(0,105,5):
    z = 5/50**2 * (x - 50)**2 - 5
    punkte.append(MG.Bodenpunkt(x, 0, z))
#profil.median_punkte = punkte
"""
richtung = numpy.array([1,0,0])
stuetz = numpy.array([5,0,-2])
punkt = numpy.array([50,0,0])
abstand = MG.abstand_punkt_gerade(richtung, stuetz, punkt)
print(abstand)


#profil = MG.Profil.ProfilAusZweiPunkten(MG.Punkt(452000, 5884870), MG.Punkt(451925.57982760004, 5884894.1805798095), 0.1, 10, 0.5)
#profil.gemessenes_profil = False

profil = MG.Profil.ProfilAusZweiPunkten(MG.Punkt(452000, 5884870), MG.Punkt(451925.57982760004, 5884894.1805798095), 0.1, 10, 0.5)
profil.gemessenes_profil = False
profil.median_punkte = [MG.Bodenpunkt(451998.3356510965, 5884870.540779741, -6.58), MG.Bodenpunkt(451993.3426043859, 5884872.16311896, -7.429), MG.Bodenpunkt(451989.3006141917, 5884873.476441187, -8.173), MG.Bodenpunkt(451984.06980335206, 5884875.176034655, -9.4455), MG.Bodenpunkt(451979.31452077057, 5884876.721119627, -10.13975), MG.Bodenpunkt(451975.27253057633, 5884878.034441854, -10.781500000000001), MG.Bodenpunkt(451970.2794838658, 5884879.656781075, -12.015), MG.Bodenpunkt(451966.4752578006, 5884880.892849051, -12.9165), MG.Bodenpunkt(451961.244446961, 5884882.592442521, -13.299), MG.Bodenpunkt(451957.20245676674, 5884883.9057647465, -13.5465), MG.Bodenpunkt(451951.9716459271, 5884885.605358216, -14.442), MG.Bodenpunkt(451948.1674198619, 5884886.841426194, -14.979), MG.Bodenpunkt(451943.41213728045, 5884888.386511166, -15.324), MG.Bodenpunkt(451941.0344959897, 5884889.159053652, -15.32775), MG.Bodenpunkt(451935.3281568919, 5884891.013155618, -15.205), MG.Bodenpunkt(451930.5728743104, 5884892.55824059, -14.6525)]
"""
punkte = []
for x in range(0,105,5):
    if x % 10 == 0:
        z = 0
    else:
        z = -2
    punkte.append(MG.Bodenpunkt(x, 0, z))
profil.median_punkte = punkte
"""

profil.ProfilAbschliessenUndTopoPunkteFinden(MG.Punkt(451930.5728743104, 5884892.55824059))
print(profil.topographisch_bedeutsame_punkte)
