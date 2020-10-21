# Skript zum Auslesen von Daten aller verbundenen Sensoren
# und einspeisen in eine Datenbank

import asyncio
import dronekit
import multiprocessing
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
        # gibt an, ob momentan ein Datenstream Daten eines Sensors in self.daten schreibt
        self.datastream = False
        # ID für die Daten-Objekte (für Datenbank)
        self.id = 0
        # hier werden die ausgelesenen Daten zwischengespeichert (Liste von Daten-Objekten)
        self.daten = None
        self.db_verb = None
        self.db_zeiger = None
        self.db_table = None
        self.db_database = None
        self.listen_process = None


    # herstellen der Verbindung
    @staticmethod
    def connect(COM=0, baudrate=0, timeout=0):
        sensor = Sensor(COM, baudrate, timeout)
        return sensor


    # schließen der Verbindung
    def kill(self):
        self.ser.close()
        self.abort_datastream()
        self.db_zeiger.close()
        self.db_verb.close()


    # liest die spezifischen Daten jedes Sensor (muss je Sensor implementiert werden)
    # Bei Echolot z.B.: Trennung jeder Datenzeile und Einfügen der Daten in eine Daten-Objekt
    def read_sensor_data(self):
        self.daten = None
        # TODO


    # Abbruch des Datenstreams (diese Variable wird innerhalb der entsprechenden Methode getestet)
    def close_datastream(self):
        self.datastream = False
        if not self.listen_process:
            self.listen_process.close() # TODO: geht das schließen von prozessen so?
            self.listen_process = None


    # liest die Daten parallel in einem gesonderten Prozess
    def read_infinite_datastream(self, db_daten_einpflegen=True):
        self.datastream = True
        # hier durchgehend (in while True) testen, ob Daten ankommen und in Daten-Objekte organisieren?
        # https://stackoverflow.com/questions/1092531/event-system-in-python
        # vllt in echtem multiproessing auslagern. innerhalb dieser methode multiprocessing starten
        #   kann über Methode stop_reading() gestoppt werden (sollte auch bei kill und beim Destruktor ausgelöst werden)!!
        # Vorgehen: read()-Methode ist eine decorated Methode, die in der außerhalb liegenden Funktion (die dekorierte normale außerhalb liegende @-Funktion) im Multithreading aufgerufen wird
        # oder die im Multithreading aufgerufene Funktion (die das eigentliche lesen des Sensors übernimmt) wird als nestes Funktion definiert (der Prozess, in der diese nestedFunktion gegeben wird)
        # wird als self.-Attribut gespeichert und kann demnach manipuliert werden (wie oben beschrieben in kill und del)
        def nested_read(datenstream=self.datastream, db_daten_einpflegen=db_daten_einpflegen):
            while datenstream:
                # self.read_sensor_data()...
                pass
            else:
                # kill process(self.read_sensor_data())...
                pass
            pass
        self.listen_process = multiprocessing.Process(target=nested_read)
        self.listen_process.start()


    # Verbindung zur Datenbank herstellen
    def connect_to_db(self, table="geom", database="geom", server="localhost", uid="root", password="8Bleistift8"):
        self.db_table = table
        self.db_database = database
        self.db_verb = pyodbc.connect("DRIVER={MySQL ODBC 8.0 ANSI Driver}; SERVER=" + server + "; DATABASE=" + database + "; UID=" + uid + ";PASSWORD=" + password + ";")
        self.db_zeiger = self.db_verb.cursor()


    # Daten in die Datenbank schreiben
    # Aufbau der Datenbank (die Felder) muss zwingend folgendermaßen sein: id als Int, zeit als Int, daten als String
    async def push_db(self):
        db_praefix = "INSERT INTO " + self.db_database + "." + self.db_table + "(id, zeit, daten) VALUES ("
        async for komp in self.daten:
            db_string = db_praefix + str(komp.id) + ", " + str(komp.timestamp) + ", " + str(komp.daten) + ");"
            self.db_zeiger.execute(db_string)
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
