import numpy
import time
import Messgebiet
import csv
import Simulation
import threading

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


punkte = [(451883.98551094846, 5884981.985510948, 9.215142857142858), (451891.37799093366, 5884989.377990934, 9.879888888888889), (451895.1385133609, 5884993.138513361, 10.07819512195122), (451906.2915157732, 5885004.291515773, 10.56675652173913), (451908.86281315924, 5885006.862813158, 10.734396825396825), (451913.21794810705, 5885011.217948107, 10.901036496350365), (451920.44972200564, 5885018.449722007, 11.25882389937107), (451894.698527482, 5885007.643794224, 11.987067307692309), (451914.81210764963, 5885007.596248378, 12.021901960784314), (451924.69844366424, 5885007.572878389, 12.134158730158731), (451939.3120391986, 5885007.538333778, 12.364506082725061), (451944.6074789489, 5885007.52581606, 12.43043705463183), (451954.15290682507, 5885007.503251929, 12.60415124153499), (451959.2210744831, 5885007.491271453, 12.705878854625551), (451963.8119707474, 5885007.4804191785, 12.801140086206896), (451973.78921559895, 5885007.456834293, 13.034045174537988), (451909.46409628395, 5885003.265713274, 13.827440287769784), (451912.81704153493, 5884999.901154142, 13.815791784702549), (451919.66731723904, 5884993.02715056, 13.822513067400275), (451940.9240275621, 5884971.696811573, 13.930044136191677), (451951.27163371927, 5884961.313363538, 13.963370460048425), (451954.9293921748, 5884957.642935396, 13.99552090800478), (451958.36255142704, 5884954.19788442, 14.041485849056604), (451962.1646950848, 5884950.382570955, 14.084230500582072), (451965.53368313605, 5884947.001913457, 14.126347126436782), (451972.60855804343, 5884939.902532707, 14.205677491601344), (451983.02033540164, 5884929.454691196, 14.27903027027027), (451993.23959915695, 5884919.200030114, 14.275506263048017), (451999.9454896589, 5884912.470911851, 14.239719101123596), (452003.4588629123, 5884908.94536903, 14.199760606060606), (452006.58720895986, 5884905.806187067, 14.147770229770229), (451911.28012288007, 5885008.637530606, 13.953760744985674), (451911.26441664563, 5885003.705737432, 13.945229566453447), (451911.24863803224, 5884998.751217104, 13.93861028893587), (451911.2184560057, 5884989.273992437, 13.937841666666667), (451911.17256774474, 5884974.864974598, 13.951264765784114), (451911.14006959146, 5884964.66048089, 13.969739799331103)]
punkte = [Messgebiet.Punkt(pkt[0], pkt[1], pkt[2]) for pkt in punkte]
tin = Messgebiet.TIN(punkte)
tin.plot()


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
