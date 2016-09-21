#!/usr/bin/python

"""
Getting measurements from the Angel Senor M1 via bluepy
 - Temperature
 - Heart Rate
 - Step Count
 - Activity

"""

import os
import struct
import datetime
import time
import csv
import binascii
import argparse

try:
    from bluepy.btle import Peripheral, ADDR_TYPE_PUBLIC, AssignedNumbers, DefaultDelegate, BTLEException
except ImportError:
    from bluepy.bluepy.btle import Peripheral, ADDR_TYPE_PUBLIC, AssignedNumbers, DefaultDelegate, BTLEException



class csvLogger():
    '''CSV logger to store the data'''

    def __init__(self, enable=False, path=None):
        self.basic_path = os.path.dirname(os.path.realpath(__file__))
        self.enable = enable
        self.path = path

    def add_log(self, descr, content):
        row = [datetime.datetime.utcnow(), descr, content]    
        if not self.path:
            if self.enable:
                with open('templog.csv', 'w+') as f:
                    w = csv.writer(f)
                    w.writerow(row)

class HRM(Peripheral):

    def __init__(self, addr):
        print("Press the Angel Sensor's button to continue...")
        while True:
            try:
                Peripheral.__init__(self, addr, addrType=ADDR_TYPE_PUBLIC)
            except BTLEException:
                time.sleep(0.5)
                continue
            break

class generalDelegate(DefaultDelegate):
    message = 0

    def __init__(self, csvlog):
        DefaultDelegate.__init__(self)
        self.csvlog = csvlog

    def handleNotification(self, cHandle, data):

        if cHandle == 24 and data[0] == '\x02':
            val = binascii.b2a_hex(data)
            temp_val = val[2:10]
            temp_exp = temp_val[-2:]
            temp_mes = temp_val[:-2]
            temp_mes_swap = "".join(map(str.__add__, temp_mes[-2::-2] ,temp_mes[-1::-2]))
            temp_final = int(temp_mes_swap, 16)*0.1
            print('Temperature: {0} Celsius'.format(temp_final))
            self.csvlog.add_log('temp', temp_final)
        
        if cHandle == 19 and data[0] == '\x00':
            value = ord(data[1])
            print('Heart rate : {0}'.format(value))
            self.csvlog.add_log('heart_rate', value)
        
        if cHandle == 92:
            value = binascii.b2a_hex(data[::-1])
            value = int(value, 16)
            print('Steps : {0}'.format(value))
            self.csvlog.add_log('steps', value)

        if cHandle == 54:
            value = binascii.b2a_hex(data[::-1])
            value = str(int(value, 16)) + '%'
            print('Battery : {0}'.format(value))
            self.csvlog.add_log('battery', value)

        if cHandle == 63:
            basic = binascii.b2a_hex(data[::-1])
            n = 6
            splited = [basic[i:i+n] for i in range(0, len(basic), n)]
            for value in splited:
                value = str(int(value, 16))
                print('Activity Waveform : {0}'.format( value))
                self.csvlog.add_log('activity_waveform', value)
        
        if(data[0] == '\x14'):
            print("Connection Lost")
            self.message = "Connection Lost"
        if(data[0] == '\x16'):
            print(str(struct.unpack("B", data[1])[0]))
            self.message = str(struct.unpack("B", data[1])[0])
        if(data[0] == '\x06'):
            print("Booting")
            self.message = "Booting"
        

    def getlastbeat(self):
       return self.message


def get_chr_handle(hrm, service_id, characteristic_id):
    '''TODO: Get the Characteristic's handle number for a service'''
    service, = [s for s in hrm.getServices() if s.uuid==service_id]
    desc = hrm.getDescriptors(service.hndStart, service.hndEnd)
    d = [d for d in desc if d.uuid.getCommonName()==characteristic_id]
    if len(d) > 1:
        raise Exception('More than one characteristic was found')
    return d[0].handle

def get_characteristic_by_handle(hrm, service_id, handle):
    '''Return the characteristic based the handle'''
    service, = [s for s in hrm.getServices() if s.uuid==service_id]
    desc = hrm.getDescriptors(service.hndStart, service.hndEnd)
    characteristic = None
    for d_char in desc:
        if d_char.handle == handle:
            characteristic = d_char
    return characteristic
        

def get_ccc_handle(hrm, service_id, characteristic_id=None ):
    '''Get the Client Characteristic Configuration's handle number for a service'''
    cccid = AssignedNumbers.client_characteristic_configuration
    service, = [s for s in hrm.getServices() if s.uuid==service_id]
    desc = hrm.getDescriptors(service.hndStart, service.hndEnd)
    #print([d.uuid.getCommonName() for d in desc ])
    d = [d for d in desc if d.uuid==cccid]
    right_ccc_d = None
    if len(d) >= 2:
        for ccc_d in d:
            prev_ccc_d =  get_characteristic_by_handle(hrm, service_id, int(ccc_d.handle) - 2)
            if prev_ccc_d.uuid.getCommonName() == characteristic_id:
                right_ccc_d = ccc_d
    else:
        right_ccc_d = d[0]
    return right_ccc_d.handle

if __name__=="__main__":
    # Description, Service, Characteristic
    MEASUREMENTS_LIST = [
        [0, 'Temperature', AssignedNumbers.healthThermometer, AssignedNumbers.temperatureMeasurement  ],
        [1, 'Heart Rate', AssignedNumbers.heart_rate, AssignedNumbers.heart_rate_measurement ],
        [2, 'Activity Monitor - Step count', '68b52738-4a04-40e1-8f83-337a29c3284d', '7a543305-6b9e-4878-ad67-29c5a9d99736' ],
        [3, 'Activity Monitor - Acceleration Energy Magnitude', '68b52738-4a04-40e1-8f83-337a29c3284d', '9e3bd0d7-bdd8-41fd-af1f-5e99679183ff' ],
        [4, 'Blood Oxygen Saturation Service', '902dcf38-ccc0-4902-b22c-70cab5ee5df2', 'b269c33f-df6b-4c32-801d-1b963190bc71' ],
        [5, 'Optical Waveform Characteristic', '481d178c-10dd-11e4-b514-b2227cce2b54', '334c0be8-76f9-458b-bb2e-7df2b486b4d7' ],
        [6, 'Battery', '0000180f-0000-1000-8000-00805f9b34fb', '' ],
        [7, 'Acceleration Waveform', '481d178c-10dd-11e4-b514-b2227cce2b54', '4e92f4ab-c01b-4b5a-b328-699856a7c2ee' ],
        [8, 'Acceleration Waveform Signal Feature', '481d178c-10dd-11e4-b514-b2227cce2b54', '4cb32ae6-0cfe-47dc-a4f6-59f52cdc2910' ],
    ]

    hrm = None

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', help='MAC address for the device to program, e.g. 00:07:80:AB:CD:EF')
    parser.add_argument('-o', '--output', action='store_true', help='Store the measurements to the templog.csv file.')

    parser.add_argument('-T', '--temperature', action='store_true', help='Returns the temperature in celcius')
    parser.add_argument('-H', '--heartrate', action='store_true', help='Returns the heart rate in beats per minute')
    parser.add_argument('-O', '--oxygensaturation', action='store_true', help='Returns the Blood Oxygen Saturation in percent')
    parser.add_argument('-S', '--stepscount', action='store_true', help='Returns the steps count')
    parser.add_argument('-A', '--acceleratorenergymagnitude', action='store_true', help='Returns the accelerator energy magnitude')
    parser.add_argument('-C', '--accelerationwaveform', action='store_true', help='Returns the acceleration wave form')
    parser.add_argument('-c', '--accelerationwavexyz', action='store_true', help='Returns the acceleration wave form in x-y-z')
    parser.add_argument('-P', '--opticalwave', action='store_true', help='Returns the Optical Wave')
    parser.add_argument('-B', '--battery', action='store_true', help='Returns Battery')
    args = parser.parse_args()

    try:
        
        hrm = HRM(args.address)
        print('Device is connected.')
        csvlog = csvLogger(enable=args.output)

        hrm.setDelegate(generalDelegate(csvlog))

        if args.temperature:
            temp_handle = get_ccc_handle(hrm, MEASUREMENTS_LIST[0][2], MEASUREMENTS_LIST[0][3])
            hrm.writeCharacteristic(temp_handle, '\x02', True) # for TEMP we have indication
        if args.heartrate:
            hr_handle = get_ccc_handle(hrm, MEASUREMENTS_LIST[1][2]) 
            hrm.writeCharacteristic(hr_handle, '\x01', True) # for HR we have notification
        if args.stepscount:
            sc_handle = get_ccc_handle(hrm, MEASUREMENTS_LIST[2][2]) 
            hrm.writeCharacteristic(sc_handle, '\x01', True) # for Step count we have notification
        if args.oxygensaturation:
            os_handle = get_ccc_handle(hrm, MEASUREMENTS_LIST[4][2])
            hrm.writeCharacteristic(os_handle, '\x02', True) # for TEMP we have indication            
        if args.opticalwave:
            op_handle = get_ccc_handle(hrm, MEASUREMENTS_LIST[5][2])
            hrm.writeCharacteristic(op_handle, '\x01', True) # for TEMP we have notification
        if args.accelerationwaveform:
            op_handle = get_ccc_handle(hrm, MEASUREMENTS_LIST[7][2], MEASUREMENTS_LIST[7][3])
            hrm.writeCharacteristic(op_handle, '\x01', True) # for TEMP we have notification  
        if args.accelerationwavexyz:
            am_handle = get_chr_handle(hrm, MEASUREMENTS_LIST[8][2], MEASUREMENTS_LIST[8][3])
            value = binascii.b2a_hex(hrm.readCharacteristic(am_handle))
            #value = int(value, 16)
            print('Activity : {0}'.format(value))
            #hrm.writeCharacteristic(op_handle, '\x01', True) # for TEMP we have notification              
        if args.battery:
            br_handle = get_ccc_handle(hrm, MEASUREMENTS_LIST[6][2])
            hrm.writeCharacteristic(br_handle, '\x01', True) # for TEMP we have notification 

        while True:
            hrm.waitForNotifications(1.)
            if args.acceleratorenergymagnitude:
                am_handle = get_chr_handle(hrm, MEASUREMENTS_LIST[3][2], MEASUREMENTS_LIST[3][3])
                value = binascii.b2a_hex(hrm.readCharacteristic(am_handle)[::-1])
                value = int(value, 16)
                print('Activity : {0}'.format(value))
                csvlog.add_log('activity', value)
            #if args.accelerationwaveform:
            #    am_handle = get_chr_handle(hrm, MEASUREMENTS_LIST[8][2], MEASUREMENTS_LIST[8][3])
            #    value = binascii.b2a_hex(hrm.readCharacteristic(am_handle)[::-1])
            #    value = int(value, 16)
            #    print('Waveform Signal Feature : {0}'.format(value))
            #    csvlog.add_log('waveform_singal_feature', value)

    except Exception as er:
        if hrm:
            hrm.disconnect()
        print(er)
