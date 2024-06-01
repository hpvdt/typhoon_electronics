import asyncio
import numpy as np
from bleak import BleakClient
import time

power_uuid = "00002a63-0000-1000-8000-00805f9b34fb"
queue = []
prev_time = 0
window = 3 # get average cadence over x seconds
no_rev = 1
# start = 0
# end = 0

'''
(info from these links: 
https://stackoverflow.com/questions/54427537/understanding-ble-characteristic-values-for-cycle-power-measurement-0x2a63
https://github.com/sputnikdev/bluetooth-gatt-parser/blob/master/src/main/resources/gatt/characteristic/org.bluetooth.characteristic.cycling_power_measurement.xml
https://stackoverflow.com/questions/49813704/cycling-speed-and-cadence-sensors-ble-gatt-characteristic-data-parsing-and-oper
)

how "Cycling Power Measurement" characteristic is read:

ex. L = [32, 0, 0, 0, 185, 88, 23, 186]
from right to left, starting at byte 0:
- bytes 0 and 1 are the Flags field. flip them and express in binary, so 32, 0 -> 00000000 00100000
  the 1 means "Crank Revolution Data Present", so the only data you get from the pedals
  is instantaneous power (bytes 2-3) and crank revolution data (bytes 4-7).
- bytes 3 and 2 are instantaneous power in watts (a 16-bit integer)
- bytes 5 and 4 are Cumulative Crank Revolutions 
- bytes 7 and 6 are Last Crank Event Time "in seconds with a resolution of 1/1024" (ie. the unit is 1/1024 seconds)

last crank event time overflows every 65536/1024 = 64 seconds
'''

def notification_callback(sender, data): # gets data every ~1 second
    # global start,end
    # start = end
    # end = time.time()
    # print(end - start)
    global queue, prev_time, no_rev

    L = list(data) # "Cycling Power Measurement" characteristic
    #print(L)
    power = L[3] * 2**8 + L[2] # concatenating the bytes
    total_revs = L[5] * 2**8 + L[4]
    new_time = L[7] * 2**8 + L[6]
    print("power (W):", power)
    print("cumulative crank revolutions:", total_revs)
    print("last crank event time (s):", new_time/1024)
    
    if (prev_time != new_time): # yes rev
        if (prev_time > new_time): # rev with overflow
            diff = (65535 - prev_time) + new_time + 1
        else:
            diff = new_time - prev_time # rev w/o overflow
        if (no_rev > window): # refresh queue if we haven't been pedalling
            queue = []
        no_rev = 1
        queue.append(diff) # fill queue with the amounts of time each new revolution takes
    else: # no rev
        no_rev += 1
    
    # get cadence
    if no_rev > window + 1: # if we haven't been pedalling in approx x seconds
        cadence = 0
    else:
        if (len(queue) > window): # remove old period
            queue.pop(0)
        avg_rev_time = sum(queue) / len(queue) / 1024 # averaged seconds per revolution
        cadence = 1/avg_rev_time * 60 # revolutions per minute
        cadence = cadence/no_rev # gets artificial drop in cadence if we don't pedal 

    #print(queue)
    print("cadence (rpm):", round(cadence,2))
    prev_time = new_time

async def main():
    address = "0F190F5F-30CD-BF3C-7F90-EED38CBA0CDC" 

    async with BleakClient(address) as client:
        # check if connection was successful
        print(f"Client connection: {client.is_connected}") # prints True or False

        await client.start_notify(power_uuid, notification_callback)

        # collect data for X seconds
        await asyncio.sleep(1000.0)
asyncio.run(main())