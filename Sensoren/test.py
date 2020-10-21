class A:

    c = 0

    def __init__(self):
        pass

    def test(self):
        print(type(self).__name__)


class B(A):

    def __init__(self):
        super().__init__()
        self.id = A.c
        A.c += 1


class C(A):

    def __init__(self):
        super().__init__()
        self.id = A.c
        A.c += 1


for i in range(20):
    obj = B()

objekte = []
for i in range(20):
    obj = C()
    objekte.append(obj)

print(objekte[15].id)
objekte[15].test()