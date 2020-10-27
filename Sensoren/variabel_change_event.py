import time


class ObjectHoldingTheValue(object):
    def __init__(self, initial_value=0):
        self._value = initial_value


    def __setattr__(self, key, value):
        try:
            old_var = self._value
        except:
            pass
        super().__setattr__(key, value)
        if key == "_value":
            print(old_var, value)


a = ObjectHoldingTheValue(10)
time.sleep(2)
a._value = 50

# https://stackoverflow.com/questions/12998926/clean-way-to-disable-setattr-until-after-initialization