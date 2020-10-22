import threading
import random
import time
import multiprocessing


b = 10000
def worker():
    while True:
        global b
        b = random.random()


class A:

    global b

    def __init__(self):
        self.datastream_check = False

    def close(self):
        self.datastream_check = False

    def nested_read(self):
        while self.datastream_check:
            print(b)
        else:
            self.listen_process.kill()
            self.listen_process.join()
            self.listen_process = None

    def read_datastream(self):
        self.datastream_check = True


        self.listen_process = threading.Thread(target=self.nested_read)
        self.listen_process.start()


if __name__ == '__main__':
    datastream = threading.Thread(target=worker)
    datastream.start()

    a = A()
    a.read_datastream()

    time.sleep(10)
    a.close()
    # worker()
    # print(b)

"""
import threading
import time

def infiniteloop1():
    while True:
        print('Loop 1')
        time.sleep(1)

def infiniteloop2():
    while True:
        print('Loop 2')
        time.sleep(1)

thread1 = threading.Thread(target=infiniteloop1)
thread1.start()

thread2 = threading.Thread(target=infiniteloop2)
thread2.start()
"""






