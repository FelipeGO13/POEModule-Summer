"""
    Created on November 22, 2014
    Last modified on April 16, 2015 by Yaodong Yu

    @author: Ruibing Zhao
    @author: Yaodong Yu

    This is a command line tool developed as a CoAP client for demonstration of UBC ECE 2014 Capstone Project #94.
    The implementation of this CoAP client is based on aiocoap module

    Reference: https://aiocoap.readthedocs.org/

    Python3.4 is required
"""

import sys
import time
import logging
import json
import asyncio
import aiocoap
import socket
import functools
import signal
import h5py
import numpy
import datetime
import paramiko
import os
import subprocess
import matplotlib.pylab as plt
import scapy


from aiocoap import *
from defs import *

																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																															
# Default client configuration:
# IP is (local) 127.0.0.1
server_IP = 'localhost'
not_alert = True
plotting, = plt.plot([], [])
# resources independent from hardware implementation
resources = {'hello': {'url': 'hello'},
             'time': {'url': 'time'}}
# Octave plotting data file
data_file = 'data.txt'
# Creating HDF5 file or opening an existing one
h5_file = h5py.File("testfile.hdf5", "a")

print("HDF5 File Created!!")
# flag to enable Octave plotting
run_demo = False
# ssh connection to get config file from server
ssh = paramiko.SSHClient() 
# asyncio event loop for																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																 client
# Keep a record so that it can be switched back after observation
client_event_loop = asyncio.get_event_loop()

try:
    from oct2py import octave
except Exception as e:
    print("{}: Not running demo files".format(e))
    run_demo = False
else:
    run_demo = True

print(plotting)
# logging configuration
logging.basicConfig(level=logging.INFO)
# TODO: Add logging function to replace "print" in the code


def create_grouph5():
    """
    Create an HDF5 group with the ip of the controller module connected to the client
    If the module is already recorded in the database, the function just assign it to a HDF5 group 
    variable.
    All the necessary metadata is obtained by the configuration json file provided by the server.
    """
    try:
        module = server_IP

        if h5_file.__contains__(module):
            print("Module {} already recorded in the database".format(module))
            grp = h5_file.__getitem__(module)
            grp.attrs["Last access"] = str(datetime.datetime.now())  
        else:
            grp = h5_file.create_group("{}".format(server_IP))
            with open('config.json') as config_file:
                data = json.load(config_file)
                if 'metadata' in data['server']:
                    metadata = data['server']['metadata']	
                    for key in metadata.keys():
                        grp.attrs['{}'.format(key)] = '{}'.format(metadata[key])
                    grp.attrs["Last access"] = str(datetime.datetime.now())
                else:
                    print("No Metadata available for this module {}".format(module))

            print("Group {} created!".format(module))

        return grp

    except Exception as e:
        print("Failed to create file or group! {}".format(e))

def insert_dataset(grp, name, comp_type):
    """
    Create an HDF5 dataset with the name of the sensor connected to the contorller module and
    implemented by the configuration json file.
   
    All the necessary metadata is obtained by the configuration file provided by the server.
    """
    try:
        dset = grp.create_dataset("{}".format(name), (1, ), comp_type, maxshape=(None,))
        with open('config.json') as config_file:
                data = json.load(config_file)
                length = len(data['sensors'])  
                for x in range(0, length-1):
                    if name == data['sensors'][x]['url']:
                         if 'metadata' in data['sensors'][x]:
                             metadata = data['sensors'][x]['metadata']
                             for key in metadata.keys():
                                 dset.attrs['{}'.format(key)] = '{}'.format(metadata[key])
                         else:
                             print("No metadata available for this sensor") 
 	
        print("Dataset succesfully created")     
    except Exception as e:
        print("Failed to create a dataset! {}".format(e))

#Testing fixed datatype formatting
    """
    Hard coded formatting for the compound type that defines the datatypes of the dataset columns
    """
"""
def create_comptype(name, jpl):
    global comp_type
    if jpl['name'] == 'temperature':
        comp_type = numpy.dtype([('time', 'S20'),('temperature', 'f'), ('active', 'S10')])
    elif jpl['name'] == 'humidity':
        comp_type = numpy.dtype([('time', 'S20'),('humidity', 'f'), ('active', 'S10')])
    elif 'Acc' in jpl['name']:
        if 'X' in jpl['name']:
            comp_type = numpy.dtype([('time', 'S20'),('AccX', 'f'), ('rate', 'i'), ('active', 'S10')])
        elif 'Y' in jpl['name']:
            comp_type = numpy.dtype([('time', 'S20'),('AccY', 'f'), ('rate', 'i'), ('active', 'S10')])
        elif 'Z' in jpl['name']:
            comp_type = numpy.dtype([('time', 'S20'),('AccZ', 'f'), ('rate', 'i'), ('active', 'S10')])
    elif jpl['name'] == 'hello':
            comp_type = numpy.dtype([('time', 'S20'),('hello', 'S30')])
    elif 'Joy' in jpl['name']:
        if 'X' in jpl['name']:
            comp_type = numpy.dtype([('time', 'S20'),('JoyX', 'f'), ('rate', 'i')])
        elif 'Y' in jpl['name']:
            comp_type = numpy.dtype([('time', 'S20'),('JoyY', 'f'), ('rate', 'i')])
    else:
        comp_type = numpy.dtype([('test', 'f')])
    return comp_type
"""

def store_data(dset, jpl):
    """
    Create a new tuple and store the obtained data from sensors in the datasets, identifying 
    the column by the json file received as response from the server.
    """
    global not_alert
    global plotting
    print(plotting)
    dset.resize(dset.len()+1, 0)
    data = json.loads(jpl['data']) 
    for key in jpl.keys():
        if key == 'data':
            for key in data.keys():
                dset['{}'.format(key), dset.len()-2] = data[jpl['name']]
                if not_alert is True:
                    not_alert = alert(data, dset)            
                else:
                    if type(plotting.get_xdata()) is not int:
                        next = len(plotting.get_xdata()) + 1
                    else:
                        next = plotting.get_xdata()+1
                    plotting.set_ydata(numpy.append(plotting.get_ydata(), data[jpl['name']]))
                    plotting.set_xdata(numpy.insert(plotting.get_xdata(), (next-1), next))
                    ax = plt.gca()
                    ax.relim()
                    ax.autoscale_view()
                    plt.draw()
        else: 
            try:          
                dset['{}'.format(key), dset.len()-2] = jpl[key]
            except Exception as e: 
                print('') 

    print("Data successfully recorded in the database!")

#Testing dynamic datatype formatting

def create_comptype(jpl): 
    """
    Dynamic formatting for the compound type that defines the datatypes of the dataset columns
    """
    global temp_comptype
    data = json.loads(jpl['data']) 
    i = 0 
    columns = []
    types = []

    columns.extend([None]*len(jpl.keys()))

    types.extend([None]*len(jpl.keys()))

    #TODO: Change this to be more dynamic
    temp_comptype = numpy.dtype([('Test', 'i'), ('Test2', 'i'), ('Test3', 'i'), ('Test4', 'i')])

    for key in jpl.keys():
        if key == 'name':
            columns[i] = jpl[key] 
            types[i] = check_type(data[jpl[key]])
            i += 1 
        elif key == 'data':
           print('')
        else:
           types[i] = check_type(jpl[key])
           columns[i] = key
           i += 1 

    temp_comptype.names = (columns[0], columns[1], columns[2] , columns[3])
    comp_type = temp_comptype.descr

    for x in range(0, len(comp_type)):
        comp_type[x] = (comp_type[x][0], types[x])
    return comp_type

# Check type of data
#TODO: Check all possible datatypes available and include more formatting options
def check_type(data):
    if type(data) is float:
        return 'f'
    elif type(data) is int:
        return 'i'
    elif type(data) is str:
        try:
            if float(data):
                return 'f'
        except:
            return 'S30'
    elif type(data) is bool:
        return 'bool'
    else:
        print("It was not possible to identify this data format")

def alert(data, dset): 
    #print(data)
    global plotting
    with open('config.json') as config_file:
        config = json.load(config_file)
        length = len(config['sensors'])     
        for key in data.keys():
            for x in range(0, length-1):
                if key == config['sensors'][x]['name']:
                    sensor = config['sensors'][x]
                    if dset.attrs.__contains__(key):
                        if (float(data[key]) > sensor['max_limit']) | (float(data[key]) < sensor['min_limit']):
                            ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
                            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                            ssh.connect('192.168.2.100', username='group94', password = 'upoe94')
                            stdin, stdout, stderr = ssh.exec_command("tclsh bootflash:poe.tcl")
                            for line in stdout.readlines():
                                print (line.strip())
                            ssh.close()                       
                            plotting, = plt.plot(dset[key])
                            plt.xlabel("Number of measurements")
                            plt.ylabel(key)
                            plt.title("Test Graphs")
                            plt.show(block=False)
                           
                            return False
    return True



def plot_octave(jpayload):
    # TODO: plotting function should be more dynamic, to match the configurability of the rest of the program
    """
    Function to direct resource data to Octave program to plot

    Example:
    octave.database_init('data.txt')
                                    x  y  z  temp   humid   motion  joystickX,Y  year  mon day hh  mm  ss
    octave.update_plot('data.txt', [3, 3, 3, NaN,   NaN,    NaN,    Nan,    NaN, 1111, 11, 11, 11, 11, 11])
    octave.save_database('data.txt')

    :param dict jpayload: resource object in dict(JSON) format
    :raises AttributeError: failed to parse jpayload for resource data
    :raises RuntimeError: failed to complete octave plotting script
    """
    if run_demo is True and jpayload['name'] in resources:
        #print("payload is {}".format(jpayload))
        time = []
        data = []
        plot_i = -1
        print(jpayload['name'])
        try:
            # TODO: data format for plotting should be more dynamic
            jvalue = json.loads(jpayload['data'])
            #print("{}".format(jvalue))
            if jpayload['name'] == 'JoyX':
                data += [float('NaN'), float('NaN'), float('NaN'),
                         float('NaN'), float('NaN'), float('NaN'),
                         float(jvalue['leftright']), float(jvalue['updown'])]
                plot_i = 1;
            elif jpayload['name'] == 'temperature':
                data += [float('NaN'), float('NaN'), float('NaN'),
                         float(jvalue['temperature']),
                         float('NaN'), float('NaN'), float('NaN'), float('NaN')]
                plot_i = 2;
            elif jpayload['name'] == 'humidity':
                data += [float('NaN'), float('NaN'), float('NaN'), float('NaN'),
                         float(jvalue['humidity']),
                         float('NaN'), float('NaN'), float('NaN')]
                plot_i = 3;
            else:
                print("Unknown data. Skip plotting...\n")
                return
        except Exception as e:
            raise AttributeError("Failed to parse data for demo: {}".format(e))

        # Parse payload data
        import re
        time_str = re.split('[- :]', jpayload['date time'])
        try:
            for i in range(5):
                time += [int(time_str[i])]
            time += [float(time_str[5])]
        except Exception as e:
            time = [0, 0, 0, 0, 0, 0.0]
            print("Failed to parse time: {}, using:".format(e, time))
        data += time

        print("data to plot: {}".format(data))

        try:
            octave.demo_update(data_file, data, plot_i)
        except Exception as e:
            # Do not want to disable plotting here since it may be a one-time failure
            #   on plotting script
            raise RuntimeError("Failed to plot: {}".format(e));


def incoming_data(response, url):
    """
    Function used to deal with response

    :var bool run_demo: (global) whether to run Octave demonstration
    :param response: response from CoAP server
    :param response: aiocoap.message.Message
    """
    global run_demo
    global jpayload
    jpayload = 0
    payload = response.payload.decode(UTF8)
    if response.opt.content_format is not JSON_FORMAT_CODE:
        print("Result:\n{}: {}".format(response.code, payload))
    else:
        jpayload = json.loads(payload)
        print("Result (JSON):\n{}: {}".format(response.code, jpayload))
        try:
            if grp.__contains__(url):
                dset = grp.__getitem__(url)
                store_data(dset, jpayload) 
                plot_octave(jpayload)
            else:
                insert_dataset(grp, url, create_comptype(jpayload))
                plot_octave(jpayload)
                print("All data will be stored in the HDF5 file")
        except Exception as e:
            #print("Failed to store in a dataset {}/ {}".format(url, e))
            print("{}".format(e))
            print("Disabling Octave script...")
            run_demo = False
       
          

def end_observation(loop):
    """
    Callback function used for ending observation to resource on client side.

    :param BaseEventLoop loop: event loop for observing resource
    """
    # FIXME: method should actually end observation on server.
    #       Now, it only deals with client side

    print("Observation ended by user interrupt...")
    # Terminate observation event loop
    loop.close()
    
    print("Observation loop ended in the client...")

    # Restore event loop
    asyncio.set_event_loop(client_event_loop)
    print("Switched back to client console...")

@asyncio.coroutine
def post_impl(jargs):
    """
    Implementation of CoAP POST request

    :param str jargs: parameter of resources to be put in JSON format
    :raises RuntimeError: incorrect Context for client
    """
    context = yield from Context.create_client_context()

    request = Message(code=POST, payload=jargs.encode(UTF8))
    request.set_request_uri('coap://{}/'.format(server_IP))

    try:
        response = yield from context.request(request).response
    except Exception as e:
        raise RuntimeError("Failed to create new resource: {}".format(e))
    else:
        incoming_data(response, url)
      
@asyncio.coroutine
def get_impl(url=''):
    """
    Implementation of CoAP GET request

    :param str url: url to locate resource
    :raises RuntimeError: incorrect Context for client
    """
    context = yield from Context.create_client_context()
    request = Message(code=GET)
    request.set_request_uri('coap://{}/{}'.format(server_IP, url))
 
    try:
        response = yield from context.request(request).response
    except Exception as e:
        raise RuntimeError("Failed to fetch resource: {}".format(e))
    else:
        incoming_data(response, url)
     
@asyncio.coroutine
def put_impl(url='', payload=""):
    """
    Implementation of CoAP Put request

    :param str url: url to locate resource
    :param str payload: content to PUT to resource
    :raises RuntimeError: incorrect Context for client
    """
    context = yield from Context.create_client_context()

    yield from asyncio.sleep(2)

    request = Message(code=PUT, payload=payload.encode(UTF8))
    request.set_request_uri('coap://{}/{}'.format(server_IP, url))

    try:
        response = yield from context.request(request).response
    except Exception as e:
        raise RuntimeError("Failed to update resource: {}".format(e))
    else:
        incoming_data(response, url)

@asyncio.coroutine
def observe_impl(url=''):
    """
    Implementation of CoAP Observe request

    :param str url: url to locate resource	
    :raises NameError: cannot locate resource at given url
    :raises RuntimeError: server responds code is unsuccessful
    """
    context = yield from Context.create_client_context()

    request = Message(code=GET)
    request.set_request_uri('coap://{}/{}'.format(server_IP, url))

    request.opt.observe = 0
    observation_is_over = asyncio.Future()
    requester = context.request(request)
    requester.observation.register_errback(observation_is_over.set_result)
    requester.observation.register_callback(lambda data: incoming_data(data, url))
    try:
        response_data = yield from requester.response
    except socket.gaierror as e:
        raise NameError("Name resolution error: {}".format(e))
       
    if response_data.payload:
        incoming_data(response_data, url)

    if not response_data.code.is_successful():
       raise RuntimeError("Observation failed!")
            
    exit_reason = yield from observation_is_over
    print("Observation exits due to {}".format(exit_reason))

class Commands():
    """
    Class to hold all the implemented commands
    """
    @staticmethod
    def do_help(command=None):
        """
        Print help menu

        If no command is given, list all available commands;
        otherwise, show __doc__ of given command.
        Example:
        ``>>>help time``

        :param str command: of which command help is needed
        """
        if command:
            print(getattr(Commands, 'do_'+command).__doc__)
        else:
            commands = [cmd[3:] for cmd in dir(Commands)
                        if cmd.startswith('do_') and cmd != 'do_resource']
            print("Valid commands: " + ", ".join(commands))
            print("Valid resources: " + ", ".join(resources))
            print("\n'help [command]' or 'help resource' for more details\n")

    @staticmethod
    def do_ip(ip=None):
        """
        Read or change server IP.

        Default IP is given by config.json upon client initialization
        If no parameter is given, return server IP; otherwise, set server IP to given value

        Examples:
        ``>>>ip 192.168.2.20``
        ``>>>ip localhost``
        ``>>>ip``

        :var str server_IP: (global) server IP address
        :param str ip: server IP to set
        """
        global server_IP

        if ip is None:
            print("Server IP: {}".format(server_IP))
        else:
            print("Server IP was {}".format(server_IP))
            server_IP = ip
            print("Server IP is set to {}".format(ip))

    @staticmethod
    def do_exit(*args):
        """
        Terminate client program using sys.exit

        Example: ``>>>exit``
        """
        print("Goodbye!")
        print("Exiting...")
        h5_file.close()
        sys.exit(0)

    @staticmethod
    @asyncio.coroutine
    def do_probe(*args):
        """
        Check whether server is alive

        Example: ``>>>probe``
        """
        # send GET request to Root resource to check on server
        yield from get_impl()

    @staticmethod
    @asyncio.coroutine
    def do_add(name, *args):
        """
        Add new resource to server

        Syntax: >>>add [name] -c [ADC_channel] (-u [url]) (-l [min] -m [max]) (-o) (-f [observe_frequency]) (-h)
        -c --channel    ADC channel this resource is connected to
        -u --url        url for the resource to post
        -l --min        lower bound of the resource to be mapped to
        -m --max        higher bound of the resource to be mapped to
        -o --observe    observable resource
        -f --frequency  frequency of observing this resource
        -h --help       detailed help page of arguments

        Example: ``>>>add new_r -c0 -u myR/r1 -l0 -m10 -o -f5``

        :param str name: name of the resource
        :param str[] args: option or payload of PUT request
        :raises AttributeError: option argument(s) not integer
        :raises RuntimeError: POST request failed
        """
        import argparse

        p = argparse.ArgumentParser(description=__doc__)
        p.add_argument('-c', '--channel', help="ADC channel this resource is connected to")
        p.add_argument('-u', '--url', help="new URL for the resource to post")
        p.add_argument('-l', '--min', help="lower bound of resource data")
        p.add_argument('-m', '--max', help="higher bound of resource data")
        p.add_argument('-o', '--observe', help="Set the resource to be observable", action='store_true')
        p.add_argument('-f', '--frequency', help="Set the frequency of observable")

        options = p.parse_args(args)

        # channel number is not optional
        if not options.channel:
            raise AttributeError("ADC Channel not found")
        else:
            try:
                channel = int(options.channel)
            except ValueError as e:
                raise ValueError("Channel must be integer")

        # default value of other options
        url = name
        active = False
        frequency = 0
        b_range = False
        min = None
        max = None

        if options.url:
            url = options.url
        else:
            print("Warning: use resource name ({}) as url".format(name))

        if options.min and options.max:
            try:
                min = int(options.min)
                max = int(options.max)
                b_range = True
            except ValueError as e:
                raise ValueError("Value range must be integer")

        if options.observe:
            active = True

            # only set frequency if resource is observable
            if options.frequency:
                try:
                    frequency = int(options.frequency)
                except ValueError as e:
                    raise ValueError("Observing frequency must be integer")

        # add new resource to resource list
        resources[name] = {'url': url,
                           'channel': channel,
                           'active': active,
                           'frequency': frequency}
        if b_range is True:
            resources[name]['min'] = min
            resources[name]['max'] = max

        # convert resource to payload (add name field)
        payload = resources[name]
        payload['name'] = name

        try:
            yield from post_impl(json.dumps(payload))
        except Exception as e:
            raise RuntimeError("Failed to complete CoAP request: {}".format(e))

    @staticmethod
    @asyncio.coroutine
    def do_resource(name, code='GET', *args):
        global not_alert
        not_alert = True
        """
        General implementation of resource command for GET/PUT

        Once observation starts, use Ctrl + c to end observation

        Syntax: >>>[resource] [code] ([-o]) ([payload])
        resource: full resource list can be acquired by help command
        code: GET/PUT
        -o: following GET to observe this resource

        Example: ``>>>temperature GET -o``
        Example: ``>>>temperature PUT period 5``

        :param str name: name of the resource
        :param str code: type of CoAP request
        :param str[] args: option or payload of PUT request
        :raises AttributeError: resource name or url not found
        :raises ValueError: invalid request code (not GET or PUT)
        :raises RuntimeError: CoAP request failed
        """
        payload = " ".join(args)
        try:
            resource = resources[name]
            url = resource['url']
        except AttributeError and IndexError as e:
            raise AttributeError("Resource name or url not found: {}".format(e))

        #print("do_resource: payload={}".format(payload))
        try:
            if code == 'GET':
                if payload.startswith('-o'):
                    if resource['active'] is True:
                        # Create new event loop for observation
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        try:
                            # Set keyboard interrupt Ctrl+c as method to end observation
                            for signame in ('SIGINT', 'SIGTERM'):
                                loop.add_signal_handler(getattr(signal, signame),
                                                        functools.partial(end_observation, loop))

                            print("Observation running forever...")
                            print("Press Ctrl + c to end observation")
                            loop.run_until_complete(observe_impl(url))
                           
                        finally:
                            # In case of exceptions, must terminate observation loop and
                            #   switch back to client event loop
                            loop.close()
                            not_alert = True
                            asyncio.set_event_loop(client_event_loop)

                    else:   # Resource is not configured to observable
                        yield from get_impl(url)
                       
                        print("Warning: resource is not observable")

                else:
                    yield from get_impl(url)
               
            elif code == 'PUT':
                yield from put_impl(url, payload)

            else:
                raise ValueError("invalid request code")
        except Exception as e:
            raise RuntimeError("Failed to complete CoAP request: {}".format(e))


def client_console():
    """
    Client command line tool

    Initialize as CoAP clients and try contacting server. While
    connecting, accept commands and resource requests from command
    line, then call corresponded CoAP request implementation

    :var bool run_demo: (global) whether to run Octave demonstration
    """
    global run_demo
    global grp

    # Probe server first
    print("\nConnecting to server {}...".format(server_IP))
    # Initialization will be blocked here if server not available
    yield from Commands.do_probe()

    try:
        grp = create_grouph5()
    except Exception as e:
        print("Failed to create HDF5 file{}".format(e))

    print("\nProbing available resources...")
    # Temporarily disable plotting
    run_demo_cache = run_demo
    run_demo = False
    for r in resources:
        # Test GET for each known resource
        yield from Commands.do_resource(r, 'GET')
        print("Success! Resource {} is available at path /{}\n".format(r, resources[r]['url']))
    print("Done probing...")
    # Restore plotting configuration
    run_demo = run_demo_cache

    # Print general info and help menu on console when client starts
    print("Initializing command prompt...\n")
    Commands.do_help()

    # Start acquiring user input
    while True:
        cmdline = input(">>>")
        cmd_parts = cmdline.split()

        # Handle empty input
        if len(cmd_parts) is 0:
            continue

        #print("cmd = {}".format(cmd_parts))
        cmd = cmd_parts[0]
        args = cmd_parts[1:]

        try:
            method = getattr(Commands, 'do_' + cmd)
        except AttributeError:
            if cmd in resources:
                try:
                    yield from Commands.do_resource(cmd, *args)
                except Exception as e:
                    print("Error: {}".format(e))
            else:
                print("Error: no such command.")

        else:
            try:
                # do_help and do_ip and do_exit are not asyncio coroutine
                if method.__name__ == 'do_help' or \
                   method.__name__ == 'do_ip' or \
                   method.__name__ == 'do_exit':
                    method(*args)
                else:
                    yield from method(*args)
            except Exception as e:
                print("Error: {}".format(e))


def main():
    """
    Main function of the client program

    Import parameters and configuration from config file, then start the event loop

    :var str server_IP: (global) server IP address
    :var dict resources: (global) list of available resources on server
    :var str data_file: (global) file to store data for Octave plotting
    :var bool run_demo: (global) whether to run Octave demonstration
    :var BaseEventloop client_event_loop: (global) store client main event loop object
    """
    global server_IP
    global resources
    global data_file
    global run_demo
    global client_event_loop
    global not_alert
    global plotting

     # TODO: **resource info is better acquired from server, provided server's IP** probably done with the addition of the lines above
   
# Given the server's IP, the username and password, acquire the configuration json file using sftp and store it into the client folder until the next program execution (It's a little bit slow, maybe it will be necessary to optimize this feature

    not_alert = True
    plotting, = plt.plot([], [])
    print(plotting)
    try:
        ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('192.168.2.20', username='pi', password = 'raspberry')
        sftp = ssh.open_sftp()
        sftp.get('POEModule-master/POEModule-master/config.json', 'config.json') 
        sftp.close()
        ssh.close()
        with open('config.json') as config_file:
            data = json.load(config_file)
            server_IP = data['server']['IP']
            data_file = data['client']['datafile']
            demo_config = data['client']['demo']
            # re-format each sensor entry for client to use
            for r in data['sensors']:
                resources[r['name']] = {i: r[i] for i in r if i != 'name'}
            # add default activeness as "false" - i.e. not observable
            for r in resources:
                if 'active' not in resources[r]:
                    resources[r]['active'] = False
    except Exception as e:
        print("Failed to parse config file form server: {}".format(e))
        print("Exiting client!!!")
        h5_file.close()
        return
  
    #print("{}".format(resources))

    if run_demo is True and demo_config is True:
        # Setup octave for data visualization and storage
        print("Initializing Octave database and visualizer...")
        octave.addpath('./')
        try:
            octave.demo_init(data_file)
            # Wait for Octave initialization to complete
            time.sleep(0.5)
        except Exception as e:
            print("Failed to initialize demo script: {}".format(e))
            print("Disabling Octave script...")
            run_demo = False
    else:
        # Turn off demo if oct2py module not present or config to not demo
        print("Disabling Octave script...")
        run_demo = False

    try:
        loop = asyncio.get_event_loop()
        # Keep a global record of the event loop for client
        client_event_loop = loop
        # Start client console
        loop.run_until_complete(client_console())

    except Exception as e:
        print("{}".format(e))

if __name__ == '__main__':
    main()
