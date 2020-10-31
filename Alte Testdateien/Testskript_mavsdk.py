from mavsdk import System

$ pip3 install mavsdk
$ pip3 install aioconsole
$ apython
> from mavsdk import connect
> from mavsdk import start_mavlink
> start_mavlink()
> drone = connect(host=’localhost’)
> await
drone.action.arm()
> await
drone.action.takeoff()

