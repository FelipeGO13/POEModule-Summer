"""
    Created on November 21, 2014
    Last modified on April 17, 2015 by Yaodong Yu

    @author: Ruibing Zhao
    @author: Peter Zhang

    This is the main CoAP server running on Raspberry Pi as a part of UBC ECE 2014 Capstone Project #94.
    The implementation of this CoAP client is based on aiocoap module

    Reference: https://aiocoap.readthedocs.org/

    Python3.4 is required
"""

import logging
import json

import asyncio

import aiocoap
from aiocoap.resource import Site

import resources as r

# logging setup
logging.basicConfig(level=logging.INFO)
logging.getLogger('coap-server').setLevel(logging.DEBUG)
# TODO: Add logging function to replace "print" in the code


def main():
    """
    Create resource tree from given configuration file
    """

    root = Site()

    # default resources to add
    root.add_resource('', r.RootResource(root))
    root.add_resource(('.well-known', 'core'), r.CoreResource(root))

    # temporarily disabled
    #root.add_resource(('alert',), r.Alert())

    with open('config.json') as data_file:
        sensor_list = json.load(data_file)['sensors']
    
    for sensor in sensor_list:
        # Known sensors that has been pre-defined
        if sensor['name'] == 'hello':
            root.add_resource(tuple(sensor['url'].split('/')), r.HelloWorld())
        elif sensor['name'] == 'time':
            root.add_resource(tuple(sensor['url'].split('/')), r.LocalTime())
        elif sensor['name'] == 'accelerometer':
            root.add_resource(tuple(sensor['url'].split('/')), r.Acceleration())
        elif sensor['name'] == 'temperature':
            root.add_resource(tuple(sensor['url'].split('/')), r.Temperature())
        elif sensor['name'] == 'humidity':
            root.add_resource(tuple(sensor['url'].split('/')), r.Humidity())
        elif sensor['name'] == 'joystick':
            root.add_resource(tuple(sensor['url'].split('/')), r.Joystick())
        # For unknown sensors, use template resource
        else:
            root.add_resource(tuple(sensor['url'].split('/')),
                              r.ResourceTemplate(sensor['name'],
                                                 sensor['active'],
                                                 sensor['period'],
                                                 sensor['min'],
                                                 sensor['max'],
                                                 sensor['channel']))

        print("{} resource added to path /{}".format(sensor['name'], sensor['url']))
        '''
        # Debug information: print all fields of each resource in configuration file
        for entry in sensor:
            if entry != 'name' and entry != 'url':
                print("{}:{}".format(entry, sensor[entry]))
        '''

    asyncio.async(aiocoap.Context.create_server_context(root))
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    main()
