#!/usr/bin/env python3

from gi.repository import GLib
import os
import sys
import logging
import platform
import traceback
import requests
from requests.exceptions import HTTPError

version = "v1.01"

# our own packages
sys.path.insert(1, os.path.join(os.path.dirname(__file__), './velib_python'))
from vedbus import VeDbusService

class DBusNativeGridMeterService(object):

    formattings = {
        'kWh': lambda path, val: f"{val} kWh",
        'A': lambda path, val: f"{val} A",
        'W': lambda path, val: f"{val} W",
        'V': lambda path, val: f"{val} V"
    }

    def __init__(self, config):
        global version
        servicename = "com.victronenergy.grid.tasmota_"+str(config['tasmotaIp']).replace(".","_")
        connection = "http://"+str(config['tasmotaIp'])
        deviceinstance = config['deviceInstance']
        self._dbusservice = VeDbusService(servicename)
        self._config = config

        logging.debug(f"{servicename} /DeviceInstance = {deviceinstance}")

        # Create the management objects, as specified in the ccgx dbus-api document
        # see https://github.com/victronenergy/venus/wiki/dbus-api
        self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
        self._dbusservice.add_path('/Mgmt/ProcessVersion', version)
        self._dbusservice.add_path('/Mgmt/Connection', connection)

        # Create the mandatory objects
        self._dbusservice.add_path('/DeviceInstance', deviceinstance)
        self._dbusservice.add_path('/ProductId', 0)
        self._dbusservice.add_path('/ProductName', config['productName'])
        self._dbusservice.add_path('/FirmwareVersion', 0)
        self._dbusservice.add_path('/HardwareVersion', 0)
        self._dbusservice.add_path('/Connected', 0) # Initial off

        for mapping in config['mappings']:
            self._dbusservice.add_path(
                mapping['dBusPath'],
                mapping['initialValue'],
                gettextcallback=self.formattings[mapping['unit']],
                writeable=True,
                onchangecallback=self._handlechangedvalue)

        GLib.timeout_add(config['queryInterval']*1000, self._update)

    def query_value(self, jdata, path):
        for part in path.split("."):
            jdata = jdata[part]
        return jdata

    def _update(self):
        try:
            r = requests.get(f"http://{self._config['tasmotaIp']}/cm?cmnd=status%2010", timeout=2)
            if r.status_code == 200:
                jdata = r.json()
                if not self._config['meterPath'] or not self._config['meterId'] or self.query_value(jdata, self._config['meterPath']) == self._config['meterId']:
                    self._dbusservice['/Connected'] = 1
                    # Set DBus values
                    for mapping in self._config['mappings']:
                        # Skip if no source
                        if not not mapping['dataPath']:
                            value = round(
                                self.query_value(
                                    jdata, mapping['dataPath']) * mapping['scale'],
                                mapping['digits'])
                            logging.debug(f"{mapping['dBusPath']}={value}")
                            self._dbusservice[mapping['dBusPath']] = value
                else:
                    self._dbusservice['/Connected'] = 0
                    logging.error(f"unknown meter id {self.query_value(jdata, self._config['meterPath'])}")
            else:
                self._dbusservice['/Connected'] = 0
                logging.error(f"http response {r.status_code}")
        except HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err}")
        except Exception as e:
            logging.error(f"Exception occurred: {e}")
            logging.error(traceback.format_exc())

        return True

    def _handlechangedvalue(self, path, value):
        logging.debug(f"someone else updated {path} to {value}")
        return True  # accept the change
