from dronekit import connect, VehicleMode, LocationGlobal
import utm

# Klasse zum Ansteuern der Motoren
class Pixhawk:

    def __init__(self,COM="COM0"):

        self.connection_string = COM
        self.vehicle = ""

    def Verbinden(self):

        self.vehicle = connect(self.connection_string, wait_ready=True)
        self.vehicle.initialize()

    def Geschwindigkeit_setzen(self, v):  # v = Geschwindigkeit im m/s

        self.vehicle.groundspeed(v)


    def Wegpunkt_anfahren(self, utm_x, utm_y):

        wp = LocationGlobal(utm.to_latlon(utm_x, utm_y, 32, 'U'))
        self.vehicle.simple_goto(wp)

    def Retrun_to_launche:
        pass


