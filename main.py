#!/usr/bin/python
#
# Getting measurements from the Angel Senor M1 via bluepy
# - Temperature
# - Heart Rate
# - Step Count

import time
import binascii
import argparse

try:
    from bluepy.btle import Peripheral, ADDR_TYPE_PUBLIC, AssignedNumbers, DefaultDelegate
except ImportError:
    from bluepy.bluepy.btle import Peripheral, ADDR_TYPE_PUBLIC, AssignedNumbers, DefaultDelegate



class HRM(Peripheral):

    def __init__(self, addr):
        Peripheral.__init__(self, addr, addrType=ADDR_TYPE_PUBLIC)


class generalDelegate(DefaultDelegate):
    message = 0

    def __init__(self):
        DefaultDelegate.__init__(self)
     

    def handleNotification(self, cHandle, data):

        if cHandle == 24 and data[0] == '\x02':
            val = binascii.b2a_hex(data)
            temp_val = val[2:10]
            temp_exp = temp_val[-2:]
            temp_mes = temp_val[:-2]
            temp_mes_swap = "".join(map(str.__add__, temp_mes[-2::-2] ,temp_mes[-1::-2]))
            temp_final = int(temp_mes_swap, 16)*0.1
            print('Temperature: {0} Celsius'.format(temp_final))
        
        if cHandle == 19 and data[0] == '\x00':
            print('Heart rate : {0}'.format(ord(data[1])))
        
        if cHandle == 92:
            val = binascii.b2a_hex(data[::-1])
            print('Steps : {0}'.format(int(val, 16)))
        
        if(data[0] == '\x14'):
            self.message = "Connection Lost"
        if(data[0] == '\x16'):
            self.message = str(struct.unpack("B", data[1])[0])
        if(data[0] == '\x06'):
           self.message = "Booting"
        

    def getlastbeat(self):
       return self.message


def get_chr_handle(hrm, characteristic_id):
    '''TODO: Get the Characteristic's handle number for a service'''
    return

def get_ccc_handle(hrm, service_id):
    '''Get the Client Characteristic Configuration's handle number for a service'''
    cccid = AssignedNumbers.client_characteristic_configuration
    service, = [s for s in hrm.getServices() if s.uuid==service_id]
    desc = hrm.getDescriptors(service.hndStart, service.hndEnd)
    d, = [d for d in desc if d.uuid==cccid]
    return d.handle

if __name__=="__main__":
    # Description, Service, Characteristic
    MEASUREMENTS_LIST = [
        [0, 'Temperature', AssignedNumbers.healthThermometer, AssignedNumbers.temperatureMeasurement  ],
        [1, 'Heart Rate', AssignedNumbers.heart_rate, AssignedNumbers.heart_rate_measurement ],
        [2, 'Activity Monitor - Step count', '68b52738-4a04-40e1-8f83-337a29c3284d', '7a543305-6b9e-4878-ad67-29c5a9d99736' ],
        [3, 'Activity Monitor - Acceleration Energy Magnitude', '68b52738-4a04-40e1-8f83-337a29c3284d', '9e3bd0d7-bdd8-41fd-af1f-5e99679183ff' ],
    ]

    hrm = None

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', help='MAC address for the device to program, e.g. 00:07:80:AB:CD:EF')
    args = parser.parse_args()

    try:
        
        hrm = HRM(args.address)
        print('Device is connected.')
   
        hrm.setDelegate(generalDelegate())

        temp_handle = get_ccc_handle(hrm, MEASUREMENTS_LIST[0][2])
        hr_handle = get_ccc_handle(hrm, MEASUREMENTS_LIST[1][2])
        sc_handle = get_ccc_handle(hrm, MEASUREMENTS_LIST[2][2])

        hrm.writeCharacteristic(temp_handle, '\x02', True) # for TEMP we have indication
        hrm.writeCharacteristic(hr_handle, '\x01', True) # for HR we have notification
        hrm.writeCharacteristic(sc_handle, '\x01', True) # for Step count we have notification
            
        while True:
            hrm.waitForNotifications(1.)

    except Exception as er:
        if hrm:
            hrm.disconnect()
        print(er)
