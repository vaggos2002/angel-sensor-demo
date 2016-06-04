py-angel-sensor
===============
Python interface to Angel Sensor M1 on Linux

The Angel Sensor  M1 (http://angelsensor.com/) is a wearable designed to allow direct access via Bluetooth. In short, the AGL-M1 model has sensors to measure the temperature, the heart rate, the acceleration, and the blood oxygen saturation (under development) .

This is a project to provide an API to allow access to the Angel Sensor M1 via a Bluetooth 
Low Energy protocol with Python. At present it runs on Linux only. The code was developed using a Raspberry Pi 3, but it is 
expected to run also on x86 Debian Linux

The code is tested on Python 2.7 .

Features
--------
Get data from :
- tempature in ceksius
- heart rate
- steps 
- accelerator energy magnitude

Exporting data to csv


Installation
------------
To install the API from the source :

    $ git clone https://github.com/vaggos2002/angel-sensor-demo
    $ cd py-angel-sensor
    $ sudo apt-get install pip
    $ sudo pip install requirement

Usage
-----
To get the temperature :

    $ ./main.py -a '00:07:80:02:F3:8C' -T


