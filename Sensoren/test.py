import threading
import random
import multiprocessing


b = 10000
datastream = None
def worker():
    while True:
        global b
        b = random.random()



class A:

    global datastream
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


        self.listen_process = multiprocessing.Process(target=self.nested_read)
        self.listen_process.start()


if __name__ == '__main__':
    """
    datastream = multiprocessing.Process(target=worker)
    datastream.start()

    a = A()
    a.read_datastream()"""
    worker()
    #print(b)