import numpy

def Geradenausgleichung(punkte):

    # Ausgleichsgerade und Gradient auf Kurs projizieren (<- Projektion ist implizit, da die zuletzt aufgenommenen Punkte auf dem Kurs liegen müssten)
    n_pkt = int(len(punkte[0]))  # Anzahl Punkte
    p1 = numpy.array([punkte[0][0], punkte[1][0], punkte[2][0]])
    p2 = numpy.array([punkte[0][1], punkte[1][1], punkte[2][1]])
    r0 = p2 - p1
    d12 = numpy.linalg.norm(r0)
    r0 = r0 / d12
    st0 = p1 - numpy.dot(r0, p1) * r0
    x0 = numpy.concatenate([st0, r0])  # Unbekanntenvektor noch ohne Lambdas
    L = []
    temp = numpy.matrix(numpy.array([1, 0, 0] * n_pkt)).getT()  # Erste Spalte der A-Matrix
    A = temp  # A-Matrix ist folgendermaßen aufgebaut: U in Spalten: erst 3 Komp. des Stützvektors, dann alle lambdas
    #   je Punkt und zuletzt 3 Komp. des Richtungsvektors (immer die Ableitungen nach diesen)
    #   in den Zeilen sind die Beobachtungen je die Komponenten der Punkte
    A = numpy.hstack((A, numpy.roll(temp, 1, 0)))
    A = numpy.hstack((A, numpy.roll(temp, 2, 0)))  # bis hierher sind die ersten 3 Spalten angelegt
    A_spalte_r0 = numpy.matrix(numpy.array([0] * n_pkt * 3))  # Spalte mit Lambdas (Abl. nach r0)
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
        x0 = numpy.append(x0, lamb)
        A = numpy.hstack((A, numpy.roll(A_spalte_lamb, 3 * i, 0)))
    print(A)
    print(A_spalte_r0)
    A_spalte_r0 = A_spalte_r0.getT()
    A = numpy.hstack((A, A_spalte_r0))
    A = numpy.hstack((A, numpy.roll(A_spalte_r0, 1, 0)))
    A = numpy.hstack((A, numpy.roll(A_spalte_r0, 2, 0)))

    # Einführung von Bedingungen an Stütz- und Richtungsvektor (Stütz senkrecht auf Richtung und Betrag von Richtung = 1)
    A_bed_1 = numpy.matrix(
        numpy.hstack((numpy.hstack((r0, numpy.zeros((1, n_pkt))[0])), st0)))  # st skalarpro r = 0
    A_bed_2 = numpy.matrix(numpy.hstack((numpy.zeros((1, n_pkt + 3))[0], 2 * r0)))  # r0 = 1
    A = numpy.vstack((A, numpy.vstack((A_bed_1, A_bed_2))))
    L += [0, 1]

    # Kürzung der Beobachtungen
    l = numpy.array([])
    for i in range(n_pkt):
        pkt0 = st0 + lambdas[i] * r0
        pkt = L[3 * i:3 * (i + 1)]
        beob = numpy.array(pkt) - pkt0
        l = numpy.hstack((l, beob))
    l = numpy.hstack((l, numpy.array([0, 0])))

    # Einführung einer Gewichtsmatrix
    p = numpy.identity(3 * n_pkt + 2)
    p[3 * n_pkt, 3 * n_pkt] = 10000000
    p[3 * n_pkt + 1, 3 * n_pkt + 1] = 10000000

    # Auswertung
    q = (A.getT().dot(A)).getI()
    x_dach = (q.dot(A.getT())).dot(l)
    X_dach = x0 + x_dach
    r = numpy.array(X_dach[0,-3:]).flatten()
    r[2] = 0
    max_steigung = r # Vektor

    return max_steigung

x = numpy.array([0,1,2,3,4])
y = numpy.array([0,0,0,0,0])
z = numpy.array([0.1,0.9,2,3.045,3.95])
punkte = [x, y, z]
print(Geradenausgleichung(punkte))