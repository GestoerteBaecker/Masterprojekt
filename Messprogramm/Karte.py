import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
plt.ion() # Aktivieren eines dynamischen Plots
import math
import rasterio
from rasterio.plot import show
import csv

# Klasse, die als Softwareverteilung dient und jedes weitere Unterprogramm per Buttondruck bereithält
class Anwendung_Karte():
    # Konstruktor  der GUI der Hauptanwendung zum Öffnen aller weiteren GUIs
    def __init__(self,Monitor,position=0,geotiff_path=None,messmodus="Vollautomatisch"):

        # Übernehmen des Ordnerpfades und Fensterposition
        self.geotiff_path=geotiff_path
        self.position=position
        self.monitor=Monitor
        self.messmodus=messmodus

        # Abschluss der Initialisierung durch erstmaliges Laden der Karte
        self.karte_laden()

    def karte_laden(self):
        self.grenzpolygon_vorhanden = False
        self.richtungslinie_vorhanden = False

        # Darstellen der Karte
        self.plt = plt
        self.figure, self.ax = plt.subplots()
        self.ax.set_xlim((451832, 452100))
        self.ax.set_ylim((5884780, 5885070))
        self.figure.suptitle("Echoboot - Autopilot Navigator")
        self.figure.patch.set_facecolor('white')
        self.figure.canvas.set_window_title('Echoboot - Autopilot Navigator')

        # Zum Abfangen von Fehlern beim Schließen der Karte
        self.figure.canvas.mpl_connect('close_event', self.karte_geschlossen)

        self.cid = self.figure.canvas.mpl_connect('button_press_event', self.onclick)
        self.coords = []

        # Anzeigen der geotiff
        self.geotiff = rasterio.open(self.geotiff_path)
        show(self.geotiff, adjust='None', ax=self.ax)

        # Quadtree von DHM berechnen
        testdaten = open("Testdaten_DHM_Tweelbaeke.txt", "r", encoding='utf-8-sig')  # ArcGIS Encoding :)
        lines = csv.reader(testdaten, delimiter=";")
        id_testdaten = []
        x_testdaten = []
        y_testdaten = []
        tiefe_testdaten = []

        # Lesen der Datei
        for line in lines:
            id_testdaten.append(int(line[0]))
            x_testdaten.append(float(line[1]))
            y_testdaten.append(float(line[2]))
            tiefe_testdaten.append(float(line[3]))
        testdaten.close()

        self.ax.scatter(x_testdaten, y_testdaten, s=1)

        # Variablen für das spätere Boot setzen
        self.boot_position, = self.ax.plot([], [], marker=(3, 0, 0),markersize=10, color="darkblue")
        self.current_boot_heading,=self.ax.plot([],[],':',lw=1, color="darkblue")
        self.grenzpolygon,=self.ax.plot([], [], marker='o',markersize=2, color="red")
        self.richtungslinie,=self.ax.plot([], [], marker='o',markersize=2, color="red")
        self.boot_streifen, = self.ax.plot([], [], ':', lw=1, color="black")
        #self.boot_allekanten=[\
           #self.ax.plot([],[],'-',lw=1, color="black")[0],\
           # self.ax.plot([],[],'-',lw=1, color="grey")[0],\
           # self.ax.plot([],[],'-',lw=1, color="lightgrey")[0]]
        self.grenzpolygon_x,self.grenzpolygon_y=[],[]
        self.richtungslinie_x,self.richtungslinie_y=[],[]
        self.boot_allekanten = LineCollection([], linewidths=1, colors="grey")
        self.ax.add_collection(self.boot_allekanten)

        # Anlegen von LineCollections um durch Farben den momentanen Tracking-Zustand anzudeuten
        # leere Liste für jeden Tracking Zustand
        self.profilroute=[]
        self.verbindungsroute=[]
        self.blindfahrtroute=[]
        self.alter_modus=None
        self.letzter_routenpunkt=None
        #Start-Index für jede Liste (wird beim ersten Benutzen auf 0 gesetzt)
        self.verbindung_index,self.profil_index,self.blindfahrt_index=-1,-1,-1
        # Anlegen der leeren LineCollection
        self.profilroute_lc = LineCollection([], linewidths=1, colors='red', linestyle='solid')
        self.verbindungsroute_lc = LineCollection([], linewidths=1, colors='orange', linestyle='solid')
        self.blindfahrtroute_lc = LineCollection([], linewidths=1, colors='black', linestyle='dotted')
        # Hinzufügen der LCs zu dem zu aktualisierenden Plot
        self.ax.add_collection(self.profilroute_lc)
        self.ax.add_collection(self.verbindungsroute_lc)
        self.ax.add_collection(self.blindfahrtroute_lc)


        # Abfragen und Setzen der Fenster-Position
        thismanager=self.plt.get_current_fig_manager()
        positionx,positiony=self.position
        #TODO: Positionierung nachgucken
        #thismanager.window.wm_geometry("+"+str(positionx)+"+"+str(positiony))

    def karte_updaten(self,gnss_north,gnss_east,gnss_heading,t,kanten, streifen, trackingmodus):
        # Setzen einer leeren Variable für die Boot-Position
        update_interval = 1

        # Plotten der aktuellen Boot-Position inklusive Heading
        self.plot_boot(gnss_north,gnss_east,gnss_heading)

        # Alle 10 Durchläufe soll die Route ergänzt werden
        if t and t % update_interval == 0:
            self.plot_bootroute(gnss_north,gnss_east, trackingmodus)

        #if kanten[0].startpunkt:
        #    self.plot_kanten(kanten) # TODO: Hier stürzt irgendwas ab
        if kanten != []:
            self.plot_kanten(kanten)

        if streifen != []:
            self.plot_streifen(streifen)

        # Plotten der aktuellen Wegpunkte
        # self.plot_waypoint()

    def plot_boot(self,gnss_north,gnss_east,gnss_heading):
        try:
            # Einlesen der aktuellen Boot-Daten

            # Setzen der Punkte im Plot auf neue Werte
            self.current_boot_heading.set_xdata([gnss_north, gnss_north + math.sin(gnss_heading*math.pi/200) * 10000])
            self.current_boot_heading.set_ydata([gnss_east, gnss_east + math.cos(gnss_heading*math.pi/200) * 10000])
            self.boot_position.set_xdata(gnss_north)
            self.boot_position.set_ydata(gnss_east)
            self.boot_position.set_marker(marker=(3,0,-gnss_heading*180/200))

        # Wenn keine GPS-Daten vorhanden, Fehlermeldung ausgeben
        except:
            self.ax.text(.5, .5,'NO GPS DATA', horizontalalignment='center',
                            verticalalignment='center', size=15, color="red",transform=self.ax.transAxes)

    def plot_streifen(self,streifen):
        sanfang_x = streifen.startpunkt.x
        sanfang_y = streifen.startpunkt.y
        sende_x = streifen.endpunkt.x
        sende_y = streifen.endpunkt.y

        self.boot_streifen.set_xdata([sanfang_x, sende_x])
        self.boot_streifen.set_ydata([sanfang_y, sende_y])

    def plot_kanten(self, kanten):
        temp_kanten = []
        for kante in kanten:
            """
            kanfang_x = kante.Anfangspunkt.x
            kanfang_y = kante.Anfangspunkt.y
            kende_x = kante.Endpunkt.x
            kende_y = kante.Endpunkt.y
            """
            kanfang_x = kante.Anfangspunkt.x
            kanfang_y = kante.Anfangspunkt.y
            kende_x = kante.Endpunkt.x
            kende_y = kante.Endpunkt.y

            #self.boot_allekanten[i].set_xdata([kanfang_x,kende_x])
            #self.boot_allekanten[i].set_ydata([kanfang_y,kende_y])
            temp_kanten.append([(kanfang_x, kanfang_y), (kende_x, kende_y)])
            #self.ax.plot([kanfang_x,kende_x],[kanfang_y,kende_y],lw=1,color='black')
            #kante.gewicht
        self.boot_allekanten.set_segments(temp_kanten)


    # TODO: Funktion definieren
    def plot_waypoint(self):
        x=1

    def plot_bootroute(self, gnss_north, gnss_east, trackingmodus):
        if trackingmodus == "TrackingMode.VERBINDUNG":
            # Prüfen, ob ein einer Modus vorherrscht
            # wenn ja, dann muss die Linie in einen Index geschrieben werden
            if trackingmodus != self.alter_modus:
                # Zum Verhindern von Lücken wird der letzte Punkt der vorangehenden Linie mit übergeben
                # Falls ein Punkt vorhanden, soll dieser als Stadt der neuen Linie gelten
                if self.letzter_routenpunkt:
                    self.verbindungsroute.append([self.letzter_routenpunkt])
                    self.verbindung_index += 1
                    self.verbindungsroute[self.verbindung_index].append((gnss_north, gnss_east))
                # Falls vorher keine Linie vorhanden, soll der erste Punkt der Linienbeginn sein
                else:
                    self.verbindungsroute.append([(gnss_north, gnss_east)])
                    self.verbindung_index += 1

                # Setzen des alten Modus auf den aktuellen Modus für die Modus-Abfrage
                self.alter_modus = trackingmodus

            # wenn der Modus identisch ist zur Schleife davor, kann der aktuelle Punkt einfach hinzugefügt werden
            else:
                self.verbindungsroute[self.verbindung_index].append((gnss_north, gnss_east))
                self.verbindungsroute_lc.set_segments(self.verbindungsroute)
                self.alter_modus = trackingmodus
                self.letzter_routenpunkt=(gnss_north, gnss_east)

        elif trackingmodus == "TrackingMode.PROFIL":
            if trackingmodus != self.alter_modus:
                if self.letzter_routenpunkt:
                    self.profilroute.append([self.letzter_routenpunkt])
                    self.profil_index += 1
                    self.profilroute[self.profil_index].append((gnss_north, gnss_east))
                else:
                    self.profilroute.append([(gnss_north, gnss_east)])
                    self.profil_index += 1

                self.alter_modus = trackingmodus

            # Setzen der Route erst, wenn eine Linie gezogen werden kann (also 2 Punkte verfügbar sind)
            else:
                self.profilroute[self.profil_index].append((gnss_north, gnss_east))
                self.profilroute_lc.set_segments(self.profilroute)
                self.alter_modus = trackingmodus
                self.letzter_routenpunkt=(gnss_north, gnss_east)

        elif trackingmodus == "TrackingMode.BLINDFAHRT" or "TrackingMode.UFERERKENNUNG":
            if trackingmodus != self.alter_modus:
                if self.letzter_routenpunkt:
                    self.blindfahrtroute.append([self.letzter_routenpunkt])
                    self.blindfahrt_index += 1
                    self.blindfahrtroute[self.blindfahrt_index].append((gnss_north, gnss_east))
                else:
                    self.blindfahrtroute.append([(gnss_north, gnss_east)])
                    self.blindfahrt_index += 1
                self.alter_modus = trackingmodus

            # Setzen der Route erst, wenn eine Linie gezogen werden kann (also 2 Punkte verfügbar sind)
            else:
                self.blindfahrtroute[self.blindfahrt_index].append((gnss_north, gnss_east))
                self.blindfahrtroute_lc.set_segments(self.blindfahrtroute)
                self.alter_modus = trackingmodus
                self.letzter_routenpunkt=(gnss_north, gnss_east)

        else:
            self.alter_modus = None

    # Funktion registriert Klick-Events
    def onclick(self,event):
        # Rechtsklick soll vorliegen
        if str(event.button)=='MouseButton.RIGHT':
            ix, iy = event.xdata, event.ydata

            # Vollautomatischer Modus benötigt keine Richtungslinie, daher kann das Vorhandensein auf True gesetzt werden
            if self.messmodus=="Vollautomatisch":
                self.richtungslinie_vorhanden = True

            # Punkte nur hinzufügen, wenn noch kein Polygon existiert
            if self.grenzpolygon_vorhanden==False:

                # Rechter Doppelklick soll Polygon schließen
                if event.dblclick==True:
                    self.grenzpolygon_x_utm32=[] # Für die Weitergabe an Pixhawk (GeoFence)
                    self.grenzpolygon_x.append(self.grenzpolygon.get_xdata()[0])
                    self.grenzpolygon_y.append(self.grenzpolygon.get_ydata()[0])
                    self.grenzpolygon.set_xdata(self.grenzpolygon_x)
                    self.grenzpolygon.set_ydata(self.grenzpolygon_y)
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

            # Wenn Polygon vorhanden, kann, falls noch nicht erfolgt, die Richtungslinie gezeichnet werden
            elif self.richtungslinie_vorhanden == False:
                # Beenden der Linie bei Doppelklick
                if event.dblclick==True:
                    self.richtungslinie.set_color('green')
                    self.richtungslinie_vorhanden=True

                # Ergänzen der Linie bei einfachem Rechtsklick
                else:
                    self.richtungslinie_x.append(ix)
                    self.richtungslinie_y.append(iy)
                    self.richtungslinie.set_xdata(self.richtungslinie_x)
                    self.richtungslinie.set_ydata(self.richtungslinie_y)

            #if self.messmodus == "Teilautomatisch" and self.grenzpolygon_vorhanden == True and self.richtungslinie_vorhanden == True:


            # Erneuter Doppelklick löscht bestehende Formen
            else:
                if event.dblclick==True:
                    self.grenzpolygon.set_xdata([])
                    self.grenzpolygon.set_ydata([])
                    self.richtungslinie.set_xdata([])
                    self.richtungslinie.set_ydata([])
                    self.richtungslinie_x, self.richtungslinie_y = [], []
                    self.grenzpolygon_x, self.grenzpolygon_y = [], []
                    self.grenzpolygon.set_color('red')
                    self.richtungslinie.set_color('red')
                    self.grenzpolygon_vorhanden=False
                    self.richtungslinie_vorhanden=False

    def karte_geschlossen(self,evt):
        self.monitor.karte_window = None