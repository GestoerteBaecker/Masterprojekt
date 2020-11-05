from tkinter import *
from tkinter import filedialog
import tkinter.ttk as ttk
from PIL import Image
import matplotlib.pyplot as plt
plt.ion() # Aktivieren eines dynamischen Plots
import math
import numpy as np
import utm
import random
import threading

# Import der aufzurufenden Skripte
#import boot
#import ____

# Klasse, die als Softwareverteilung dient und jedes weitere Unterprogramm per Buttondruck bereithält
class Anwendung_Karte(Frame):
    # Konstruktor  der GUI der Hauptanwendung zum Öffnen aller weiteren GUIs
    def __init__(self,position=0,tilefiles=None):

        # Übernehmen des Ordnerpfades und Fensterposition
        self.tilefiles=tilefiles
        self.position=position

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

        self.xmax,self.ymax=-math.inf,-math.inf
        self.xmin, self.ymin=math.inf,math.inf
        self.zoom=int(self.tilefiles[0].rsplit("/",1)[1].split("_")[0]) # Zoom-Angabe für erstes Bild

        # Schleife zum Finden der Bounding-Box
        for tilefile in self.tilefiles:
            xtile_num=int(tilefile.rsplit("/",1)[1].split("_")[1]) # Kachelname für Lat
            ytile_num=int(tilefile.rsplit("/", 1)[1].split("_")[2].split(".")[0]) # Kachelname für Lon

            if xtile_num > self.xmax: self.xmax=xtile_num
            if xtile_num < self.xmin: self.xmin=xtile_num
            if ytile_num > self.ymax: self.ymax=ytile_num
            if ytile_num < self.ymin: self.ymin=ytile_num

        # Anlegen eines neuen Bildes, in dem die Kacheln geladen werden
        self.cluster = Image.new('RGB', ((self.xmax - self.xmin + 1) * 256-1, (self.ymax - self.ymin + 1) * 256-1)) # 256-1?

        # Schleife über alle Bilder öffnet die Kacheln und fügt es dem Bildcluster hinzu
        for tilefile in self.tilefiles:
            tileimg=Image.open(tilefile)
            tilename=tilefile.rsplit("/",1)[1] # Dateiname aus Dateipfad extrahieren
            xtile=int(tilename.split("_")[1]) # Extrahieren der X-Tile
            ytile=int(tilename.split("_")[2].split(".")[0]) # Extrahieren der Y-Tile abzüglich Datei-Endung

            self.cluster.paste(tileimg, box=((xtile - self.xmin) * 256, (ytile - self.ymin) * 256)) # Vorher 255
            tileimg.close()

        # Dimension des Bildes
        self.img_width,self.img_height=self.cluster.size

        # Darstellen der Karte
        self.plt=plt
        self.figure,self.ax = plt.subplots()
        self.figure.suptitle("EchoBoat - Autopilot Navigator")
        self.figure.patch.set_facecolor('white')
        self.figure.canvas.set_window_title('EchoBoat - Autopilot Navigator')
        self.map=self.ax.imshow(np.asarray(self.cluster))
        # Abfragen und Setzen der Fenster-Position
        thismanager=plt.get_current_fig_manager()
        positionx,positiony=self.position
        thismanager.window.wm_geometry("+"+str(positionx)+"+"+str(positiony))

    def karte_updaten(self):
        # Setzen einer leeren Variable für die Boot-Position
        self.boat_position, = self.ax.plot([], [], marker=(3, 0, 0),markersize=10, color="darkblue")
        self.current_boat_heading,=self.ax.plot([],[],':',lw=1, color="darkblue")
        self.boat_route,=self.ax.plot([],[],'-',lw=1, color="grey")
        self.route_x=[]
        self.route_y=[]


        t = 0
        update_interval = 10
        # Schleife plottet ständig die neuesten Daten
        while True:
            # Plotten der aktuellen Boot-Position inklusive Heading
            self.plot_boat(t)
            # Plotten der aktuellen Wegpunkte
            # self.plot_waypoint()
            if t%update_interval==0:
                # Plotten der abgefahrenen Route (im vorgegebenen Aktualisierungstakt)
                self.plot_boatroute()
            # Plotten der neuen Daten
            self.figure.canvas.draw()
            t+=1
            plt.pause(0.2)


    def plot_boat(self,t):
        try:
            # Einlesen der aktuellen Boot-Daten
            heading_deg = 27+random.randint(-10,10)
            heading_rad=math.radians(heading_deg)
            boat_utm_x = 452049.974+t
            boat_utm_y = 5885228.359+t

            # Umrechnung der Boot-UTM-Koordinaten in Bild-Koordinaten
            self.current_boat_position_x,self.current_boat_position_y=self.img_utm_trans(boat_utm_x,boat_utm_y)

            # Setzen der Punkte im Plot auf neue Werte
            self.current_boat_heading.set_xdata([self.current_boat_position_x, self.current_boat_position_x+math.sin(heading_rad)*100])
            self.current_boat_heading.set_ydata([-self.current_boat_position_y, -self.current_boat_position_y + math.cos(heading_rad-math.pi) * 100])
            self.boat_position.set_xdata(self.current_boat_position_x)
            self.boat_position.set_ydata(-self.current_boat_position_y)
            self.boat_position.set_marker(marker=(3,0,-heading_deg))

            # Plotten der neuen Daten
            #self.figure.canvas.draw()

        # Wenn keine GPS-Daten vorhanden, Fehlermeldung ausgeben
        except:
            self.ax.text(.5, .5,'NO GPS DATA', horizontalalignment='center',
                            verticalalignment='center', size=15, color="red",transform=self.ax.transAxes)

    def img_utm_trans(self,boat_utm_x,boat_utm_y):

        # Umrechnung der Kachelnummern im Bild in Lat und Lon
        xmin,ymin=self.num2deg(self.xmin,self.ymin,self.zoom)
        xmax,ymax=self.num2deg(self.xmax+1,self.ymax+1,self.zoom) # +1, da rechte untere Ecke der Kachel gesucht ist

        # UTM-Koordinaten der oberen linken und unteren rechten Bildecke
        upperleft_utm=utm.from_latlon(xmin, ymin)[0:2]
        lowerright_utm=utm.from_latlon(xmax, ymax)[0:2]

        # Bildkoordinaten der Bildecken
        upperleft_img=0,0
        lowerright_img=self.img_width,self.img_height

        # Transformationparameter zwischen den Systemen (img und utm)
        delta_y_quell=lowerright_utm[1]-upperleft_utm[1]
        delta_x_quell = lowerright_utm[0] - upperleft_utm[0]
        delta_y_ziel=lowerright_img[1]-upperleft_img[1]
        delta_x_ziel=lowerright_img[0]-upperleft_img[0]

        s_quell=math.sqrt(delta_y_quell**2+delta_x_quell**2)
        s_ziel=math.sqrt(delta_y_ziel**2+delta_x_ziel**2)

        m=s_ziel/s_quell

        # Anwenden der Transformationsparameter
        boat_img_x=upperleft_img[0]-m*upperleft_utm[0]+m*boat_utm_x
        boat_img_y=upperleft_img[1]-m*upperleft_utm[1]+m*boat_utm_y

        return boat_img_x,boat_img_y

    # TODO: Funktion definieren
    def plot_waypoint(self):
        x=1

    def plot_boatroute(self):
        self.route_x.append(self.current_boat_position_x)
        self.route_y.append(-self.current_boat_position_y)
        if len(self.route_y)>1:
            self.boat_route.set_xdata(self.route_x)
            self.boat_route.set_ydata(self.route_y)


#if __name__=="__main__":
    #fenster=Tk()
    #fenster.title("EchoBoat - Autopilot Navigator")
    #anwendung=Anwendung_Karte(fenster)
    #fenster.mainloop()