# Skript zum Auslesen von Daten aller verbundenen Sensoren
# und einspeisen in eine Datenbank

# hier wird Multithreading benutzt: bei sehr zeitintensiven Berechnungen und gleichzeitiger Nutzung eines gemeinsamen Arbeitsspeichers
# (Variablenscope) sollte Multithreading dem Multiprocessing vorgezogen werden (Multiprocessing hat getrennte Arbeitsspeicherbereiche
# und ist eher für CPU-intensive Berechnungen wichtig, da das Programm auch physisch parallel ausgeführt wird

import datetime
import pynmea2
import pyodbc
import queue
import random
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

    def __init__(self, COM="COM0", baudrate=0, timeout=0, taktrate=0.2, bytesize=None, parity=None):
        # alle Attribute mit default None werden zu einem späteren Zeitpunkt definiert und nicht in der Initialisierungsmethode
        self.com = COM
        self.Fehlerzaehler_pars = 0
        self.baudrate = baudrate
        self.timeout = timeout
        self.taktrate = taktrate/4 # Frequenz der Beobachtung
        self.bytesize = bytesize
        self.parity = parity
        # sagt aus, ob die Verbindung zum Sensor besteht (ob das serial.Serial()-Objekt besteht
        self.verbindung_hergestellt = False
        try:
            if self.bytesize:
                self.ser = serial.Serial(self.com, timeout=self.timeout, baudrate=self.baudrate, bytesize=self.bytesize, parity=self.parity)
            else:
                self.ser = serial.Serial(self.com, baudrate=self.baudrate, timeout=self.timeout)
            self.verbindung_hergestellt = True
            #TODO: test auf echter Verbindung, ob Daten ausgelesen werden können
            #-> falls nicht, dann in den except Ast
        except:
            self.ser = None
            print("Fehler bei der Verbindung mit der Schnittstelle")
            self.verbindung_suchen()
        # gibt an, ob momentan ein Datenstream Daten eines Sensors in self.daten schreibt
        self.datastream = False
        # gibt an, ob gerade in die DB geschrieben wird
        self.writing_db = False
        # ID für die Daten-Objekte (für Datenbank)
        self.id = 0
        # ein einziges Daten-Objekt
        self.daten = queue.Queue() # ist eine threadsichere Liste; neuer Thread fügt die erst hinzugefügten Daten der DB hinzu
        self.aktdaten = None
        self.db_felder = [("id", "INT"), ("zeitpunkt", "DOUBLE")] # DB-Felddefinition für die EInrichtung einer DB-Tabelle
        self.db_verb = None
        self.db_zeiger = None
        self.db_table = None
        self.db_database = None
        self.listen_process = None
        self.writing_process = None
        self.db_schreiben_wiederaufnehmen = False # diese Variable zeigt an, ob jemals in die DB geschrieben wurde. Bei Verbindungsverlust des Sensors und gesetztem True wird
        # das Schreiben in die DB wieder aufgenommen, bei False nicht
        self.datastream_wiederaufnehmen = False # bestimmt, ob jemals Daten ausgelesen wurden, und ob nach einer unfreiwilligen Unterbrechung wieder damit begonnen werden soll


    # suche Verbindung zum Sensor alle 10 sek
    def verbindung_suchen(self):
        def nested_verb_suchen(self):
            while not self.verbindung_hergestellt:
                try:
                    if self.bytesize:
                        self.ser = serial.Serial(self.com, timeout=self.timeout, baudrate=self.baudrate, bytesize=self.bytesize, parity=self.parity)
                        self.ser.write(b's0o\r\n')
                    else:
                        self.ser = serial.Serial(self.com, baudrate=self.baudrate, timeout=self.timeout)
                    self.verbindung_hergestellt = True
                except:
                    self.ser = None
                    print("Wiederholte Verbindungssuche vom Sensor \"{}\" fehlgeschlagen".format(type(self).__name__))
                    time.sleep(10)
            else:
                if self.datastream_wiederaufnehmen:
                    self.read_datastream()
                if self.db_schreiben_wiederaufnehmen:
                    self.start_pushing_db()
        threading.Thread(target=nested_verb_suchen, args=(self, ), daemon=True).start()


    # herstellen der Verbindung
    @staticmethod
    def connect(COM="COM0", baudrate=0, timeout=0, taktrate=0):
        sensor = Sensor(COM, baudrate, timeout, taktrate)
        return sensor


    # schließen der Verbindung
    def kill(self):
        self.close_datastream()
        time.sleep(0.2)
        if self.ser:
            self.ser.close()
        if self.db_zeiger:
            self.db_zeiger.close()
            self.db_verb.close()


    # liest die spezifischen Daten jedes Sensor (muss je Sensor implementiert werden)
    # Bei Echolot z.B.: Trennung jeder Datenzeile und Einfügen der Daten in ein Daten-Objekt
    def read_sensor_data(self):
        pass # Implementierung in abgeleiteter Klasse


    # Abbruch des Datenstreams (diese Variable wird innerhalb der entsprechenden Methode getestet)
    def close_datastream(self):
        self.close_writing_db()
        time.sleep(0.2)
        self.datastream = False
        if not self.listen_process:
            self.listen_process = None


    # beendet das Schreiben auf die DB
    def close_writing_db(self):
        self.writing_db = False
        time.sleep(0.2)
        if not self.writing_process:
            self.writing_process = None


    # liest die Daten parallel in einem gesonderten Thread, zunächst unendlicher Stream, kann aber über self.close_datastream() abgebrochen werden
    def read_datastream(self):
        self.datastream = True
        self.datastream_wiederaufnehmen = True

        # hier durchgehend (in while True) testen, ob Daten ankommen und in Daten-Objekte organisieren
        def nested_read(self):
            while self.datastream and self.verbindung_hergestellt:
                t = time.time()
                try:
                    daten = self.read_sensor_data()
                    if daten:
                        self.aktdaten = daten
                        self.daten.put(daten)
                    else:
                        self.aktdaten = False
                    schlafen = max(0, self.taktrate - (time.time() - t))
                    time.sleep(schlafen)
                except Exception as e: # hierin werden Ausnahmen behandelt, bei denen die Verbindung zur seriellen Schnittstelle nachweislich abgebrochen wurde
                    self.close_datastream() # schließen, da vermutlich keine Verbindung zum Sensor besteht
                    self.verbindung_hergestellt = False
                    self.verbindung_suchen()
                    print("Datenstrom zum Sensor \"{}\" abgebrochen. Versuche neu zu verbinden.".format(type(self).__name__))
                    print(e)
                except: #TODO: hierin werden Ausnahmen behandelt, bei der der Sensor nachweislich verbunden ist, aber zunächst keine Signale liefert (hierbei darf die Behandlung nicht in den read_data-Methoden der abgeleitetn Klassen erfolgen)
                    print("Datenstrom zum Sensor \"{}\" kurzzeitig abgebrochen".format(type(self).__name__))
                    schlafen = max(0, self.taktrate - (time.time() - t))
                    time.sleep(schlafen)
            else:
                # der Thread muss nicht gekillt werden, wenn seine Target-Funktion terminiert
                # was sie tut, sobald self.datastream == False ist
                pass

        self.listen_process = threading.Thread(target=nested_read, args=(self, ), daemon=True)
        self.listen_process.start()


    # Verbindung zur Datenbank herstellen
    # database nach dem Schema: 20201025_175800
    def connect_to_db(self, db_table="", database="`"+str((datetime.datetime.fromtimestamp(time.time())))+"`",server="localhost", uid="root", password="EchoBoat"):
        if db_table == "":
            self.db_table = type(self).__name__
        else:
            self.db_table = db_table
        self.db_database = database
        self.db_verb = pyodbc.connect("DRIVER={MySQL ODBC 8.0 ANSI Driver}; SERVER=" + server + "; UID=" + uid + ";PASSWORD=" + password + ";")
        self.db_zeiger = self.db_verb.cursor()

        # Anlegen einer Datenbank je Messkampagne und einer Tabelle je Sensor
        self.db_zeiger.execute("CREATE SCHEMA IF NOT EXISTS " + self.db_database + ";")
        connect_table_string = "CREATE TABLE " + self.db_database + ".`" + self.db_table + "` ("
        temp = ", ".join([komp[0] + " " + komp[1] for komp in self.db_felder])
        self.db_zeiger.execute(connect_table_string + temp + ");")


    # setzt eine Liste von Daten zusammen, mit denen die Daten-Objekte über Cursor.execute() in die DB enigepflegt werden können
    # WICHTIG: auf den Aufbau der Datenbank achten! Columns id, zeit und vor allem wie daten aufgebaut ist
    # id_zeit: sagt aus, ob auch diese beiden Attribute in den String umgesetzt werden
    def make_db_command(self, datenpaket, id_zeit=True, fehler=False):
        return str()


    # Daten in die Datenbank schreiben
    #TODO: falls diese Funktion benutzt wird, muss abgefangen werden, dass make_db_command bei einem Fehler "" zurückgibt
    def start_pushing_db(self):
        self.writing_db = True
        self.db_schreiben_wiederaufnehmen = True

        def nested_db_hochladen(self):
            while self.writing_db and self.datastream: # in DB schreiben, nur wenn auch der Sensor ausgelesen wird
                daten = self.daten.get()
                if daten != None: # ... und Daten zum Schreiben vorliegen
                    db_string_praefix = "INSERT INTO " + self.db_database + "." + self.db_table + " VALUES ("
                    self.db_zeiger.execute(db_string_praefix + self.make_db_command(daten) + ");")
                    self.db_zeiger.commit()

        self.writing_process = threading.Thread(target=nested_db_hochladen, args=(self, ), daemon=True)
        self.writing_process.start()


class IMU(Sensor):

    id = 0

    def __init__(self, COM=0, baudrate=0, timeout=0, taktrate=0.2, bytesize=None, parity=None):
        super().__init__(COM, baudrate, timeout, taktrate, bytesize, parity)
        self.db_felder = [("id", "INT"), ("zeitpunkt", "DOUBLE"), (), (), (), (), (), (), (), (), ()]  # DB-Felddefinition für die EInrichtung einer DB-Tabelle



class Echolot(Sensor):

    id = 0

    def __init__(self, COM=0, baudrate=19200, timeout=0, taktrate=0.2, bytesize=None, parity=None):
        super().__init__(COM, baudrate, timeout, taktrate, bytesize, parity)
        self.db_felder = [("id", "INT"), ("zeitpunkt", "DOUBLE"), ("tiefe1", "DOUBLE"), ("tiefe2", "DOUBLE")]


    # Aufbau der Datenbank (die Felder) muss zwingend folgendermaßen sein: id als Int, zeit als Int, daten als String
    def make_db_command(self, datenpaket, id_zeit=True, fehler=False):
        if not fehler:
            if id_zeit:
                db_string_daten = [datenpaket.id, datenpaket.timestamp, datenpaket.daten[0], datenpaket.daten[1]]
            else:
                db_string_daten = [datenpaket.daten[0], datenpaket.daten[1]]
            db_string_daten = ", ".join(str(x) for x in db_string_daten)
            return db_string_daten
        else:
            return ""


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
        tiefe1 = bytes(line).decode("UTF-8").split()[2]
        tiefe2 = bytes(line).decode("UTF-8").split()[3]
        db_objekt = Daten(Echolot.id, [tiefe1, tiefe2], time.time())
        Echolot.id += 1


        return db_objekt # Datenobjekt mit entsprechenden Einträgen



class GNSS(Sensor):

    #Todo: ids gnss richtig angeben
    id = 0

    def __init__(self, COM=0, baudrate=115200, timeout=0, taktrate=0.2, bytesize=None, parity=None):
        super().__init__(COM, baudrate, timeout, taktrate, bytesize, parity)
        self.db_felder = [("id", "INT"), ("zeitpunkt", "DOUBLE"), ("punkt", "POINT"), ("HDOP","DOUBLE"), ("up", "DOUBLE"), ("Qualitaet", "INT")]


    # je nach Art der NMEA-Nachricht müssen hier unterschiedliche Daten-Objekte gebildet werden
    def read_sensor_data(self):
        nmea = self.ser.readline()
        if nmea != b"":
            nmea = nmea.decode("utf-8")
            try:
                nmea = pynmea2.parse(nmea)
                # auslesen der GNSS-Daten nur, wenn eine GGA-Nachricht vorliegt
                if nmea.sentence_type == "GGA":
                    # die self.daten sind hier erstmal nur die Koordinaten in utm
                    koords = utm.from_latlon(nmea.latitude, nmea.longitude)
                    daten = [koords[2]*10**6+koords[0], koords[1], nmea.horizontal_dil, nmea.altitude, nmea.gps_qual] # Ausgeben von lat, lon, Höhe, Qualität,
                    db_objekt = Daten(GNSS.id, daten, time.time())
                    GNSS.id += 1
                    return db_objekt  # Datenobjekt mit entsprechenden Einträgen
            except Exception as e:
                print("Parsen fehlgeschlagen",self.db_table, e)
                #TODO: Prio 99, Fehlerzähler + Ausgabe in GUI self.Fehlerzaehler_pars += 1


    # Aufbau der Datenbank (die Felder) muss zwingend folgendermaßen sein: id als Int, zeit als Int, east/north als DOUBLE
    def make_db_command(self, datenpaket, id_zeit=True, fehler=False):
        if not fehler:
            punkt_temp = "ST_pointfromtext('POINT(" + str(datenpaket.daten[0]) + " " + str(datenpaket.daten[1]) + ")', 25832)"
            if id_zeit:
                db_string_daten = [datenpaket.id, datenpaket.timestamp, punkt_temp, str(datenpaket.daten[2]), str(datenpaket.daten[3]), str(datenpaket.daten[4])] # Einfügen von Id, Timestamp, lat, lon, Höhe, Qualität,
            else:
                db_string_daten = [punkt_temp, str(datenpaket.daten[2]), str(datenpaket.daten[3]), str(datenpaket.daten[4])]  # Einfügen von Id, Timestamp, lat, lon, Höhe, Qualität,
            db_string_daten = ", ".join(str(x) for x in db_string_daten)
            return db_string_daten
        else:
            return ""

class Distanzmesser(Sensor):

    id = 0

    def __init__(self, COM=0, baudrate=19200, timeout=0, taktrate=0.2, bytesize=7, parity='E'):
        super().__init__(COM, baudrate, timeout, taktrate, bytesize, parity)
        self.db_felder = [("id", "INT"), ("zeitpunkt", "DOUBLE"), ("distanz", "DOUBLE")]

    def make_db_command(self, datenpaket, id_zeit=True, fehler=False):
        if not fehler:
            if id_zeit:
                db_string_daten = [datenpaket.id, datenpaket.timestamp, datenpaket.daten]
            else:
                db_string_daten = [datenpaket.daten]
            db_string_daten = ", ".join(str(x) for x in db_string_daten)
            return db_string_daten
        else:
            return ""


    # je nach Art der NMEA-Nachricht müssen hier unterschiedliche Daten-Objekte gebildet werden
    def read_sensor_data(self):
        try:
            self.ser.write(b's0g\r\n')
            Dist = self.ser.readline().decode("ascii")[4:].rstrip("\n")
            if Dist != '':
                Dist=int(Dist)/10000
                db_objekt = Daten(Distanzmesser.id, Dist, time.time())
                Distanzmesser.id += 1
                return db_objekt  # Datenobjekt mit entsprechenden Einträgen

        except Exception as e:
                print("Fehler bei Distanzmessung", self.db_table, e)


# Nur zum Testen:
if __name__ == "__main__":

    gps2 = GNSS("COM10",115200,0,0.2)
    gps2.connect_to_db("GNSS2")
    gps2.read_datastream()
    gps2.start_pushing_db()

    gps1 = GNSS("COM11",115200,0,0.2)
    gps1.connect_to_db("GNSS1")
    gps1.read_datastream()
    gps1.start_pushing_db()

    dist = Distanzmesser("COM12",19200,0,1)
    dist.connect_to_db()
    dist.read_datastream()
    dist.start_pushing_db()
    
    echo = Echolot("COM1",19200,0,0.2)
    echo.connect_to_db()
    echo.read_datastream()
    echo.start_pushing_db()

    #todo Überprüfen von Fetch in datenbank Lösung: Neustart https://stackoverflow.com/questions/57905821/tables-and-views-keep-on-fetching-in-mysql
    time.sleep(10)
    print("Kills ausführen")
    gps1.kill()
    gps2.kill()
    dist.kill()
    echo.kill()