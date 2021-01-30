import numpy
import time

t = time.time()
punkte = [numpy.array([1.0,2,3,4,5,6,7,8,9,10]), numpy.array([1.0,2,3,4,5,6,7,8,9,10]), numpy.array([1.1,1.9,3,4.1,5.2,5.8,7.05,7.8,8.8,9.6])]

n_pkt = int(len(punkte[0]))  # Anzahl Punkte
p1 = numpy.array([punkte[0][0], punkte[1][0], punkte[2][0]])
p2 = numpy.array([punkte[0][-1], punkte[1][-1], punkte[2][-1]])
r0 = p2 - p1
d12 = numpy.linalg.norm(r0)
r0 = r0 / d12 # Richtungsvektor
st0 = p1 - numpy.dot(r0, p1) * r0 # Stützvektor, senkrecht auf Richtungsvektor
L = []
temp = numpy.matrix(numpy.array([1, 0, 0] * n_pkt)).getT()  # Erste Spalte der A-Matrix
A = temp  # A-Matrix ist folgendermaßen aufgebaut: Unbekannte in Spalten: erst 3 Komp. des Stützvektors, dann alle lambdas
#   je Punkt und zuletzt 3 Komp. des Richtungsvektors (immer die Ableitungen nach diesen)
#   in den Zeilen sind die Beobachtungen je die Komponenten der Punkte
A = numpy.hstack((A, numpy.roll(temp, 1, 0)))
A = numpy.hstack((A, numpy.roll(temp, 2, 0)))  # bis hierher sind die ersten 3 Spalten angelegt
A_spalte_r0 = numpy.matrix(numpy.array([0.0] * n_pkt * 3))  # Spalte mit Lambdas (Abl. nach r0)
A_spalte_lamb = numpy.hstack((numpy.matrix(r0), numpy.matrix(
    numpy.array([0] * 3 * (n_pkt - 1))))).getT()  # Spalte mit Komp. von r0 (Ableitungen nach den Lambdas)
lambdas = []
for i in range(n_pkt):
    p = []  # gerade ausgelesener Punkt
    for j in range(3):
        p.append(punkte[j][i])
    L += p
    p = numpy.array(p)
    lamb = numpy.dot(r0, (p - st0)) / d12
    lambdas.append(lamb)
    A_spalte_r0[0, i * 3] = lamb
    # x0 = numpy.append(x0, lamb)
    A = numpy.hstack((A, numpy.roll(A_spalte_lamb, 3 * i, 0)))
A_spalte_r0 = A_spalte_r0.getT()
A = numpy.hstack((A, A_spalte_r0))
A = numpy.hstack((A, numpy.roll(A_spalte_r0, 1, 0)))
A = numpy.hstack((A, numpy.roll(A_spalte_r0, 2, 0)))

# Kürzung der Beobachtungen
l = numpy.array([])
for i in range(n_pkt):
    pkt0 = st0 + lambdas[i] * r0
    pkt = L[3 * i:3 * (i + 1)]
    beob = numpy.array(pkt) - pkt0
    l = numpy.hstack((l, beob))

# Einführung von Bedingungen an Stütz- und Richtungsvektor (Stütz senkrecht auf Richtung und Betrag von Richtung = 1)
A_trans = A.getT()
N = A_trans.dot(A)
# Bedingungen an die N-Matrix anfügen
A_bed_1 = numpy.matrix(
    numpy.hstack((numpy.hstack((r0, numpy.zeros((1, n_pkt))[0])), st0)))  # st skalarpro r = 0
A_bed_2 = numpy.matrix(numpy.hstack((numpy.zeros((1, n_pkt + 3))[0], 2 * r0)))  # r0 = 1
N = numpy.hstack((N, A_bed_1.getT()))
N = numpy.hstack((N, A_bed_2.getT()))
A_bed_1 = numpy.hstack((A_bed_1, numpy.matrix(numpy.array([0, 0]))))
A_bed_2 = numpy.hstack((A_bed_2, numpy.matrix(numpy.array([0, 0]))))
N = numpy.vstack((N, A_bed_1))
N = numpy.vstack((N, A_bed_2))
# Anfügen der Widersprüche
w_senkrecht = 0 - numpy.dot(r0, st0)
w_betrag_r = 1 - (r0[0] ** 2 + r0[1] ** 2 + r0[2] ** 2)
n = A_trans.dot(l)
n = numpy.hstack((n, numpy.array([[w_senkrecht, w_betrag_r]])))

# Auswertung
x0 = numpy.matrix(numpy.hstack((numpy.hstack((st0, numpy.array(lambdas))), r0))).getT()
q = N.getI()
x_dach = numpy.matrix(q.dot(n.getT()))
x_dach = x_dach[0:len(x_dach) - 2, 0]
X_dach = x0 + x_dach
r = numpy.array([X_dach[len(X_dach) - 3, 0], X_dach[len(X_dach) - 2, 0], X_dach[len(X_dach) - 1, 0]])

# "Standardabweichung": Mittlerer Abstand der Punkte von der Geraden, aber nur in z-Richtung!
v = []
n_u = len(punkte[0][0]) - len(lambdas)
for i, lamb in enumerate(lambdas):
    z_ist = punkte[2][i]
    z_ausgl = X_dach[2, 0] + lamb * r0[2]
    v.append(z_ist - z_ausgl)
v = numpy.array(v)
s0 = numpy.linalg.norm(v) / n_u

r[2] = 0
max_steigung = r  # Vektor
print(time.time()-t)
print(r)