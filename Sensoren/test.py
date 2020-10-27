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
        #self.listen_process = None

    def read_datastream(self):

        self.datastream_check = True

        def nested_read(self):
            while self.datastream_check:
                print(b)
                time.sleep(1)
            else:
                # der Thread muss nicht gekillt werden, wenn seine Target-Funktion terminiert
                # was sie tut, sobald self.datastream_check == False ist
                pass

        self.listen_process = threading.Thread(target=nested_read, args=(self,), daemon=True)
        self.listen_process.start()


if __name__ == '__main__':

    threading.Thread(target=worker, daemon=True).start() # da daemon, bricht dieser Thread ab, sobald main terminiert (was er tut, sobald er unten den letzten Befehl ausgeführt hat)

    a = A()
    a.read_datastream()
    time.sleep(10)
    print(a.listen_process.is_alive())
    a.close()
    time.sleep(1)
    print(a.listen_process.is_alive())

# https://stackoverflow.com/questions/9747994/kill-a-daemon-thread-whilst-the-script-is-still-running
# -> im Hauptthread nur alle Kindthreads starten, da nur er OS-Befehle abgreifen (Abbruch durch User und so...), der Hauptthread muss dann warten bis die anderen fertig sind
# https://www.youtube.com/watch?v=KYu4bts4dPI

# andere Möglichkeiten
# https://stackoverflow.com/questions/17553543/pyserial-non-blocking-read-loop

# https://stackoverflow.com/questions/26047544/python-serial-port-listener

# https://stackoverflow.com/questions/911089/python-monitoring-over-serial-port



