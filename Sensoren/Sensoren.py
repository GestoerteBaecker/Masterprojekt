# Skript zum Auslesen von Daten aller verbundenen Sensoren
# und einspeisen in eine Datenbank

import asyncio
import dronekit
import pynmea
import pyodbc
import serial
import time


# Rohdaten der einzelnen Sensoren
# je nach Sensor ist das Attribut self.daten eine Tiefe, ein Punkt oder sonstiges!!!
class Daten:
    def __init__(self, id, daten, timestamp=time.time()):
        # je nach zugeordnetem Sensor
        self.id = id
        self.daten = daten
        #self.sensor = sensor
        self.timestamp = timestamp


class Sensor:

    def __init__(self, COM=0, baudrate=0, timeout=0):
        # alle Attribute mit default None werden zu einem späteren Zeitpunkt definiert und nicht in der Initialisierungsmethode
        self.com = COM
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = serial.Serial(self.com, self.baudrate)
        # ID für die Daten-Objekte (für Datenbank)
        self.id = 0
        # hier werden die ausgelesenen Daten zwischengespeichert (Liste von Daten-Objekten)
        self.daten = None
        self.db_zeiger = None
        self.db_table = None
        self.db_database = None


    # herstellen der Verbindung
    @staticmethod
    def connect(COM=0, baudrate=0, timeout=0):
        sensor = Sensor(COM, baudrate, timeout)
        return sensor


    # schließen der Verbindung
    def kill(self):
        self.ser.close()


    # Daten auslesen
    async def read(self):
        # hier durchgehend (in while True) testen, ob Daten ankommen und in Daten-Objekte organisieren?
        # https://stackoverflow.com/questions/1092531/event-system-in-python
        pass


    # Verbindung zur Datenbank herstellen
    def connect_to_db(self, table="geom", database="geom", server="localhost", uid="root", password="8Bleistift8"):
        self.db_table = table
        self.db_database = database
        verb = pyodbc.connect("DRIVER={MySQL ODBC 8.0 ANSI Driver}; SERVER=" + server + "; DATABASE=" + database + "; UID=" + uid + ";PASSWORD=" + password + ";")
        self.db_zeiger = verb.cursor()


    # Daten in die Datenbank schreiben
    # Aufbau der Datenbank (die Felder) muss zwingend folgendermaßen sein: id als Int, zeit als Int, daten als String
    async def push_db(self):
        async for komp in self.daten:
            db_string = "INSERT INTO " + self.db_database + "." + self.db_table + "(id, zeit, daten) VALUES (" + str(komp.id) + ", " + str(komp.timestamp) + ", " + str(komp.daten) + ");"
            self.zeiger.execute(db_string)
        self.daten = []


"""
class IMU(Sensor):

    def __init__(self):
        super().__init__()


class Echolot(Sensor):

    def __init__(self):
        super().__init__()


class GNSS(Sensor):

    def __init__(self):
        super().__init__()


class Pixhawk(Sensor):

    def __init__(self):
        super().__init__()


class Distanzmesser(Sensor):

    def __init__(self):
        super().__init__()
"""


if __name__ == '__main__':
