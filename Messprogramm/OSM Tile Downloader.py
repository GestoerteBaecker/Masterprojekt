import matplotlib.pyplot as plt
import math
import requests
from tkinter import *
from PIL import Image
from tkinter import filedialog
import time

# Projektionspackages
from osgeo import gdal,osr
from pyproj import Proj, transform
import rasterio
from rasterio.merge import merge
import rasterio.mask
from rasterio.plot import show
import os

# ACHTUNG: WARNUNG IM MODUL pyproj (wird hier aber ignoriert)
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Code entlehnt aus https://stackoverflow.com/questions/28476117/easy-openstreetmap-tile-displaying-for-python

class Anwendung_Download(Frame):
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
        #self.var_lat_max.set('53.1438') # Campus-Gelände
        self.var_lat_max.set('53.11984') # Tweelbäker See
        Label(self, text="Lat1 in Grad").grid(row=1, column=0)
        self.lat_max=Entry(self,textvariable=self.var_lat_max).grid(row=2,column=0, padx=5)

        self.var_lon_max=StringVar()
        #self.var_lon_max.set('8.198') # Campus-Gelände
        self.var_lon_max.set('8.2746') # Tweelbäker See
        Label(self, text="Lon1 in Grad").grid(row=1, column=1)
        self.lon_max=Entry(self,textvariable=self.var_lon_max).grid(row=2,column=1, padx=5)

        self.var_lat_min=StringVar()
        #self.var_lat_min.set('53.141') # Campus-Gelände
        self.var_lat_min.set('53.1063') # Tweelbäker See
        Label(self, text="Lat2 in Grad").grid(row=3, column=0,pady=(10,0))
        self.lat_min=Entry(self,textvariable=self.var_lat_min).grid(row=4,column=0, padx=5)

        self.var_lon_min=StringVar()
        #self.var_lon_min.set('8.2036') # Campus-Gelände
        self.var_lon_min.set('8.2886') # Tweelbäker See
        Label(self, text="Lon2 in Grad").grid(row=3, column=1,pady=(10,0))
        self.lon_min=Entry(self,textvariable=self.var_lon_min).grid(row=4,column=1, padx=5)

        self.var_zoom=StringVar()
        self.var_zoom.set('18')
        Label(self, text="Zoomstufe:").grid(row=5, column=0,pady=10)
        self.zoom=Entry(self,textvariable=self.var_zoom).grid(row=5,column=1, padx=5,pady=10)

        self.folderPath = StringVar()
        self.save_button=Button(self, text="Speichern unter...",command=lambda:getFolderPath())
        self.save_button.grid(row=6,column=0, columnspan=2,pady=10,padx=10)

        bulk_download_button=Button(self, text="Download!",command=lambda:download_OSMTiles())
        bulk_download_button.grid(row=7,column=0, columnspan=2,pady=10,padx=10)

        # Button zum Schließen des Programms
        Button(self, text="Beenden", command=master.destroy, bg="light grey").grid(row=8, column=0,columnspan=2, pady=5, padx=10)

# Umrechnung von Lat und Lon zu Kachelnummern
def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)

# Umrechnung von Kachelnummern zu Lat und Lon
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
    all_tiff_files=[]
    xtiles=[]
    ytiles=[]
    lat_deg_max = float(anwendung.var_lat_max.get())
    lat_deg_min = float(anwendung.var_lat_min.get())
    lon_deg_max = float(anwendung.var_lon_max.get())
    lon_deg_min = float(anwendung.var_lon_min.get())
    zoom=int(anwendung.var_zoom.get())

    # Berechnung der Größe eines Pixels bei dem gegebenen Breitengrad (hier für mittlere Breite)
    lat_deg_mitte = lat_deg_min+(lat_deg_max-lat_deg_min)/2
    res = 156543.03 * math.cos(lat_deg_mitte / 180 * math.pi) / (2 ** zoom)

    smurl = r"http://a.tile.openstreetmap.de/{0}/{1}/{2}.png"
    xmin, ymax = deg2num(lat_deg_min, lon_deg_max, zoom)
    xmax, ymin = deg2num(lat_deg_max, lon_deg_min, zoom)


    for xtile in range(xmin, xmax + 1):
        for ytile in range(ymin, ymax + 1):
            try:
                url = smurl.format(zoom, xtile, ytile)
                print(url)
                osm_request=requests.get(url)
                tile_path=str(anwendung.folderPath.get())+"/"+str(zoom)+"_"+str(xtile)+"_"+str(ytile)
                original_tile_img=open(tile_path+".png","wb")
                original_tile_img.write(osm_request.content)
                original_tile_img.close()

                xtiles.append(xtile)
                ytiles.append(ytile)

                # Umwandlung von Palette zu RGB
                original_tile=Image.open(tile_path+".png")
                RGB_tile=Image.new('RGB',original_tile.size)
                RGB_tile.paste(original_tile)
                RGB_tile.save(tile_path+"_RGB.png")
                RGB_tile.close()

                print("Download abgeschlossen\n")

                # Kachelnummer in Breite / Länge umrechnen (EPSG 4326)
                lat_tile, lon_tile = num2deg(xtile, ytile, zoom)

                # Umrechnung von Lat und Lon in kartesische Koordinaten (4326 zu 3857)
                osm_deg_proj = Proj("epsg:4326")  # Input-Proj
                osm_kart_proj = Proj("epsg:3857")  # Output-Proj

                # Kachelnummern im EPSG 3857 (als kartesische Koordinaten im WGS84)
                xtile_3857, ytile_3857 = transform(osm_deg_proj, osm_kart_proj, lat_tile, lon_tile)

                RGB_tile_path=tile_path+"_RGB.png"
                RGB_tile=gdal.Open(RGB_tile_path)
                RGB_tile_3857_path=str(anwendung.folderPath.get())+"/"+str(zoom)+"_"+str(int(xtile_3857))+"_"+str(int(ytile_3857))+".tiff"

                # Georeferenzierung mittels GTiff
                driver = gdal.GetDriverByName('GTIFF')
                options = ['PHOTOMETRIC=RGB', 'PROFILE=GeoTIFF']

                # Angabe des Zielpfades und Öffnen der Eingangsdatei als Kopie
                RGB_tile_3857 = driver.CreateCopy( RGB_tile_3857_path, RGB_tile, 0, options=options)

                # Specify raster location through geotransform array
                # (uperleftx, scalex, skewx, uperlefty, skewy, scaley)
                gt = [xtile_3857, res*5/3, 0, ytile_3857, 0, -res*5/3]

                # Speichern des Ausgaberasters mit Georeferenzierung
                RGB_tile_3857.SetGeoTransform(gt)

                # Get raster projection
                epsg = 3857
                srs = osr.SpatialReference()
                srs.ImportFromEPSG(epsg)
                dest_wkt = srs.ExportToWkt()

                # Projektion setzen
                RGB_tile_3857.SetProjection(dest_wkt)

                all_tiff_files.append(RGB_tile_3857_path)

                # Schließen der Raster
                del RGB_tile
                del RGB_tile_3857

                # Löschen der nicht benötigten Dateien
                os.remove(tile_path + "_RGB.png")
                os.remove(tile_path+".png")

                time.sleep(0.1)

            except Exception as e:
                print("Download fehlgeschlagen: ",e)

    # Lesen der Metadaten der ersten Kachel
    with rasterio.open(all_tiff_files[0]) as src0:
        meta_data = src0.meta

        del src0

    tiff_to_mosaic=[]

    # Iteration über alle geladenen Tiff-Kacheln
    for tiff in all_tiff_files:
        rasterio_tiff=rasterio.open(tiff)
        # Hinzufügen zur Liste der zusammenzufügenden Tiffs
        tiff_to_mosaic.append(rasterio_tiff)

        del rasterio_tiff

    # Merge-Befehl
    mosaic, mos_trans = merge(tiff_to_mosaic)

    # Update der Metadaten
    meta_data.update({"driver": "GTiff",
                     "height": mosaic.shape[1],
                     "width": mosaic.shape[2],
                     "transform": mos_trans})

    name_x=str(min(xtiles))
    name_y=str(max(ytiles))
    mosaic_3857_path=str(anwendung.folderPath.get())+"/"+str(zoom)+"_"+name_x+"_"+name_y+"_"+"Mosaic_3857.tiff"

    # Speichern des Rasters
    with rasterio.open(mosaic_3857_path, "w", **meta_data) as dest:
        dest.write(mosaic)

    # Lesen des Rasters und Projizieren in UTM-Koordinaten (EPSG 25832)
    mosaic_3857 = gdal.Open(mosaic_3857_path)
    mosaic_25832_path = str(anwendung.folderPath.get())+"/"+str(zoom)+"_"+name_x+"_"+name_y+"_"+"Mosaic_25832.tiff"
    gdal.Warp(mosaic_25832_path,mosaic_3857,dstSRS='EPSG:25832')


    print("Projizierung nach EPSG 25832 abgeschlossen")

    # Löschen der nicht-benötigten Dateien
    del mosaic_3857
    del tiff_to_mosaic
    for tiff in all_tiff_files:
        os.remove(tiff)
    os.remove(mosaic_3857_path)

    rasterio_tiff = rasterio.open(mosaic_25832_path)
    figure, ax = plt.subplots()
    show(rasterio_tiff, adjust='None',ax=ax)
    #ax.plot([446497.524],[5888479.012], marker='o',markersize=5, color="red")
    plt.show()

# Hauptanwendung
if __name__ == "__main__":
    fenster = Tk()
    fenster.title("OSM Tile Downloader")
    anwendung = Anwendung_Download(fenster)
    fenster.mainloop()


