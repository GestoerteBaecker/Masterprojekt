import threading
import random
from multiprocessing import Process, Pipe
import time

def worker(conn):
    while True:
        b = random.random()
        print('SEND: ',b)
        conn.send(b)
        time.sleep(1)

class A:

    def __init__(self):
        self.datastream_check = False

    def close(self):
        self.datastream_check = False

    def nested_read(self,conn):
        while self.datastream_check:
            print('REC: ',conn.recv())
            time.sleep(1)
        else:
            self.listen_process.kill()
            self.listen_process.join()
            self.listen_process = None


    def read_datastream(self):
        self.datastream_check = True
        self.listen_process = Process(target=self.nested_read(parent_conn,))
        self.listen_process.start()


if __name__ == '__main__':

    parent_conn, child_conn=Pipe()
    datastream = Process(target=worker,args=(child_conn,))
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






