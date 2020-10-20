# Skript zum Auslesen von Daten aller verbundenen Sensoren
# und einspeisen in eine Datenbank

import asyncio
import dronekit
import mavsdk
import pymavlink
import pynmea
import serial
import time


# Zeitpunkt der Messung
class Daten:
    def __init__(self, daten, timestamp=time.time()):
        self.daten = daten
        self.timestamp = timestamp


class Sensor:

    def __init__(self, COM=0, baudrate=0, timeout=0):
        self.com = COM
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = serial.Serial(self.com, self.baudrate)



    # herstellen der Verbindung
    @staticmethod
    def connect(COM=0, baudrate=0, timeout=0):
        sensor = Sensor(COM, baudrate, timeout)
        return sensor


    # schließen der Verbindung
    def kill(self):
        self.ser.close()


    # Daten auslesen
    def read(self):
        pass


    # Daten in die Datenbank schreiben
    def push_db(self):
        pass


    # Verbindung zur Datenbank herstellen
    def connect_db(self):
        pass


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

