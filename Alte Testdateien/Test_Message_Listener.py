from dronekit import *
import time

vehicle = connect('tcp:127.0.0.1:5760', wait_ready=True)

i=0
while True:
    i+=1
    time.sleep(1)

@vehicle.on_message('*')
def listener (self, name, message):
    print('message: %s' % message)