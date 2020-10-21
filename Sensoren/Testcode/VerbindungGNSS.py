
import serial 
import pynmea2
import utm
import time

try:

    ser = serial.Serial('COM6',baudrate=115200)

    # es werden die Formate RMC und GGA ausgegeben
    while True:

        nmea = ser.readline()
        nmea = nmea.decode("utf-8")
        nmeaobjekt = pynmea2.parse(nmea)
        typ = nmeaobjekt.sentencetype
        if typ == "GGA":
            x = utm.fromlatlon(nmeaobjekt.latitude,nmeaobjekt.longitude)
            t = nmeaobjekt.timestamp-time.time
            print(t)

        #if typ == "RMC":
            #print("RMC",nmeaobjekt.latitude)


except:
    print("COM ist blockiert")
```