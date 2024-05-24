import asyncio
import numpy as np
from bleak import BleakClient

power_uuid = "00002a63-0000-1000-8000-00805f9b34fb"

def notification_callback(sender, data):

    L = list(data) # all the info under "Cycling Power Measurement" characteristic, includes power (L[3] L[2]) and cadence (somewhere)
                   # first two bytes in list are 00000000 00100000, the 1 at index 5 means "Crank Revolution Data Present"
    # print(L)
    # print("power (W):", int(L[3]), int(L[2]))
    print("power (W):", int(str(L[3]) + str(L[2])))

async def main():
    address = "0F190F5F-30CD-BF3C-7F90-EED38CBA0CDC" 

    async with BleakClient(address) as client:
        # Check if connection was successful
        print(f"Client connection: {client.is_connected}") # prints True or False

        await client.start_notify(power_uuid, notification_callback)

        # Collect data for X seconds
        await asyncio.sleep(30.0)
asyncio.run(main())