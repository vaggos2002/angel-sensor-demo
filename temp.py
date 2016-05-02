#!/usr/bin/python
#
# Getting the temperature from the Angel Senor M1 via bluepy
# 

import time
import binascii
import argparse

from bluepy.btle import Peripheral, ADDR_TYPE_PUBLIC, AssignedNumbers, DefaultDelegate


class HRM(Peripheral):

    def __init__(self, addr):
        Peripheral.__init__(self, addr, addrType=ADDR_TYPE_PUBLIC)


class heartDelegate(DefaultDelegate):
    message = 0

    def __init__(self):
        DefaultDelegate.__init__(self)
     

    def handleNotification(self, cHandle, data):

        if(data[0] == '\x02'):
            val = binascii.b2a_hex(data)
            temp_val = val[2:10]
            temp_exp = temp_val[-2:]
            temp_mes = temp_val[:-2]
            temp_mes_swap = "".join(map(str.__add__, temp_mes[-2::-2] ,temp_mes[-1::-2]))
            self.message = int(temp_mes_swap, 16)*0.1
        elif(data[0] == '\x14'):
            self.message = "Connection Lost"
        elif(data[0] == '\x16'):
            self.message = str(struct.unpack("B", data[1])[0])
        elif(data[0] == '\x06'):
           self.message = "Booting"
        

    def getlastbeat(self):
       return self.message



if __name__=="__main__":
    cccid = AssignedNumbers.client_characteristic_configuration
    htid = AssignedNumbers.healthThermometer # service Health Thermometer 
    httid = AssignedNumbers.temperatureMeasurement # characteristic

    hrmid = AssignedNumbers.heart_rate
    hrmmid = AssignedNumbers.heart_rate_measurement

    hrm = None


    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', help='MAC address for the device to program, e.g. 00:07:80:AB:CD:EF')
    args = parser.parse_args()


    try:
        
        hrm = HRM(args.address)
        print('Device is connected.')
        hrm.setDelegate(heartDelegate())
        print('Deleagate was set.')

        service, = [s for s in hrm.getServices() if s.uuid==htid] # done
        ccc, = service.getCharacteristics(forUUID=str(httid))  #d one

        if 0: # This doesn't work
            ccc.write('\1\0')
            
        else:
            desc = hrm.getDescriptors(service.hndStart, service.hndEnd)
            d, = [d for d in desc if d.uuid==cccid]
            hrm.writeCharacteristic(26, '\x02', True)
            
        while True:
            hrm.waitForNotifications(2.)
            print('Temperature: {0} Celsius'.format(hrm.delegate.getlastbeat()))

    finally:
        if hrm:
            hrm.disconnect()
