from tkinter import *
from PIL import Image
from pyproj import Proj, transform
import matplotlib.pyplot as plt
plt.ion() # Aktivieren eines dynamischen Plots
import math
import numpy as np
import utm
import random
import threading

# Klasse, die als Softwareverteilung dient und jedes weitere Unterprogramm per Buttondruck bereithält
class Anwendung_Karte():
    # Konstruktor  der GUI der Hauptanwendung zum Öffnen aller weiteren GUIs
    def __init__(self,Monitor,position=0,tilefiles=None):

        # Übernehmen des Ordnerpfades und Fensterposition
        self.tilefiles=tilefiles
        self.position=position
        self.monitor=Monitor

        # Abschluss der Initialisierung durch erstmaliges Laden der Karte
        self.karte_laden()

    # Funktion, um Lat und Lon zu OSM-Kachelnummern umzurechnen
    def deg2num(self,lat_deg, lon_deg, zoom):
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        return (xtile, ytile)

    # Funktion, um OSM-Kachelnummern zu Lat und Lon umzurechnen
    def num2deg(self,xtile, ytile, zoom):
        n = 2.0 ** zoom
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        lat_deg = math.degrees(lat_rad)
        return (lat_deg, lon_deg)


    def karte_laden(self):
        # Öffnen der Kacheln

        self.xtile_num_max,self.ytile_num_max=-math.inf,-math.inf
        self.xtile_num_min, self.ytile_num_min=math.inf,math.inf
        self.zoom=int(self.tilefiles[0].rsplit("/",1)[1].split("_")[0]) # Zoom-Angabe für erstes Bild

        # Schleife zum Finden der Bounding-Box
        for tilefile in self.tilefiles:
            xtile_num=int(tilefile.rsplit("/",1)[1].split("_")[1]) # Kachelname für Lat
            ytile_num=int(tilefile.rsplit("/", 1)[1].split("_")[2].split(".")[0]) # Kachelname für Lon

            if xtile_num > self.xtile_num_max: self.xtile_num_max=xtile_num
            if xtile_num < self.xtile_num_min: self.xtile_num_min=xtile_num
            if ytile_num > self.ytile_num_max: self.ytile_num_max=ytile_num
            if ytile_num < self.ytile_num_min: self.ytile_num_min=ytile_num

        # Anlegen eines neuen Bildes, in dem die Kacheln geladen werden
        self.cluster = Image.new('RGB', ((self.xtile_num_max - self.xtile_num_min + 1) * 256-1, (self.ytile_num_max - self.ytile_num_min + 1) * 256-1)) # 256-1?

        # Schleife über alle Bilder öffnet die Kacheln und fügt es dem Bildcluster hinzu
        for tilefile in self.tilefiles:
            tileimg=Image.open(tilefile)
            tilename=tilefile.rsplit("/",1)[1] # Dateiname aus Dateipfad extrahieren
            xtile=int(tilename.split("_")[1]) # Extrahieren der X-Tile
            ytile=int(tilename.split("_")[2].split(".")[0]) # Extrahieren der Y-Tile abzüglich Datei-Endung

            self.cluster.paste(tileimg, box=((xtile - self.xtile_num_min) * 256, (ytile - self.ytile_num_min) * 256)) # Vorher 255
            tileimg.close()

        # Dimension des Bildes
        self.img_width,self.img_height=self.cluster.size

        # Darstellen der Karte
        self.plt=plt
        self.figure,self.ax = plt.subplots()
        self.figure.suptitle("EchoBoat - Autopilot Navigator")
        self.figure.patch.set_facecolor('white')
        self.figure.canvas.set_window_title('EchoBoat - Autopilot Navigator')
        # Zum Abfangen von Fehlern beim Schließen der Karte
        self.figure.canvas.mpl_connect('close_event',self.karte_geschlossen)

        # Variablen für das spätere Boot setzen
        self.boat_position, = self.ax.plot([], [], marker=(3, 0, 0),markersize=10, color="darkblue")
        self.current_boat_heading,=self.ax.plot([],[],':',lw=1, color="darkblue")
        self.boat_route,=self.ax.plot([],[],'-',lw=1, color="red")
        self.route_x,self.route_y=[],[]

        # Anzeigen des Bildes
        self.map=self.ax.imshow(np.asarray(self.cluster))
        # Abfragen und Setzen der Fenster-Position
        thismanager=plt.get_current_fig_manager()
        positionx,positiony=self.position
        thismanager.window.wm_geometry("+"+str(positionx)+"+"+str(positiony))

        # Bestimmen der Transformationsparameter
        # Umrechnung der (kleinsten und größten) Kachelnummern im Bild in Lat und Lon
        xtile_deg_min,ytile_deg_min=self.num2deg(self.xtile_num_min,self.ytile_num_min,self.zoom)
        xtile_deg_max,ytile_deg_max=self.num2deg(self.xtile_num_max+1,self.ytile_num_max+1,self.zoom) # +1, da rechte untere Ecke der Kachel gesucht ist

        # Umrechnung von Lat und Lon in kartesische Koordinaten (beide WGS84)
        osm_proj=Proj("epsg:4326") # Input-Proj
        gnss_proj=Proj("epsg:3857") # Output-Proj

        xtile_deg_min_proj, ytile_deg_min_proj = transform(osm_proj,gnss_proj,xtile_deg_min,ytile_deg_min)
        xtile_deg_max_proj, ytile_deg_max_proj = transform(osm_proj,gnss_proj,xtile_deg_max,ytile_deg_max)

        self.upperleft_wgs84=xtile_deg_min_proj,ytile_deg_min_proj
        self.lowerright_wgs84=xtile_deg_max_proj,ytile_deg_max_proj

        # Bildkoordinaten der Bildecken
        self.upperleft_img=0,0
        self.lowerright_img=self.img_width,self.img_height

        # Transformationparameter zwischen den Systemen (img und wgs84)
        delta_y_quell=self.lowerright_wgs84[1]-self.upperleft_wgs84[1]
        delta_x_quell = self.lowerright_wgs84[0] - self.upperleft_wgs84[0]
        delta_y_ziel=self.lowerright_img[1]-self.upperleft_img[1]
        delta_x_ziel=self.lowerright_img[0]-self.upperleft_img[0]

        s_quell=math.sqrt(delta_y_quell**2+delta_x_quell**2)
        s_ziel=math.sqrt(delta_y_ziel**2+delta_x_ziel**2)

        self.m=s_ziel/s_quell


    def karte_updaten(self,gnss_north,gnss_east,gnss_heading,t):
        # Setzen einer leeren Variable für die Boot-Position
        self.gnss_north=gnss_north
        self.gnss_east=gnss_east
        self.gnss_heading=gnss_east
        self.t=t

        # Plotten der aktuellen Boot-Position inklusive Heading
        self.plot_boat()

        # Plotten der abgefahrenen Route (im vorgegebenen Aktualisierungstakt)
        # Wird nicht ausgeführt, falls kein Signal vorhanden (also t=None)
        if self.t: self.plot_boatroute()

        # Plotten der aktuellen Wegpunkte
        # self.plot_waypoint()

        # Plotten der neuen Daten
        self.figure.canvas.draw()
        #plt.pause(0.2)

    def plot_boat(self):
        try:
            # Einlesen der aktuellen Boot-Daten
            heading_deg = self.gnss_heading
            heading_rad=math.radians(self.gnss_heading)
            boat_utm_x=self.gnss_north
            boat_utm_y = self.gnss_east

            # Umrechnung der Boot-UTM-Koordinaten in Bild-Koordinaten
            self.current_boat_position_x,self.current_boat_position_y=self.img_utm_trans(boat_utm_x,boat_utm_y)

            # Setzen der Punkte im Plot auf neue Werte
            self.current_boat_heading.set_xdata([self.current_boat_position_x, self.current_boat_position_x+math.sin(heading_rad)*100])
            self.current_boat_heading.set_ydata([-self.current_boat_position_y, -self.current_boat_position_y + math.cos(heading_rad-math.pi) * 100])
            self.boat_position.set_xdata(self.current_boat_position_x)
            self.boat_position.set_ydata(-self.current_boat_position_y)
            self.boat_position.set_marker(marker=(3,0,-heading_deg))

        # Wenn keine GPS-Daten vorhanden, Fehlermeldung ausgeben
        except:
            self.ax.text(.5, .5,'NO GPS DATA', horizontalalignment='center',
                            verticalalignment='center', size=15, color="red",transform=self.ax.transAxes)

    def img_utm_trans(self,boat_utm_x,boat_utm_y):

        # Umrechnung der ETRS89-Koordinaten aus GNSS zu WGS84 OSM-System
        gnss_proj=Proj("epsg:25832") # Input-Proj
        osm_proj=Proj("epsg:3857") # Output-Proj

        boat_wgs84_x, boat_wgs84_y = transform(gnss_proj,osm_proj,boat_utm_x,boat_utm_y)

        # Anwenden der Transformationsparameter
        boat_img_x=self.upperleft_img[0]-self.m*self.upperleft_wgs84[0]+self.m*boat_wgs84_x
        boat_img_y=self.upperleft_img[1]-self.m*self.upperleft_wgs84[1]+self.m*boat_wgs84_y

        return boat_img_x,boat_img_y

    # TODO: Funktion definieren
    def plot_waypoint(self):
        x=1

    def plot_boatroute(self):
        update_interval = 10
        if self.t % update_interval == 0:
            self.route_x.append(self.current_boat_position_x)
            self.route_y.append(-self.current_boat_position_y)
            if len(self.route_y)>1:
                self.boat_route.set_xdata(self.route_x)
                self.boat_route.set_ydata(self.route_y)

    def karte_geschlossen(self,evt):
        self.monitor.karte_window = None