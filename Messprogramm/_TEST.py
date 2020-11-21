import numpy
import time


def abstand_punkt_gerade(richtung, stuetz, punkt):
    if richtung.shape[0] == 2: # falls die Vektoren 2D sind
        richtung = numpy.array([richtung[1], -richtung[0]])
    else: # falls die Vektoren 3D sind
        #richtung = numpy.cross(richtung, numpy.cross(punkt, richtung))
        richtung = punkt - numpy.dot(punkt, richtung) * richtung
        richtung = richtung / numpy.linalg.norm(richtung)
    return numpy.dot(richtung, (punkt - stuetz))

stuetz = numpy.array([-2,1,7])
richtung = numpy.array([4,1,-3])
richtung = richtung / numpy.linalg.norm(richtung)
punkt = numpy.array([10,5,7])

t = time.time()
print(t)
print(abstand_punkt_gerade(richtung, stuetz, punkt))
print(time.time()-t)

