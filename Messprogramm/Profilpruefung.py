import Messgebiet as MG
import numpy
import scipy

Punkt1 = MG.Punkt(0,0)
Punkt2 = MG.Punkt(10,40)
Punkt3 = MG.Punkt(2,0)
Punkt4 = MG.Punkt(10,40)

Profil1 = MG.Profil.ProfilAusZweiPunkten(Punkt1,Punkt2)
Profil2 = MG.Profil.ProfilAusZweiPunkten(Punkt3,Punkt4)

wert = Profil1.PruefProfilExistiert(Profil2.heading,Profil2.stuetzpunkt,5,0.5,[Profil2.start_lambda,Profil2.end_lambda])
print(wert)
