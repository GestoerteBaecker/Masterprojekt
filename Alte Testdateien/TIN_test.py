import Messprogramm.Messgebiet as Messgebiet
#import tinned_python
import trimesh
import open3d as o3d
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as tri
import pyvista as pv


def Bodenpunktberechnung(Bodendaten):

    z_werte = []                    #Liste, da nicht mittelwert, sondern Median berechnet wird
    for messung in Bodendaten:



        z_boden = messung.z
        z_werte.append(z_boden)

    mitte = (len(Bodendaten)//2)
    z_werte.sort()

    if mitte != len(Bodendaten)/2:      # Die Liste hat eine ungerade länge
        z_median = z_werte[mitte]
    else:
        z_median = z_werte[mitte-1]

        # -1, da mitte immer der obere Wert vom Median ist, z.B. 6//2 = 3 => 2. und 3. Index einer 6 einträge langen Liste müssen benutzt werden

    for punkt in Bodendaten:
        if punkt.z == z_median:
            return punkt

# Einlesen der Testdaten================================================================================================

#Testdaten_txt = open("Test_DHM.txt","r")
Testdaten_txt = open("Tweelbäke_Messwerte.txt","r")

Datenzeile = Testdaten_txt.readline().replace("\n","").split("\t")

laenge = 0

TINpunkte = []

Messpunkte = []

while Datenzeile != ['']:

    Messpunkt = Messgebiet.Bodenpunkt(float(Datenzeile[0]),float(Datenzeile[1]),float(Datenzeile[2]))
    punkt_in_liste = [float(Datenzeile[0]),float(Datenzeile[1]),float(Datenzeile[2])]


    if len(Messpunkte)>=100:
        Bodenpunkt = Bodenpunktberechnung(Messpunkte)
        TINpunkte.append(Bodenpunkt)
        laenge += 1
        Messpunkte=[]

    Messpunkte.append(Messpunkt)

    Datenzeile = Testdaten_txt.readline().replace("\n", "").split("\t")



Punktliste_array = np.zeros(shape=(laenge,3))

i=0
for punkt in TINpunkte:
    punkt_in_liste = [punkt.x, punkt.y, punkt.z]
    Punktliste_array[i] = punkt_in_liste
    Datenzeile = Testdaten_txt.readline().replace("\n", "").split("\t")
    i+=1

# Test des Packages "trimesh"==================================================================================================



#cloud = trimesh.points.PointCloud(vertices = Punktliste)

# TEST des Packages "scipy"===============================================================================================

"""
mesh = scipy.spatial.Delaunay(Punktliste_array[:-1])

indices = mesh.simplices

vertices = Punktliste_array[indices]

cloud = trimesh.Trimesh(vertices = Punktliste_array, faces=indices)
cloud.show()
"""

# Test pyvista ==========================================================================================================

cloud = pv.PolyData(Punktliste_array)
mesh = cloud.delaunay_2d()
faces = mesh.faces
print(faces)
mesh.plot(show_edges=True)

#https://docs.pyvista.org/examples/00-load/create-tri-surface.html

print("test")
#indices = hull.simplices
#vertices = Punktliste[indices]