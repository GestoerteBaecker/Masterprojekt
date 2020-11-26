import numpy
import time
import Messgebiet
import csv

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
