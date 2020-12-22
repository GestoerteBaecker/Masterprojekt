import Messprogramm.Messgebiet as MG
Punkt1 = MG.Punkt(1,1)
Punkt2 = MG.Punkt(1,100)
Punkt3 = MG.Punkt(40,101)

Profil1 = MG.Profil.ProfilAusZweiPunkten(Punkt1,Punkt2)
Profil2 = MG.Profil.ProfilAusZweiPunkten(Punkt1,Punkt3)

wert = Profil1.PruefProfilExistiert(Profil2.heading,Profil2.stuetzpunkt,5,0.5,[Profil2.start_lambda,Profil2.end_lambda])
print(wert)