# Skript zum Auslesen von Daten aller verbundenen Sensoren
# und einspeisen in eine Datenbank

import asyncio
import dronekit
import mavsdk
import pymavlink
import pynmea
import serial

class Sensor:

    def __init__(self, COM=0, baudrate=0, timeout=0):
        self.com = COM
        self.baudrate = baudrate
        self.timeout = timeout

    # herstellen der Verbindung
    @staticmethod
    def connect(COM=0, baudrate=0, timeout=0):
        sensor = Sensor(COM, baudrate, timeout)
        return sensor


    # schließen der Verbindung
    def kill(self):
        pass


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

