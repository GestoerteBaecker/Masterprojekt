import Messgebiet as MG
import numpy
Punkt1 = MG.Punkt(1,1)
Punkt2 = MG.Punkt(1,100)
Punkt3 = MG.Punkt(-20,50)
Punkt4 = MG.Punkt(20,50)

Profil1 = MG.Profil.ProfilAusZweiPunkten(Punkt1,Punkt2)
Profil2 = MG.Profil.ProfilAusZweiPunkten(Punkt3,Punkt4)

wert = Profil1.PruefProfilExistiert(Profil2.heading,Profil2.stuetzpunkt,5,0.5,[Profil2.start_lambda,Profil2.end_lambda])
print(wert)


x = numpy.array([0,5,5,0])
y = numpy.array([0,0,5,5])
print(MG.Flächenberechnung(x, y))