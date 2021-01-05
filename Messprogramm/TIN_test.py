import Messgebiet as Messgebiet
import numpy as np
import pyvista as pv
# Einlesen der Testdaten================================================================================================

#Testdaten_txt = open("Test_DHM.txt","r")
Testdaten_txt = open("Referenz_Tweelbaeke.txt","r")

Datenzeile = Testdaten_txt.readline().replace("\n","").split(";")

print(Datenzeile[1])

laenge = 0

TINpunkte = []

Messpunkte = []

while Datenzeile != ['']:

    Messpunkt = Messgebiet.Bodenpunkt(float(Datenzeile[1]),float(Datenzeile[2]),float(Datenzeile[4]))
    punkt_in_liste = [float(Datenzeile[1]),float(Datenzeile[2]),float(Datenzeile[4])]

    TINpunkte.append(Messpunkt)

    Datenzeile = Testdaten_txt.readline().replace("\n", "").split(";")
    laenge +=1



Punktliste_array = np.zeros(shape=(laenge,3))

i=0
for punkt in TINpunkte:
    punkt_in_liste = [punkt.x, punkt.y, punkt.z]
    Punktliste_array[i] = punkt_in_liste
    i+=1

# Test pyvista ==========================================================================================================

cloud = pv.PolyData(Punktliste_array)
mesh = cloud.delaunay_2d()
faces = mesh.faces
mesh.plot(show_edges=True)

#https://docs.pyvista.org/examples/00-load/create-tri-surface.html

print("test")
#indices = hull.simplices
#vertices = Punktliste[indices]