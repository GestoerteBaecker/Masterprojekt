import pymavlink, pymavlink.mavutil

# Start a connection listening to a UDP port
the_connection = pymavlink.mavutil.mavlink_connection('udpin:localhost:14540')

# Wait for the first heartbeat
#   This sets the system and component ID of remote system for the link
the_connection.wait_heartbeat()
print("Heartbeat from system (system %u component %u)" % (the_connection.target_system, the_connection.target_system))

# Once connected, use 'the_connection' to get and send messages

# Verteilung der Systemzeit
time_unix_usec = 0
time_boot_ms = 0
the_connection.mav.system_time_send(time_unix_usec, time_boot_ms)

# WICHTIG! Absenden von "Heartbeats" der verbundenen Systemkomponenten, damit die Verbindung aufrecht erhalten bleibt
# Send heartbeat from a MAVLink application.
the_connection.mav.heartbeat_send(pymavlink.mavutil.mavlink.MAV_TYPE_ONBOARD_CONTROLLER, pymavlink.mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0)

