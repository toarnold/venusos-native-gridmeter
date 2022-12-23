#!/usr/bin/env python3
from gi.repository import GLib
import logging
import json
from DBusNativeGridMeterService import DBusNativeGridMeterService

def main():
    logging.basicConfig(level=logging.INFO)

    #Read config
    with open('config.json') as f:
        config = json.load(f)

    from dbus.mainloop.glib import DBusGMainLoop
    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)

    service = DBusNativeGridMeterService(config)

    logging.info(
        'Connected to dbus, and switching over to GLib.MainLoop() (= event based)')
    mainloop = GLib.MainLoop()
    mainloop.run()


if __name__ == "__main__":
    main()
