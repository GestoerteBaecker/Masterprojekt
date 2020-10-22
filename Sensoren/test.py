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
<<<<<<< HEAD
        self.listen_process = Process(target=self.nested_read(parent_conn,))
=======


        self.listen_process = multiprocessing.Process(target=self.nested_read)
>>>>>>> 00aed82... versuch multiprocessing - gescheitert
        self.listen_process.start()


if __name__ == '__main__':
<<<<<<< HEAD
    parent_conn, child_conn=Pipe()
    datastream = Process(target=worker,args=(child_conn,))
=======
    datastream = multiprocessing.Process(target=worker)
>>>>>>> 00aed82... versuch multiprocessing - gescheitert
    datastream.start()
    a = A()
    a.read_datastream()

    time.sleep(10)
    a.close()
    # worker()
    # print(b)







