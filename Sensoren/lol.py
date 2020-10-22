class A:
    def test(self):
        print("innerhalb", self)


a = A()

print(a)
a.test()