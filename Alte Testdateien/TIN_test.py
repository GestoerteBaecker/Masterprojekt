import Messprogramm.Messgebiet as Messgebiet
#import tinned_python
import trimesh
import open3d as o3d
import numpy as np
import scipy
import matplotlib.pyplot as plt
import matplotlib.tri as tri
import pyvista as pv


# Einlesen der Testdaten================================================================================================

#Testdaten_txt = open("Test_DHM.txt","r")
Testdaten_txt = open("Test_Pyramide.txt","r")

Datenzeile = Testdaten_txt.readline().replace("\n","").split(";")

laenge = 0

TINpunkte = []


while Datenzeile != ['']:

    Bodenpunkt = Messgebiet.Bodenpunkt(float(Datenzeile[1]),float(Datenzeile[2]),float(Datenzeile[3]))
    punkt_in_liste = [float(Datenzeile[1]),float(Datenzeile[2]),float(Datenzeile[3])]

    TINpunkte.append(Bodenpunkt)
    #Punktliste_arry.insert(punkt_in_liste)

    Datenzeile = Testdaten_txt.readline().replace("\n", "").split(";")
    laenge += 1

#Testdaten_txt = open("Test_DHM.txt","r")
Testdaten_txt = open("Test_Pyramide.txt","r")

Datenzeile = Testdaten_txt.readline().replace("\n","").split(";")
Punktliste_array = np.zeros(shape=(laenge,3))

i=0
while Datenzeile != ['']:
    punkt_in_liste = [float(Datenzeile[1]), float(Datenzeile[2]), float(Datenzeile[3])]
    Punktliste_array[i] = punkt_in_liste
    Datenzeile = Testdaten_txt.readline().replace("\n", "").split(";")
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