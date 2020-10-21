import asyncio
from mavsdk import System
import time
#from dronekit import*
# Source code und Links zu Docs: https://github.com/mavlink/MAVSDK-Python

async def run():

    drone = System()
    await drone.connect(system_address="serial://COM5:115200")

    #oder so von https://github.com/mavlink/MAVSDK-Python/issues/130
    # how to run mavsdk_server externally: https://auterion.com/getting-started-with-mavsdk-java/
    # https://github.com/mavlink/MAVSDK-Python/issues/180
    #drone = System(mavsdk_server_address="127.0.0.1") # hier muss mavsdk_server extern gestartet werden
    #await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"Drone discovered with UUID: {state.uuid}")
            break

    print("Waiting for drone to have a global position estimate...")
    while True:
        p = drone.telemetry.position_velocity_ned()
        print(p.)


    print("-- Arming")
    await drone.action.arm()

    print("-- Taking off")
    await drone.action.takeoff()

    await asyncio.sleep(5)

    print("-- Landing")
    #await drone.action.land()

    # telemetry ist eine property-Methode der Klasse System, die ein telemetry.Telemetry-Objekt (durch -> in der Funktionsdef gekennzeichnet) quasi inline zurückgibt
    # eigentlich lässt sich drone.telemetry.position() somit als
    #     tel = drone.telemetry()
    #     tel.psoition()   aufteilen
    # durch Nutzung dieser Schreibweise kann die Zeile gespart werden
    await print_position(drone) #print_position(drone)

async def print_position(drone):
    async for position in drone.telemetry.position():
        print(position.latitude_deg)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())