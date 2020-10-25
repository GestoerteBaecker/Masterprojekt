# Skript zum Auslesen von Daten aller verbundenen Sensoren
# und einspeisen in eine Datenbank

# hier wird Multithreading benutzt: bei sehr zeitintensiven Berechnungen und gleichzeitiger Nutzung eines gemeinsamen Arbeitsspeichers
# (Variablenscope) sollte Multithreading dem Multiprocessing vorgezogen werden (Multiprocessing hat getrennte Arbeitsspeicherbereiche
# und ist eher für CPU-intensive Berechnungen wichtig, da das Programm auch physisch parallel ausgeführt wird

import asyncio
import pynmea2
import pyodbc
import serial
import threading
import time
import utm


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

    def __init__(self, COM=0, baudrate=0, timeout=0, taktrate=0.2):
        # alle Attribute mit default None werden zu einem späteren Zeitpunkt definiert und nicht in der Initialisierungsmethode
        self.com = COM
        self.baudrate = baudrate
        self.timeout = timeout
        self.taktrate = taktrate # Frequenz der Beobachtung
        try:
            self.ser = serial.Serial(self.com, self.baudrate)
        except:
            self.ser = None #TODO: stetig nach Verbindung checken (vllt Signal zur GUI, ob der Sensor "lebt")
            print("Fehler bei der Verbindung mit der Schnittstelle")
        # gibt an, ob momentan ein Datenstream Daten eines Sensors in self.daten schreibt
        self.datastream = False
        # ID für die Daten-Objekte (für Datenbank)
        self.id = 0
        # ein einziges Daten-Objekt
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
        self.close_datastream()
        self.db_zeiger.close()
        self.db_verb.close()


    # liest die spezifischen Daten jedes Sensor (muss je Sensor implementiert werden)
    # Bei Echolot z.B.: Trennung jeder Datenzeile und Einfügen der Daten in ein Daten-Objekt
    def read_sensor_data(self):
        pass # Implementierung in abgeleiteter Klasse


    # Abbruch des Datenstreams (diese Variable wird innerhalb der entsprechenden Methode getestet)
    def close_datastream(self):
        self.datastream = False
        if not self.listen_process:
            self.listen_process = None


    # liest die Daten parallel in einem gesonderten Prozess, zunächst unendlicher Stream, kann aber über self.close_datastream() abgebrochen werden
    def read_datastream(self, db_daten_einpflegen=True):
        self.datastream = True

        # hier durchgehend (in while True) testen, ob Daten ankommen und in Daten-Objekte organisieren
        def nested_read(self, db_daten_einpflegen=db_daten_einpflegen):
            while self.datastream:
                self.daten = self.read_sensor_data()
                if db_daten_einpflegen:
                    self.push_db()
                time.sleep(self.taktrate)
            else:
                # der Thread muss nicht gekillt werden, wenn seine Target-Funktion terminiert
                # was sie tut, sobald self.datastream_check == False ist
                pass

        self.listen_process = threading.Thread(target=nested_read, args=(self, db_daten_einpflegen), daemon=True)
        self.listen_process.start()


    # Verbindung zur Datenbank herstellen
    #TODO: Argument einfügen, das das Erstellen eines neuen Schemas und Tabelle ermöglicht
    def connect_to_db(self, table="geom", database="geom", server="localhost", uid="root", password="8Bleistift8"):
        self.db_table = table
        self.db_database = database
        self.db_verb = pyodbc.connect("DRIVER={MySQL ODBC 8.0 ANSI Driver}; SERVER=" + server + "; DATABASE=" + database + "; UID=" + uid + ";PASSWORD=" + password + ";")
        self.db_zeiger = self.db_verb.cursor()


    # setzt eine Liste von Daten zusammen, mit denen die Daten-Objekte über Cursor.execute() in die DB enigepflegt werden können
    # WICHTIG: auf den Aufbau der Datenbank achten! Columns id, zeit und vor allem wie daten aufgebaut ist
    def make_db_command(self, datenpaket):
        return str()


    # Daten in die Datenbank schreiben
    def push_db(self):

        def db_hochladen(self):
            db_praefix = "INSERT INTO " + self.db_database + "." + self.db_table
            self.db_zeiger.execute(db_praefix + self.make_db_command(self.daten))
            self.db_zeiger.commit()

        threading.Thread(target=db_hochladen, args=(self, ), daemon=True).start()


class IMU(Sensor):

    id = 0

    def __init__(self, COM=0, baudrate=0, timeout=0, taktrate=0.2):
        super().__init__(COM, baudrate, timeout, taktrate)


class Echolot(Sensor):

    id = 0

    def __init__(self, COM=0, baudrate=19200, timeout=0, taktrate=0.2):
        super().__init__(COM, baudrate, timeout, taktrate)


    # Aufbau der Datenbank (die Felder) muss zwingend folgendermaßen sein: id als Int, zeit als Int, daten als String
    def make_db_command(self, datenpaket):
        db_string_praefix = "(id, zeit, tiefe) VALUES ("
        db_string_daten = [datenpaket.id, datenpaket.zeitstamp, datenpaket.daten]
        db_string_daten = ", ".join(str(x) for x in db_string_daten)
        return db_string_praefix + db_string_daten + ");"


    def read_sensor_data(self):
        eol = b'\r' # Enddefinition einer Zeile
        line = bytearray()
        # lese so viele Zeichen aus dem seriellen Port bis das Zeichen \r gelesen wird
        # und das Gelesene ins bytearray line
        while True:
            c = self.ser.read()
            if c:
                line += c
                if line[-1:] == eol:
                    break
            else:
                break
        tiefe = bytes(line).decode("UTF-8").split()[2]
        db_objekt = Daten(Echolot.id, tiefe, time.time())

        return db_objekt # Datenobjekt mit entsprechenden Einträgen


class GNSS(Sensor):

    id = 0

    def __init__(self, COM=0, baudrate=115200, timeout=0, taktrate=0.2):
        super().__init__(COM, baudrate, timeout, taktrate)


    # je nach Art der NMEA-Nachricht müssen hier unterschiedliche Daten-Objekte gebildet werden
    def read_sensor_data(self):
        nmea = self.ser.readline()
        nmea = nmea.decode("utf-8")
        nmea = pynmea2.parse(nmea)
        # auslesen der GNSS-Daten nur, wenn eine GGA-Nachricht vorliegt
        if nmea.sentencetype == "GGA":
            # die self.daten sind hier erstmal nur die Koordinaten in utm
            koords = utm.fromlatlon(nmea.latitude, nmea.longitude)
            daten = [koords[2]*10**6+koords[0], koords[1]]
            db_objekt = Daten(GNSS.id, daten, time.time())
            return db_objekt  # Datenobjekt mit entsprechenden Einträgen


    # Aufbau der Datenbank (die Felder) muss zwingend folgendermaßen sein: id als Int, zeit als Int, east/north als Float
    def make_db_command(self, datenpaket):
        db_string_praefix = "(id, zeit, east, north) VALUES ("
        db_string_daten = [datenpaket.id, datenpaket.zeitstamp, *(datenpaket.daten)]
        db_string_daten = ", ".join(str(x) for x in db_string_daten)
        return db_string_praefix + db_string_daten + ");"


class Distanzmesser(Sensor):

    id = 0

    def __init__(self, COM=0, baudrate=0, timeout=0, taktrate=0.2):
        super().__init__(COM, baudrate, timeout, taktrate)


"""
class Pixhawk(Sensor):

    id = 0

    def __init__(self, COM=0, baudrate=0, timeout=0):
        super().__init__(COM, baudrate, timeout)
"""