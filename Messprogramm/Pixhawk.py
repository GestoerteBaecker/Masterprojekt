import dronekit as dronekit
import utm
import time
#import mavgen
import threading

# Klasse zum Ansteuern der Motoren
class Pixhawk:

    def __init__(self, COM):

        self.connection_string = COM
        self.vehicle = ""
        self.verbindung_hergestellt = False
        self.initialisierung = False

        try:
            self.Verbinden()

        except:
            print("Es konnte keine Verbindung mit dem PixHawk hergestellt werden")

        while not self.vehicle.is_armable:              # Warten, bis der PixHawk bereit zum initialisieren ist
            time.sleep(1)                               # Homeposition wird automatisch bei einer FIX-GNSS-Lösung erzeugt

        try:
            self.Initialisieren()
            print("PixHawk verbunden und initialisiert")

        except:
            print("PixHawk konnte nicht initialisiert werden")


    def Verbinden(self):

        def DauerhafteVerbindung(self):

            while True:
                if self.vehicle.mode: self.verbindung_hergestellt = True
                else: self.verbindung_hergestellt = False

                if not self.verbindung_hergestellt:
                    self.vehicle = dronekit.connect(self.connection_string, wait_ready=True)
                    self.verbindung_hergestellt = True
                time.sleep(10)

        self.listen_process = threading.Thread(target=DauerhafteVerbindung, args=(self,), daemon=True)
        self.listen_process.start()

    def Initialisieren(self):

        self.vehicle.initialize()
        self.vehicle.armed = True
        self.vehicle.mode = dronekit.VehicleMode("GUIDED")
        self.initialisierung = True

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

    def Trennen(self):

        self.vehicle.close()

