import numpy
import time
import Messgebiet

"""
t = time.time()
start_punkt = Messgebiet.Bodenpunkt(0,0,0)
profil = Messgebiet.Profil(50, start_punkt, True, 0, 100, 0, 50)

for pkt in range(10):
    if pkt < 5:
        z = 10*pkt
    else:
        z = 0
    punkt = Messgebiet.Bodenpunkt(10*pkt, 10*pkt, z)
    profil.MedianPunktEinfuegen(punkt)

profil.ProfilAbschliessen()
topo = profil.topographisch_bedeutsame_punkte
for pkt in topo:
    print(pkt)
print(time.time()-t)
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
