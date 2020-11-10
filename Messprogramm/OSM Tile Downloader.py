import matplotlib.pyplot as plt
import numpy as np
import math
import requests
from tkinter import *
from PIL import Image
from tkinter import filedialog
import time

class Anwendung_Karte(Frame):
    # Konstruktor  der GUI der Hauptanwendung zum Öffnen aller weiteren GUIs
    def __init__(self, master):
        # Ausführen des Konstruktors der Basisklasse
        super().__init__(master)
        # Anlegen eines zum Platzieren von Widgets benötigten Gitters
        self.grid()
        # Den Widgetcontainer als Objektvariable einführen, damit er von außen zugänglich ist
        self.master = master
        # Fixieren des Fensters
        self.master.resizable(width=False, height=False)

        # Definieren eines Randabstandes des Fensters
        randabstand = 50
        self.master.geometry('+%d+%d' % (randabstand, randabstand))

        # Überschrift
        Label(self,text="OSM Tile Downloader",font='Helvetica 12 bold').grid(row=0,column=0,columnspan=8,pady=10)

        self.var_lat_max=StringVar()
        self.var_lat_max.set('53.1201')
        Label(self, text="Lat1 in Grad").grid(row=1, column=0)
        self.lat_max=Entry(self,textvariable=self.var_lat_max).grid(row=2,column=0, padx=5)

        self.var_lon_max=StringVar()
        self.var_lon_max.set('8.268')
        Label(self, text="Lon1 in Grad").grid(row=1, column=1)
        self.lon_max=Entry(self,textvariable=self.var_lon_max).grid(row=2,column=1, padx=5)

        self.var_lat_min=StringVar()
        self.var_lat_min.set('53.1056')
        Label(self, text="Lat2 in Grad").grid(row=3, column=0,pady=(10,0))
        self.lat_min=Entry(self,textvariable=self.var_lat_min).grid(row=4,column=0, padx=5)

        self.var_lon_min=StringVar()
        self.var_lon_min.set('8.2924')
        Label(self, text="Lon2 in Grad").grid(row=3, column=1,pady=(10,0))
        self.lon_min=Entry(self,textvariable=self.var_lon_min).grid(row=4,column=1, padx=5)

        self.var_zoom=StringVar()
        self.var_zoom.set('15')
        Label(self, text="Zoomstufe:").grid(row=5, column=0,pady=10)
        self.zoom=Entry(self,textvariable=self.var_zoom).grid(row=5,column=1, padx=5,pady=10)

        self.folderPath = StringVar()
        self.save_button=Button(self, text="Speichern unter...",command=lambda:getFolderPath())
        self.save_button.grid(row=6,column=0, columnspan=2,pady=10,padx=10)

        bulk_download_button=Button(self, text="Download!",command=lambda:download_OSMTiles())
        bulk_download_button.grid(row=7,column=0, columnspan=2,pady=10,padx=10)

        # Button zum Schließen des Programms
        Button(self, text="Beenden", command=master.destroy, bg="light grey").grid(row=8, column=0,columnspan=2, pady=5, padx=10)

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)


def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

def getFolderPath():
    tiles_path=filedialog.askdirectory()
    anwendung.folderPath.set(tiles_path)

def download_OSMTiles():
    lat_deg_max = float(anwendung.var_lat_max.get())
    lat_deg_min = float(anwendung.var_lat_min.get())
    lon_deg_max = float(anwendung.var_lon_max.get())
    lon_deg_min = float(anwendung.var_lon_min.get())
    zoom=int(anwendung.var_zoom.get())

    smurl = r"http://a.tile.openstreetmap.de/{0}/{1}/{2}.png"
    xmin, ymax = deg2num(lat_deg_min, lon_deg_max, zoom)
    xmax, ymin = deg2num(lat_deg_max, lon_deg_min, zoom)

    Cluster = Image.new('RGB', ((xmax - xmin + 1) * 256 - 1, (ymax - ymin + 1) * 256 - 1))

    for xtile in range(xmin, xmax + 1):
        for ytile in range(ymin, ymax + 1):
            try:
                url = smurl.format(zoom, xtile, ytile)
                print(url)
                osm_request=requests.get(url)
                tile_path=str(anwendung.folderPath.get())+"/"+str(zoom)+"_"+str(xtile)+"_"+str(ytile)+".png"
                tile_img=open(tile_path,"wb")
                tile_img.write(osm_request.content)
                tile_img.close()
                tile=Image.open(tile_path)
                print("Download abgeschlossen")
                Cluster.paste(tile, box=((xtile - xmin) * 255, (ytile - ymin) * 255))

            except Exception as e:
                print("Download fehlgeschlagen: ",e)

    fig = plt.figure()
    fig.suptitle("Preview")
    fig.patch.set_facecolor('white')
    plt.imshow(np.asarray(Cluster))
    plt.show()

# Hauptanwendung
if __name__ == "__main__":
    fenster = Tk()
    fenster.title("OSM Tile Downloader")
    anwendung = Anwendung_Karte(fenster)
    fenster.mainloop()