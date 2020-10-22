import threading
import random
from multiprocessing import Process, Pipe
import time
import threading

def worker(conn):
    while True:
        b = random.random()
        print('SEND: ',b)
        conn.send(b)
        time.sleep(1)

class A:

    def __init__(self):
        self.datastream_check = False
        self.listen_process = None

    def close(self):
        self.datastream_check = False

    def nested_read(self,conn):
        while self.datastream_check:
            print("datenstream im Objekt mit der schleife:", self.datastream_check)
            print("objektname im while prozess:", self)
            print('REC: ',conn.recv())
            time.sleep(1)
        else:
            print("ich gehe nochmal in die while schelife")
            self.listen_process.kill()
            self.listen_process.join()
            self.listen_process = None


    def read_datastream(self):
        self.datastream_check = True
        self.listen_process = Process(target=self.nested_read, args=(parent_conn,)) #, args=(parent_conn,))   target=self.nested_read(parent_conn,))
        self.listen_process.start()


if __name__ == '__main__':

    parent_conn, child_conn=Pipe()
    datastream = Process(target=worker,args=(child_conn,))
    datastream.start()

    print("erreichbar")

    a = A()
    #t = threading.Timer(10, a.close)
    #t.start()
    a.read_datastream()

    print("nicht erreichbar")

    print(a.datastream_check)
    time.sleep(10)
    a.close() #TODO: das Attribut self.datastream in a wird nicht verändert!!! warum? (das objekt im hauptthread nicht mit dem objekt im while prozess übereinstimmt
    print(a.datastream_check)
    print("objektname im hauptprozess", a)
    # worker()
    # print(b)


# https://stackoverflow.com/questions/17553543/pyserial-non-blocking-read-loop

# https://stackoverflow.com/questions/26047544/python-serial-port-listener

# https://stackoverflow.com/questions/911089/python-monitoring-over-serial-port



