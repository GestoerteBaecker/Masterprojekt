
import time

class ObjectHoldingTheValue:
    def __init__(self, initial_value=0):
        self._value = initial_value
        self._callbacks = []

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        old_value = self._value
        self._value = new_value
        self._notify_observers(old_value, new_value)

    def _notify_observers(self, old_value, new_value):
        for callback in self._callbacks:
            callback(old_value, new_value)

    def register_callback(self, callback):
        self._callbacks.append(callback)


a = ObjectHoldingTheValue(10)
print(a.x)
time.sleep(10)
a.x = 50
