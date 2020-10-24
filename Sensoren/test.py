import threading
import random
import time

b = 1000

def worker():
    global b
    while True:
        b = random.random()
        time.sleep(0.999)

class A:

    global b

    def __init__(self):
        self.datastream_check = False
        self.listen_process = None

    def close(self):
        self.datastream_check = False
        self.listen_process = None

    def read_datastream(self):

        self.datastream_check = True

        def start_thread(self):
            self.listen_process = threading.Thread(target=nested_read, args=(self, ), daemon=True)
            self.listen_process.start()

        def nested_read(self):
            while self.datastream_check:
                print(b)
                time.sleep(1)
            else:
                # hier muss der Thread vernünftig gekillt werden
                self.listen_process = None

        start_thread(self)


if __name__ == '__main__':

    threading.Thread(target=worker, daemon=True).start()

    a = A()
    a.read_datastream()
    time.sleep(10)
    a.close()

# https://stackoverflow.com/questions/9747994/kill-a-daemon-thread-whilst-the-script-is-still-running
# -> im Hauptthread nur alle Kindthreads starten, da nur er OS-Befehle abgreifen (Abbruch durch User und so...), der Hauptthread muss dann warten bis die anderen fertig sind


# andere Möglichkeiten
# https://stackoverflow.com/questions/17553543/pyserial-non-blocking-read-loop

# https://stackoverflow.com/questions/26047544/python-serial-port-listener

# https://stackoverflow.com/questions/911089/python-monitoring-over-serial-port



