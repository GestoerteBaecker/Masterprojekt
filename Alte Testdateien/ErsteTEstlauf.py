from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
print "Start simulator (SITL)"
import dronekit_sitl
sitl = dronekit_sitl.start_default()
connection_string = sitl.connection_string()

#print connection_string
# -- Connect to the vehicle
#import argparse

#parser = argparse.ArgumentParser(description='commands')
#parser.add_argument('--connect')
#args = parser.parse_args()

#connection_string = args.connect
print connection_string

print("Connection to the vehicle on %s" % connection_string)
vehicle = connect(connection_string, wait_ready=True)



while vehicle.is_armable == False:
    # Get some vehicle attributes (state)
    print "Get some vehicle attribute values:"
    print " GPS: %s" % vehicle.gps_0
    print " Battery: %s" % vehicle.battery
    print " Last Heartbeat: %s" % vehicle.last_heartbeat
    print (" Is Armable?: %s" % vehicle.is_armable)
    print " System status: %s" % vehicle.system_status.state
    print " Mode: %s" % vehicle.mode.name  # settable
    print vehicle.location.global_relative_frame.alt
    time.sleep(1)

vehicle.initialize()
vehicle.mode = VehicleMode('GUIDED')
vehicle.simple_takeoff(10)

while True:
    # Get some vehicle attributes (state)
    print "Get some vehicle attribute values:"
    print " GPS: %s" % vehicle.gps_0
    print " Battery: %s" % vehicle.battery
    print " Last Heartbeat: %s" % vehicle.last_heartbeat
    print " Is Armable?: %s" % vehicle.is_armable
    print " System status: %s" % vehicle.system_status.state
    print " Mode: %s" % vehicle.mode.name  # settable
    print vehicle.location.global_relative_frame.alt
    time.sleep(1)

"""
# -- Define the function for takeoff
def arm_and_takeoff(tgt_altitude):
    print("Arming motors")

    while not vehicle.is_armable:
        time.sleep(1)

    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed: time.sleep(1)

    print("Takeoff")
    vehicle.simple_takeoff(tgt_altitude)

    # -- wait to reach the target altitude
    while True:
        altitude = vehicle.location.global_relative_frame.alt

        if altitude >= tgt_altitude - 1:
            print("Altitude reached")
            break

        time.sleep(1)


# ------ MAIN PROGRAM ----
arm_and_takeoff(10)

# -- set the default speed
vehicle.airspeed = 7

# -- Go to wp1
print ("go to wp1")
wp1 = LocationGlobalRelative(35.9872609, -95.8753037, 10)

vehicle.simple_goto(wp1)

# --- Here you can do all your magic....
time.sleep(30)

# --- Coming back
print("Coming back")
vehicle.mode = VehicleMode("RTL")

time.sleep(20)

# -- Close connection
vehicle.close()


"""