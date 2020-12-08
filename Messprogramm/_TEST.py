import numpy
import time
import Messgebiet
import csv
import Simulation
import threading
import copy
import itertools

class P:
    def __init__(self, a, b):
        self.a = a
        self.b = b


    def __add__(self, p2):
        return P(self.a+p2.a, self.b+p2.b)

b = ["a", "b", "c", "d"]

def test(menge, anzahl):
    aussen_ausgabe = []
    def nested(index=0, ausgabe=None, einfügen=None):
        if not ausgabe:
            ausgabe = []
        if not einfügen:
            einfügen = []
        if index == anzahl:
            aussen_ausgabe.append(einfügen)
            einfügen = []
        else:
            for el in menge:
                einfügen = [el] + einfügen
                nested(index+1, ausgabe, einfügen)
    nested()
    return aussen_ausgabe

#print(test(b, 3))

liste = []
for i in range(3):
    liste.append(b)

liste_neu = []
for produkt in itertools.product(*liste):
    einzig = True
    for ele in produkt:
        einzig = einzig and produkt.count(ele) == 1
    if einzig:
        liste_neu.append(produkt)

print(liste_neu)


"""
t = time.time()
profil = Messgebiet.Profil(50, Messgebiet.Bodenpunkt(451880, 5884978, 0), stuetz_ist_start=True, start_lambda=0, end_lambda=None, grzw_dichte_topo_pkt=0.1, grzw_neigungen=50)
end_punkt = Messgebiet.Bodenpunkt(451943.3846900004, 5885041.384689885,0)

# nachbilden der Methode sternbfahren aus boot
# median punkte einfügen
median_punkte = []
testdaten = open("Test_Medianpunkte.txt")
lines = csv.reader(testdaten, delimiter=";")

# Lesen der Datei
for line in lines:
    punkt = Messgebiet.Bodenpunkt(float(line[0]), float(line[1]), float(line[2]))
    median_punkte.append(punkt)
testdaten.close()

for punkt in median_punkte:
    profil.MedianPunktEinfuegen(punkt)

profil.ProfilAbschliessenUndTopoPunkteFinden(end_punkt)

print("Länge median punkte", len(median_punkte), "länge topo punkte", len(profil.topographisch_bedeutsame_punkte))
"""
"""
boot = Simulation.Boot_Simulation()
boot.auslesen = True
time.sleep(0.3)
boot.Datenaktualisierung()
time.sleep(0.3)
boot.Erkunden()

while not boot.stern_beendet:
    time.sleep(0.1)
print("Fertig gemessen")
"""




"""
import shapely.geometry as shp

#ring = shp.LinearRing([(0,0), (200,0), (200,200), (0,200)])

#line = shp.LineString([(10,100), (2000,100)])

ring = shp.LinearRing([(451913.7237857745, 5885059.348336109), (451956.6619978332, 5885033.343503454), (452029.838387398, 5884991.614818496), (452066.7289639555, 5884974.076675542), (452067.3337275056, 5884957.143296138), (452018.9526434958, 5884868.243054271), (451990.52875664, 5884855.543019718), (451974.2001407868, 5884828.328659963), (451979.0382491877, 5884802.928590857), (451887.7189531192, 5884859.171601019), (451933.0762193784, 5884919.043192481), (451853.2474307623, 5884983.148128794), (451860.5045933637, 5885001.291035297), (451920.3761848258, 5885036.972084755), (451913.7237857745, 5885059.348336109)])
line = shp.LineString([(451988.6982560926, 5885007.317037198), (451281.5914749061, 5884300.210256011)])


schnitt = ring.intersection(line)

print(schnitt)

if type(schnitt).__name__ == "MultiPoint":
    schnitt = [numpy.array([pkt.x, pkt.y]) for pkt in schnitt]
else:
    schnitt = [numpy.array([schnitt.x, schnitt.y])]

print(schnitt)

"""




"""



class A:
    def __init__(self):
        self.a = 0
        time.sleep(0.1)

        def plus(self, liste, index=0):
            while True:
                self.a = liste[index]
                index += 1
                print("self.a", self.a, "thread:", threading.get_ident())
                time.sleep(0.1)
        threading.Thread(target=plus, args=(self, ["Element Nr. " + str(i) for i in list(range(10000))], 0), daemon=True).start()


    #def test(self):
        #while True:
            #print(self.a)
            #time.sleep(0.1)

    def verändern(self):
        def intern(self):
            while True:
                print("Einmal self.a", self.a, "thread:", threading.get_ident())
                time.sleep(0.1)
                print("Nochmal self.a", self.a, "thread:", threading.get_ident())
                time.sleep(0.4)
        threading.Thread(target=intern, args=(self, ), daemon=True).start()

a = A()
a.verändern()
#a.test()
while True:
    pass

"""




#

"""
class A:
    i = 0
    def __init__(self):
        self.id = A.i
        A.i+= 1
        self.liste = []
        self.akt = False

    def neu(self):
        a = A()
        self.liste.append(a)

    def aktuell(self):
        if self.akt:
            return self.id
        liste = []
        def rek(self):
            for a in self.liste:
                if a.akt:
                    liste.append(a.id)
                rek(a)
        rek(self)
        return liste

a = A()
a.neu()
a.neu()
a.liste[0].neu()
a.liste[1].akt = True
a.liste[0].liste[0].akt = True
print(a.aktuell())
i = 0
"""

"""
def check_with_list(dd, check_value, other_value=None):

    for index, h in enumerate(dd):
        if isinstance(h, list):
            result = check_with_list(h, check_value)

            if result is not None:
                if other_value:
                    new = (index,) + result
                    if len(new) == 2:

                        if dd[new[0]][0] == other_value:
                            result = None
                        else:
                            return (index,) + result


        elif h == check_value:
            return (index,)
    # value not found
    return None

dd = [
    "gcc",
    "fcc",
    ["scc", "jhh", "rrr"],
    ["www", "rrr", "rrr"],
    "mmm",
    ["qwe", ["ree", "rrr", "rrr"], "ere"]
]
dd = check_with_list(dd, "rrr", "ree")
print(check_with_list(dd, "rrr", "ree"))
"""


# hier weiter gucken https://stackoverflow.com/questions/58389370/getting-all-recursion-results-in-a-list
