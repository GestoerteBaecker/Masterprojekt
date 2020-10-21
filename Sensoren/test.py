import threading
import random


a = 10000
datastream = None
def worker():
    while True:
        global a
        a = random.random()
        #print(a)


class A:

    global datastream

    def __init__(self):
        self.datastream_check = False

    def close(self):
        self.datastream_check = False

    def read_datastream(self):
        self.datastream_check = True

        def nested_read(self):
            while self.datastream_check:
                print(datastream)
            else:
                self.listen_process.kill()
                self.listen_process.join()
                self.listen_process = None
        self.listen_process = threading.Thread(target=nested_read, args=(self, ), daemon=True).start()
        #self.listen_process.start()


if __name__ == '__main__':
    datastream = threading.Thread(target=worker, daemon=True).start()
    #datastream.start()

    a = A()
    a.read_datastream()