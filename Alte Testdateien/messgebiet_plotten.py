import matplotlib.pyplot as plt
import csv
import Masterprojekt.Messprogramm.Messgebiet as Messgebiet

Testdaten_txt = open("Test_DHM.txt","r")
Datenzeile = Testdaten_txt.readline().replace("\n","").split(";")
laenge = 0
TINpunkte = []
Messpunkte = []

while Datenzeile != ['']:
    print(Datenzeile)
    Messpunkt = Messgebiet.Punkt(float(Datenzeile[1]),float(Datenzeile[2]))
    Messpunkte.append(Messpunkt)
    Datenzeile = Testdaten_txt.readline().split(";")

# EINLESEN DES TEST POLYGONS
testdaten_path = open("Testdaten_Polygon.txt", "r")
lines = csv.reader(testdaten_path, delimiter=";")
polygonpunkte = []

# Lesen der Datei
for line in lines:
    polygonpunkt = Messgebiet.Punkt(float(line[0]),float(line[1]))
    polygonpunkte.append(polygonpunkt)

testdaten_path.close()

xp = []
yp = []
#Messpunkte plotten
fig, ax = plt.subplots()
plt.grid(True)
for punkt in Messpunkte:
    xp.append(punkt.x)
    yp.append(punkt.y)
plt.scatter(xp,yp)
#Polygon plotten

xl = []
yl = []
for i, punkt in enumerate(polygonpunkte):

    x1, y1 = punkt.x, punkt.y
    x2, y2 = polygonpunkte[i-1].x, polygonpunkte[i-1].y
    xl.append(x1)
    xl.append(x2)
    yl.append(y1)
    yl.append(y2)
    ax.plot([x1, x2],[y1,y2], '-r')


plt.ioff()
plt.show()
print("debug")