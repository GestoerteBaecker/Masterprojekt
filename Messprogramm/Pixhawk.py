import dronekit as dronekit
import utm
import time
#import mavgen
import threading

# Klasse zum Ansteuern der Motoren
class Pixhawk:

    def __init__(self, COM):

        self.connection_string = COM
        self.verbindung_hergestellt = False
        self.initialisierung = False
        self.homepoint = None # für RTL

        def Initialisierungsfuntion(self):  # Wird aufgerufen, damit das Hauptprogramm nicht aufgehalten wird, wenn kein Pixhawk angeschlossen ist, oder der Verbindungsvorgang sehr lange dauert
            try:
                self.Verbinden()    # Methode führt die Verbindungsfunktion so lange aus, bis self.vehicle angelegt ist

            except:
                print("Es konnte keine Verbindung mit dem PixHawk hergestellt werden")

            while not hasattr(self, 'vehicle'):              # Warten, bis der PixHawk bereit zum initialisieren ist
                time.sleep(1)                               # Homeposition wird automatisch bei einer FIX-GNSS-Lösung erzeugt
            print('PixHawk verbunden')
            try:
                self.Initialisieren()
                print("PixHawk verbunden und initialisiert")

            except:
                print("PixHawk konnte nicht initialisiert werden")

        self.listen_process = threading.Thread(target=Initialisierungsfuntion, args=(self,), daemon=True)
        self.listen_process.start()

    def Verbinden(self):

        while True:
            if hasattr(self, 'vehicle'):
                self.verbindung_hergestellt = True
                break
            else:
                self.verbindung_hergestellt = False

            if not self.verbindung_hergestellt:

                try:
                    self.vehicle = dronekit.connect(self.connection_string, wait_ready=True)
                except:
                    self.verbindung_hergestellt = False
                    print("Wiederholte Verbindungssuche vom Sensor 'PixHawk' fehlgeschlagen")
                    time.sleep(10)

    def Initialisieren(self):

        self.vehicle.initialize()
        self.vehicle.armed = True
        self.vehicle.mode = dronekit.VehicleMode("GUIDED")
        self.initialisierung = True
        self.HomepointSetzen()

        #todo: Takeoff einbauen?

    def Geschwindigkeit_setzen(self, v):  # v = Geschwindigkeit im m/s

        self.vehicle.groundspeed = v

    def Wegpunkt_anfahren(self, utm_x, utm_y):

        if self.initialisierung:
            wp = dronekit.LocationGlobal(utm.to_latlon(utm_x, utm_y, 32, 'U'), 0)
            self.vehicle.simple_goto(wp)
        else:
            try:    self.Initialisieren()
            except: print("PixHawk konnte nicht initialisiert werden")

            if self.initialisierung: self.Wegpunkt_anfahren()

    def Notstop(self):
        pass
        #self.vehicle.send_mavlink("MAV_GOTO_DO_HOLD") #todo: richtige MAV-Link-Nachricht eifügen

    def Return_to_launch(self):

        self.vehicle.mode = dronekit.VehicleMode("RTL")

    # Punkt, der bei RTL angefahren werden soll
    def HomepointSetzen(self):
        #TODO: Implementieren
        pass

    def Trennen(self):

        if self.vehicle: self.vehicle.close()

