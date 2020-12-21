from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import tkinter.ttk as ttk
import sys, os
import time

# Import der aufzurufenden Skripte
import Karte
import Simulation
import Boot

# Klasse, die als Softwareverteilung dient und jedes weitere Unterprogramm per Buttondruck bereithält
class Anwendung(Frame):
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
        randabstand = 10
        self.master.geometry('+%d+%d' % (randabstand, randabstand))
        self.karte_window=None

        # Überschrift
        Label(self,text="EchoBoat Autopilot-Monitor",font='Helvetica 12 bold').grid(row=0,column=0,columnspan=8,pady=10)


        # OptionMenu, ob eine Simulation vorliegt
        # Einführen einer Variablen für ein OptionMenu
        self.__om_variable_sim = StringVar(self)
        self.__om_variable_sim.set("Simulation")

        # OptionMenu, ob Vorwissen existiert
        # Einführen einer Variablen für ein OptionMenu
        self.__om_variable_mode = StringVar(self)
        self.__om_variable_mode.set("Vollautomatisch")

        # OptionMenu zur Auswahl der Simulation und Erkundungsmethode
        self.om = OptionMenu(self, self.__om_variable_mode, *["Vollautomatisch", "Teilautomatisch"], command=self.modusabfrage)
        self.om.grid(row=1, column=2,padx=10,sticky="ew")
        self.om = OptionMenu(self, self.__om_variable_sim, *["Simulation", "Reale Daten"], command=self.simulationsabfrage)
        self.om.grid(row=1, column=3,padx=10,sticky="ew")

        # Button zum Öffnen der Karte
        button_open_map=Button(self, text="Karte öffnen...", command=lambda: self.karte_laden())
        button_open_map.grid(row=1, column=0, columnspan=2, sticky="we", padx=(30,10), pady=10)

        # Verbindung, Erkundung und Vermessung
        button_verbinden=Button(self, text="Verbinden", command=lambda: self.boot_verbinden(),width=14,font='Helvetica 9 bold')
        button_verbinden.grid(row=2, column=0, columnspan=2, sticky="we", padx=(30,10), pady=(20,10))
        button_daten_lesen=Button(self, text="Auslesen", command=lambda: self.boot_daten_lesen(),width=14)
        button_daten_lesen.grid(row=2, column=2, sticky="we", padx=10, pady=(20,10))
        button_db_starten=Button(self, text="in DB schreiben", command=lambda: self.boot_db_starten(),width=14)
        button_db_starten.grid(row=2, column=3,sticky="we", padx=10, pady=(20,10))
        button_erkunden=Button(self, text="Erkunden", command=lambda: self.boot_erkunden(),width=14,font='Helvetica 9 bold')
        button_erkunden.grid(row=3, column=0, columnspan=2, sticky="we", padx=(30,10), pady=10)

        # Label der Verbindungsqualität
        Label(self,text="Status").grid(row=4,column=0,pady=(10,0))
        self.con_qual_gnss1=Label(self, bg="red",width=3,height=2,relief="groove")
        self.con_qual_gnss1.grid(row=5, column=0, pady=10, padx=5)
        self.con_qual_gnss2=Label(self, bg="red",width=3,height=2,relief="groove")
        self.con_qual_gnss2.grid(row=6, column=0, pady=10, padx=5)
        self.con_qual_echolot=Label(self, bg="red",width=3,height=2,relief="groove")
        self.con_qual_echolot.grid(row=7, column=0, pady=10, padx=5)
        self.con_qual_dimetix=Label(self, bg="red",width=3,height=2,relief="groove")
        self.con_qual_dimetix.grid(row=8, column=0, pady=10, padx=5)
        self.con_qual_pixhawk4=Label(self, bg="red",width=3,height=2,relief="groove")
        self.con_qual_pixhawk4.grid(row=9, column=0, pady=10, padx=5)
        #self.con_qual_imu=Label(self, bg="red",width=3,height=2,relief="groove")
        #self.con_qual_imu.grid(row=11, column=0, pady=10, padx=5)

        # Label der Instrumentnamen
        Label(self,text="Instrument",width=14).grid(row=4,column=1,pady=(10,0))
        label_gnss1=Label(self, text="GNSS1",bg="lightgrey",height=2,relief="groove")
        label_gnss1.grid(row=5, column=1, pady=5, sticky=W+E)
        label_gnss2=Label(self, text="GNSS2",bg="lightgrey",height=2,relief="groove")
        label_gnss2.grid(row=6, column=1, sticky=W+E)
        label_echolot=Label(self, text="Echolot",bg="lightgrey",height=2,relief="groove")
        label_echolot.grid(row=7,column=1, sticky=W+E)
        label_dimetix=Label(self, text="Dimetix",bg="lightgrey",height=2,relief="groove")
        label_dimetix.grid(row=8, column=1, sticky=W+E)
        label_pixhawk4=Label(self, text="Pixhawk4",bg="lightgrey",height=2,relief="groove")
        label_pixhawk4.grid(row=9, column=1, sticky=W+E)
        #label_imu=Label(self, text="IMU",bg="lightgrey",height=2,relief="groove")
        #label_imu.grid(row=11, column=1, sticky=W+E)

        # Label der empfangenen Messwerte
        Label(self,text="aktuelle Daten",width=14).grid(row=4,column=2,pady=(20,0))
        #Label(self,text="-/-").grid(row=11,column=2)

        self.var_current_state1=StringVar()
        self.var_current_state1.set("No Data")
        self.current_state1=Entry(self,state="readonly",textvariable=self.var_current_state1,justify="center")
        self.current_state1.grid(row=5, column=2, padx=(0,10), ipady=8)

        self.var_current_state2=StringVar()
        self.var_current_state2.set("No Data")
        self.current_state2=Entry(self,state="readonly",textvariable=self.var_current_state2,justify="center")
        self.current_state2.grid(row=6, column=2, padx=(0,10), ipady=8)

        self.var_current_depth=StringVar()
        self.var_current_depth.set("No Data")
        self.current_depth=Entry(self,state="readonly",textvariable=self.var_current_depth,justify="center")
        self.current_depth.grid(row=7, column=2, padx=(0,10), ipady=8)

        self.var_current_distance=StringVar()
        self.var_current_distance.set("No Data")
        self.current_distance=Entry(self, state="readonly",textvariable=self.var_current_distance,justify="center")
        self.current_distance.grid(row=8, column=2, padx=(0,10), ipady=8)

        self.var_current_px4=StringVar()
        self.var_current_px4.set("No Data")
        self.current_px4=Entry(self, state="readonly", textvariable = self.var_current_px4, justify = "center")
        self.current_px4.grid(row=9, column=2, padx=(0,10), ipady=8)

        # Verbindung, Erkundung und Vermessung
        button_latestDB=Button(self, text="Letzter DB-Eintrag", command=lambda: self.boot_letzter_Eintrag(),width=14)
        button_latestDB.grid(row=11, column=0, columnspan=2, sticky="we", padx=(30,10), pady=20)
        button_rtl=Button(self, text="RTL", command=lambda: self.Boot_RTL(),width=14)
        button_rtl.grid(row=11, column=2, sticky="we", padx=10, pady=20)
        button_stopp=Button(self, text="NOT-STOPP", command=lambda: self.boot_stopp(), width=14,bg="darkred",fg="white",font="Helvetica 10 bold")
        button_stopp.grid(row=11, column=3, sticky="we", padx=10, pady=20)


        # Button zum Schließen des Programms
        Button(self, text="Beenden", command=lambda: self.alles_schliessen(), bg="light grey").grid(row=12, column=2,pady=5, padx=10, sticky=W + E)
        Button(self, text="Trennen", command=lambda: self.boot_trennen(),width=14).grid(row=12, column=0, columnspan=2,pady=5, padx=(30,10), sticky=W + E)


        # Einfügen von Separatoren zur besseren Lesbarkeit zwischen den Zeilen
        self.line_style = ttk.Style()
        self.line_style.configure("Line.TSeparator", background="#000000")
        ttk.Separator(self, orient=VERTICAL).grid(row=1, column=1, columnspan=2, sticky='ns',pady=5,padx=(0,40))
        ttk.Separator(self, orient=VERTICAL).grid(row=1, column=2, columnspan=2, sticky='ns',pady=5, padx=(10,0))
        ttk.Separator(self, orient=HORIZONTAL,style="Line.TSeparator").grid(row=1, column=0, columnspan=4, rowspan=2, sticky='ew')
        ttk.Separator(self, orient=HORIZONTAL,style="Line.TSeparator").grid(row=3, column=0, columnspan=4, rowspan=2, sticky='ew',pady=(15,0))
        ttk.Separator(self, orient=HORIZONTAL).grid(row=5, column=0, columnspan=3, rowspan=2, sticky='ew')
        ttk.Separator(self, orient=HORIZONTAL).grid(row=6, column=0, columnspan=3, rowspan=2, sticky='ew')
        ttk.Separator(self, orient=HORIZONTAL).grid(row=7, column=0, columnspan=3, rowspan=2, sticky='ew')
        ttk.Separator(self, orient=HORIZONTAL).grid(row=8, column=0, columnspan=3, rowspan=2, sticky='ew')
        #ttk.Separator(self, orient=HORIZONTAL).grid(row=10, column=0, columnspan=3, rowspan=2, sticky='ew')
        ttk.Separator(self, orient=HORIZONTAL,style="Line.TSeparator").grid(row=9, column=0, columnspan=4, rowspan=3, sticky='ew')


        # Abrufen der neuesten Daten und Stati
        self.verbindung_initialisiert=False
        self.status_und_daten_aktualisieren()
        self.t=0


    def karte_laden(self):
        # Öffnen der Datei
        geotiff_path = filedialog.askopenfilename(filetypes=[("GeoTiff","*.tiff"),("OSM-Tile", "*.png")])
        try:
            self.position=(self.winfo_width()+self.master.winfo_x()+10,self.master.winfo_y())
            self.karte_window=Karte.Anwendung_Karte(self,self.position,geotiff_path,self.__om_variable_mode.get())
        except:
            print("Dateien ungültig")


    def simulationsabfrage(self, x):
        print(x)

    def modusabfrage(self, x):
        print(x)

    def boot_verbinden(self):
        try:
            self.verbindung_initialisiert = True
            if self.__om_variable_sim.get() == "Reale Daten":
                self.boot = Boot.Boot()
            elif self.__om_variable_sim.get() == "Simulation":
                self.boot = Simulation.Boot_Simulation()

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            messagebox.showerror(title="Verbindungsfehler!", message=("Verbindung zu den Sensoren konnte nicht hergestellt werden: "+str(e)+"\nTyp: "+str(exc_type)+"\nName: "+str(fname)+"\nZeile: "+str(exc_tb.tb_lineno)))

    def boot_daten_lesen(self):
        try:
            self.datenlesen_initialisiert=True
            self.boot.Datenaktualisierung()

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            messagebox.showerror(title="Fehler beim Daten lesen!", message=("Lesen der Daten konnte nicht initialisiert werden: "+str(e)+"\nTyp: "+str(exc_type)+"\nName: "+str(fname)+"\nZeile: "+str(exc_tb.tb_lineno)))


    def boot_db_starten(self):
        self.boot.Datenbank_beschreiben()

    def boot_erkunden(self):
        self.boot.Erkunden(self.__om_variable_mode.get())

    def boot_stopp(self):
        # TODO: Aktivieren des Loiter-Modus im Pixhawk. Veranlasst den aktuellen Punkt zu halten
        pass

    def boot_trennen(self):
        self.boot.Trennen() #TODO: das hier muss beim Verlassen unbedingt aufgerufen werden!!!

    def status_und_daten_aktualisieren(self):
        # Anzahl der Durchläufe für die Bootsroute
        t = time.time()
        if self.verbindung_initialisiert==True:
            self.t+=1
            if self.boot.PixHawk.verbindung_hergestellt==True:
                modus=str(self.boot.PixHawk.vehicle.mode).split(":")[1]
                self.con_qual_pixhawk4.config(bg="orange")

                if self.boot.PixHawk.vehicle.armed==False:armed="DISARMED"

                elif self.boot.PixHawk.vehicle.armed==True: armed="ARMED"

                self.var_current_px4.set(armed+"  |  "+modus)

                if modus=="GUIDED" and armed=="ARMED":
                    self.con_qual_pixhawk4.config(bg="green")
            else:
                self.con_qual_pixhawk4.config(bg="red")
                self.var_current_px4.set("No Data")

            # E C H T E  D A T E N  G N S S 1
            if "GNSS1" in self.boot.Sensornamen:
                index = self.boot.Sensornamen.index("GNSS1")
                gnss = self.boot.Sensorliste[index]
                if gnss.verbindung_hergestellt:
                    try:
                        gnss_qual_indikator = self.boot.AktuelleSensordaten[0].daten[4]
                        gnss_north,gnss_east = self.boot.AktuelleSensordaten[0].daten[0],self.boot.AktuelleSensordaten[0].daten[1]
                        gnss_heading = self.boot.heading

                        if gnss_qual_indikator==4:
                            if not gnss.simulation:
                                self.con_qual_gnss1.config(bg="green")
                            else:
                                self.con_qual_gnss1.config(bg="green")
                            self.var_current_state1.set("RTK fix")
                        elif gnss_qual_indikator==5:
                            if not gnss.simulation:
                                self.con_qual_gnss1.config(bg="yellow")
                            else:
                                self.con_qual_gnss1.config(bg="yellow")
                            self.var_current_state1.set(str(gnss_qual_indikator)+": RTK float")
                        else:
                            self.var_current_state1.set(str(gnss_qual_indikator)+": kein RTK")
                            if not gnss.simulation:
                                self.con_qual_gnss1.config(bg="yellow")
                            else:
                                self.con_qual_gnss1.config(bg="yellow")
                        if self.karte_window!= None:
                            try:
                                kanten = self.boot.KantenPlotten()
                                self.karte_window.karte_updaten(gnss_north, gnss_east, gnss_heading, self.t, kanten)

                            except:
                                print("Karte kann nicht aktualisiert werden.")
                    except:
                        if not gnss.simulation:
                            self.con_qual_gnss1.config(bg="orange")
                            if self.karte_window: self.karte_window.karte_updaten(None, None, None, None)
                        else:
                            self.con_qual_gnss1.config(bg="orange")
                else:
                    if self.karte_window: self.karte_window.karte_updaten(None, None, None, None)
                    self.con_qual_gnss1.config(bg="red")

            # E C H T E  D A T E N  G N S S 2
            if "GNSS2" in self.boot.Sensornamen:
                index = self.boot.Sensornamen.index("GNSS2")
                gnss2 = self.boot.Sensorliste[index]
                if gnss2.verbindung_hergestellt:  # TODO: Was, wenn nur eine GNSS??
                #if self.datenlesen_initialisiert == True:
                    try:
                        gnss_qual_indikator=self.boot.AktuelleSensordaten[1].daten[4]
                        if gnss_qual_indikator==4:
                            if not gnss2.simulation:
                                self.con_qual_gnss2.config(bg="green")
                            else:
                                self.con_qual_gnss2.config(bg="green")
                            self.var_current_state2.set("RTK fix")
                        elif gnss_qual_indikator==5:
                            if not gnss2.simulation:
                                self.con_qual_gnss2.config(bg="yellow")
                            else:
                                self.con_qual_gnss2.config(bg="yellow")
                            self.var_current_state2.set(str(gnss_qual_indikator)+": RTK float")
                        else:
                            self.var_current_state2.set(str(gnss_qual_indikator)+": kein RTK")
                            if not gnss2.simulation:
                                self.con_qual_gnss2.config(bg="yellow")
                            else:
                                self.con_qual_gnss2.config(bg="yellow")
                    except:
                        if not gnss2.simulation:
                            self.con_qual_gnss2.config(bg="orange")
                        else:
                            self.con_qual_gnss2.config(bg="orange")
                else:
                    self.con_qual_gnss2.config(bg="red")

            # E C H T E  D A T E N  E C H O L O T
            if "Echolot" in self.boot.Sensornamen:
                index = self.boot.Sensornamen.index("Echolot")
                echolot = self.boot.Sensorliste[index]
                if echolot.verbindung_hergestellt:
                    if not echolot.simulation:
                        self.con_qual_echolot.config(bg="orange")
                    else:
                        self.con_qual_echolot.config(bg="orange")
                    try:
                        t1 = round(float(self.boot.AktuelleSensordaten[2].daten[0]),2)
                        t2 = round(float(self.boot.AktuelleSensordaten[2].daten[1]),2)
                        if not echolot.simulation:
                            self.con_qual_echolot.config(bg="green")
                        else:
                            self.con_qual_echolot.config(bg="green")
                        self.var_current_depth.set(str(t1) + "  |  " + str(t2))
                    except:
                        if not echolot.simulation:
                            self.con_qual_echolot.config(bg="orange")
                        else:
                            self.con_qual_echolot.config(bg="orange")
                else:
                    self.con_qual_echolot.config(bg="red")

            # E C H T E  D A T E N  D I M E T I X
            if "Distanz" in self.boot.Sensornamen:
                index = self.boot.Sensornamen.index("Distanz")
                dimetix = self.boot.Sensorliste[index]
                if dimetix.verbindung_hergestellt:
                    if not dimetix.simulation:
                        self.con_qual_dimetix.config(bg="orange")
                    else:
                        self.con_qual_dimetix.config(bg="orange")
                    try:
                        d = self.boot.AktuelleSensordaten[3].daten
                        if not dimetix.simulation:
                            self.con_qual_dimetix.config(bg="green")
                        else:
                            self.con_qual_dimetix.config(bg="green")
                        self.var_current_distance.set(str(round(d,2)))
                    except:
                        if not dimetix.simulation:
                            self.con_qual_dimetix.config(bg="orange")
                        else:
                            self.con_qual_dimetix.config(bg="orange")
                else:
                    self.con_qual_dimetix.config(bg="red")

        schlafen = int(max(0, 100 - (time.time() - t)))
        #print(time.time())
        self.after(schlafen, self.status_und_daten_aktualisieren) # Alle 1 Sekunden wird Befehl ausgeführt

    def alles_schliessen(self):
        if self.verbindung_initialisiert == True: self.boot_trennen()
        if self.karte_window:
            self.karte_window.plt.close()
            self.karte_window=None
        self.master.destroy()

# Hauptanwendung
if __name__ == "__main__":
    hauptfenster = Tk()
    hauptfenster.title("EchoBoat - Autopilot Monitor")
    anwendung = Anwendung(hauptfenster)
    hauptfenster.mainloop()
