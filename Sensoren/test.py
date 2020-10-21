class A:

    c = 0

    def __init__(self):
        pass


class B:

    def __init__(self):
        self.id = A.c
        A.c += 1


class C:

    def __init__(self):
        self.id = A.c
        A.c += 1


for i in range(20):
    obj = B()

objekte = []
for i in range(20):
    obj = C()
    objekte.append(obj)

print(objekte[15].id)