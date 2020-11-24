from tkinter import *
from PIL import Image
from pyproj import Proj, transform
import matplotlib.pyplot as plt
plt.ion() # Aktivieren eines dynamischen Plots
import math
import numpy as np
import rasterio
from rasterio.plot import show
import time
import utm

# Klasse, die als Softwareverteilung dient und jedes weitere Unterprogramm per Buttondruck bereithält
class Anwendung_Karte():
    # Konstruktor  der GUI der Hauptanwendung zum Öffnen aller weiteren GUIs
    def __init__(self,Monitor,position=0,geotiff_path=None):

        # Übernehmen des Ordnerpfades und Fensterposition
        self.geotiff_path=geotiff_path
        self.position=position
        self.monitor=Monitor

        # Abschluss der Initialisierung durch erstmaliges Laden der Karte
        self.karte_laden()

    def karte_laden(self):
        self.grenzpolygon_vorhanden=False

        # Darstellen der Karte
        self.plt = plt
        self.figure, self.ax = plt.subplots()
        self.figure.suptitle("EchoBoat - Autopilot Navigator")
        self.figure.patch.set_facecolor('white')
        self.figure.canvas.set_window_title('EchoBoat - Autopilot Navigator')

        # Zum Abfangen von Fehlern beim Schließen der Karte
        self.figure.canvas.mpl_connect('close_event', self.karte_geschlossen)

        self.cid = self.figure.canvas.mpl_connect('button_press_event', self.onclick)
        self.coords = []

        # Anzeigen der geotiff
        self.geotiff = rasterio.open(self.geotiff_path)
        show(self.geotiff, adjust='None', ax=self.ax)

        # Variablen für das spätere Boot setzen
        self.boat_position, = self.ax.plot([], [], marker=(3, 0, 0),markersize=10, color="darkblue")
        self.current_boat_heading,=self.ax.plot([],[],':',lw=1, color="darkblue")
        self.grenzpolygon,=self.ax.plot([], [], marker='o',markersize=5, color="red")
        self.boat_route,=self.ax.plot([],[],'-',lw=1, color="red")
        self.route_x,self.route_y=[],[]
        self.grenzpolygon_x,self.grenzpolygon_y=[],[]


        # Abfragen und Setzen der Fenster-Position
        thismanager=self.plt.get_current_fig_manager()
        positionx,positiony=self.position
        #TODO: Positionierung nachgucken
        thismanager.window.wm_geometry("+"+str(positionx)+"+"+str(positiony))

    def karte_updaten(self,gnss_north,gnss_east,gnss_heading,t):
        # Setzen einer leeren Variable für die Boot-Position
        update_interval = 10
        self.gnss_north=gnss_north-32000000
        self.gnss_east=gnss_east
        self.gnss_heading=gnss_heading

        # Plotten der aktuellen Boot-Position inklusive Heading
        self.plot_boat()

        # Plotten der aktuellen Wegpunkte
        # self.plot_waypoint()

        # Alle 10 Durchläufe soll die Route ergänzt werden
        if t and t % update_interval == 0:
            self.plot_boatroute()


    def plot_boat(self):
        try:
            # Einlesen der aktuellen Boot-Daten

            # Setzen der Punkte im Plot auf neue Werte
            self.current_boat_heading.set_xdata([self.gnss_north, self.gnss_north + math.sin(self.gnss_heading*math.pi/200) * 100])
            self.current_boat_heading.set_ydata([self.gnss_east, self.gnss_east + math.cos(self.gnss_heading*math.pi/200 - math.pi) * 100])
            self.boat_position.set_xdata(self.gnss_north)
            self.boat_position.set_ydata(self.gnss_east)
            self.boat_position.set_marker(marker=(3,0,-self.gnss_heading*180/200))

        # Wenn keine GPS-Daten vorhanden, Fehlermeldung ausgeben
        except:
            self.ax.text(.5, .5,'NO GPS DATA', horizontalalignment='center',
                            verticalalignment='center', size=15, color="red",transform=self.ax.transAxes)


    # TODO: Funktion definieren
    def plot_waypoint(self):
        x=1

    def plot_boatroute(self):
        self.route_x.append(self.current_boat_position_x)
        self.route_y.append(-self.current_boat_position_y)
        # Setzen der Route erst, wenn eine Linie gezogen werden kann (also 2 Punkte verfügbar sind)
        if len(self.route_y)>1:
            self.boat_route.set_xdata(self.route_x)
            self.boat_route.set_ydata(self.route_y)

    # Funktion registriert Klick-Events
    def onclick(self,event):
        # Rechtsklick soll vorliegen
        if str(event.button)=='MouseButton.RIGHT':
            ix, iy = event.xdata, event.ydata

            if self.grenzpolygon_vorhanden==False:
                # Rechter Doppelklick soll Polygon schließen
                if event.dblclick==True:
                    self.grenzpolygon_x_utm32=[] # Für die Weitergabe an Pixhawk (GeoFence)
                    self.grenzpolygon_x.append(self.grenzpolygon.get_xdata()[0])
                    self.grenzpolygon_y.append(self.grenzpolygon.get_ydata()[0])
                    self.grenzpolygon.set_color('green')
                    self.grenzpolygon_vorhanden=True
                    for x in self.grenzpolygon_x:
                        x_utm32=x+32000000
                        self.grenzpolygon_x_utm32.append(x_utm32)
                # Einfacher Klick ergänzt Polygon
                else:
                    self.grenzpolygon_x.append(ix)
                    self.grenzpolygon_y.append(iy)

                self.grenzpolygon.set_xdata(self.grenzpolygon_x)
                self.grenzpolygon.set_ydata(self.grenzpolygon_y)

            # Erneuter Doppelklick löscht bestehende Form
            else:
                if event.dblclick==True:
                    self.grenzpolygon.set_xdata([])
                    self.grenzpolygon.set_ydata([])
                    self.grenzpolygon_x, self.grenzpolygon_y = [], []
                    self.grenzpolygon.set_color('red')
                    self.grenzpolygon_vorhanden=False

    def karte_geschlossen(self,evt):
        self.monitor.karte_window = None