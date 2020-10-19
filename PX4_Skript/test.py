import asyncio
from mavsdk import System

# Source code und Links zu Docs: https://github.com/mavlink/MAVSDK-Python
# andere fragen: https://github.com/mavlink/MAVSDK-Python/issues?page=1&q=is%3Aissue+is%3Aclosed

# asynchroner code: lässt python-code quasi parallel laufen, sodass eine unendliche Schleife ausgeführt wird, aber gleichzeitig noch andere Befehle ausgeführt werden
# das ist insbesondere gut für Drohnen: ständig abfragen und verabrieten von Sensordaten und gleichzeitig darauf reagieren (zB Motor entsprechend steuern oder
# das Steuerprogramm ausführen!)

async def run():

    drone = System()
    #await drone.connect(system_address="udp://:14540")
    await drone.connect(system_address="serial://COM4")#5760") oder bei Verbindung zu PX4: serial://COM0:115200

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"Drone discovered with UUID: {state.uuid}")
            break

    """
    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok:
            print("Global position estimate ok")
            break
    """

    #print("-- Arming")
    #await drone.action.arm()
    print("Test")
    a = await drone.info.get_product()
    print(a)
    print("lol")
    #async for euler in drone.telemetry.attitude_euler():
    #    print(euler.yaw_deg)

    await drone.telemetry.set_rate_imu(100)
    # https://github.com/mavlink/MAVSDK-Python/issues/241
    # magnetoemter feldstärke
    async for health in drone.telemetry.health():
        print(health)
        break

    #async for euler in drone.telemetry.attitude_euler():
    #    print(euler)

    async for position in drone.telemetry.position():
        print(position)

    async for imu in drone.telemetry.imu():
        print(imu)
        #print(imu.magnetic_field_frd.forward_gauss)
        #print(imu.magnetic_field_frd.down_gauss)
        #print(imu.magnetic_field_frd.right_gauss)
        #print("-----")

    # eulerwinkel aus magnetometer
    #async for euler in drone.telemetry.attitude_euler():
    #    print(euler.yaw_deg)

    #await print("-- Taking off")
    #await drone.action.takeoff()

    #await asyncio.sleep(5)

    #print("-- Landing")
    #await drone.action.land()

    # telemetry ist eine property-Methode der Klasse System, die ein telemetry.Telemetry-Objekt (durch -> in der Funktionsdef gekennzeichnet) quasi inline zurückgibt
    # eigentlich lässt sich drone.telemetry.position() somit als
    #     tel = drone.telemetry()
    #     tel.psoition()   aufteilen
    # durch Nutzung dieser Schreibweise kann die Zeile gespart werden
    #await print_position(drone) #print_position(drone)

async def print_position(drone):
    async for position in drone.telemetry.position():
        print(position.latitude_deg)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())