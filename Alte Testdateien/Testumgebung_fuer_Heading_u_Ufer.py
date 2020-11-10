import numpy

def Uferpunktberechnung(x1,y1,s,offset,heading):
    strecke = s+offset

    e = x1 + numpy.sin((heading / (200 / numpy.pi))) * strecke
    n = y1 + numpy.cos((heading / (200 / numpy.pi))) * strecke

    return (e, n)


def Headingberechnung(x1, y1, x2, y2):
    Bootsmitte = [x1,y1]
    Bootsbug = [x2,y2]

    # Heading wird geodätisch (vom Norden aus im Uhrzeigersinn) berechnet und in GON angegeben
    heading_rad = numpy.arctan((Bootsmitte[0] - Bootsbug[0])/ (Bootsmitte[1] - Bootsbug[1]))

    # Quadrantenabfrage

    if Bootsbug[0] > Bootsmitte[0]:
        if Bootsbug[1] > Bootsmitte[1]:
            q_zuschl = 0  # Quadrant 1
        else:
            q_zuschl = 2 * numpy.pi  # Quadrant 4
    else:
        if Bootsbug[1] > Bootsmitte[1]:
            q_zuschl = numpy.pi  # Quadrant 2
        else:
            q_zuschl = numpy.pi  # Quadrant 3

    heading_rad += q_zuschl
    heading_gon = heading_rad * (200 / numpy.pi)

    return heading_gon

x1 = 0
y1 = 0
x2 = 1
y2 = -1

s = 50
offset = 0.5

heading = Headingberechnung(x1,y1,x2,y2)
print(heading)

uferpunkt = Uferpunktberechnung(x1,y1,s, offset, heading)
print(uferpunkt)