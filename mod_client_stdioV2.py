"""
    Created on November 22, 2014
    Last modified on July 7, 2015 by Felipe Gabriel Osorio
    
    @author: Ruibing Zhao
    @author: Yaodong Yu
    @author: Felipe Gabriel Osorio

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

from aiocoap import *
from defs import *
																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																													
# Default client configuration:
# IP is (local) 127.0.0.1
server_IP = 'localhost'
# Alert is not on
not_alert = True
# Plot is initialized with empty axis 
plotting, = plt.plot([], [])
# resources independent from hardware implementation
resources = {'hello': {'url': 'hello'},
             'time': {'url': 'time'}}
# ssh connection to get config file from server
ssh = paramiko.SSHClient() 
# asyncio event loop for																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																															 client
# Keep a record so that it can be switched back after observation
client_event_loop = asyncio.get_event_loop()

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
    global h5_file
    try:
        module = server_IP
        if h5_file.__contains__(module):
            print("Module {} already recorded in the database".format(module))
            grp = h5_file.__getitem__(module)
            grp.attrs["Last access"] = str(datetime.datetime.now())  
        else:
            grp = h5_file.create_group("{}".format(server_IP))
            with open('config {}.json'.format(server_IP)) as config_file:
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
        with open('config {}.json'.format(server_IP)) as config_file:
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

def store_data(dset, jpl):
    """
    Create a new tuple and store the obtained data from sensors in the datasets, identifying 
    the column by the json file received as response from the server. Also, enables the data     visualization and the smart power managent system.
    """
    global not_alert
    global plotting
    global ax
    global text
    global graph
    global start
    global server_IP
    global timer
    global terminal
    global power
    global status
    global switch_IP
    
    # Indicates when the alert is activated (True = Alert off/ False = Alert on)
    not_alert = True

    with open('config {}.json'.format(server_IP)) as config_file:
        config = json.load(config_file)
        length = len(config['sensors'])
        time = config['server']['visualization time']  
        print (time)  
        for x in range(0, length-1):
            if jpl['name'] == config['sensors'][x]['name']:
                sensor = config['sensors'][x]
				
    # Creates the data visualization if it is not enabled
    if graph == False:
	# Plots the data visualization
        plt.figure(1)
        plotting, = plt.plot(dset[jpl['name']], color='black')
        plt.ylim([(sensor['min_limit']*2), (sensor['max_limit']*2)])
        plt.xlabel("Number of measurements")
        plt.ylabel(jpl['name'])
        plt.title("Real-Time Visualization {}".format(server_IP))
        plt.axhline(y=sensor['max_limit'], c='red')
        plt.axhline(y=sensor['min_limit'], c='red')
        ax = plt.gca()
        
        textstr = 'Average = %.2f\nMaximum=%.2f\nMinimum=%.2f'%(numpy.mean(dset[jpl['name']]), max(dset[jpl['name']]), min(dset[jpl['name']])) 
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        text = ax.text(0.01, 0.95, textstr, transform=ax.transAxes, fontsize=14, verticalalignment='top', bbox=props)

        plt.show(block=False)
        graph = True

    data = json.loads(jpl['data']) 
    avg = 0

    for key in jpl.keys():
        if key == 'data':
            for key in data.keys():
			
                dset[key, dset.len()-1] = data[jpl['name']]
                avg_trunc = "%.4f"%numpy.around(numpy.mean(dset[key]), decimals=4)
                avg = float(avg_trunc)
                
                if status == 'main':
		    # Connect to switch and reads the power available in the second module
                    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(switch_IP, username='group94', password = 'upoe94')
                    stdin, stdout, stderr = ssh.exec_command("show power inline gi 2/5")
                    power = float(stdout.read()[310: 320])
                    ssh.close() 
                else:
                    power = 0

	        #Checks if alert is on, otherwise verify if data is in the normal range
                if (not_alert is True) & (power == 0) :
                    not_alert = alert(data, dset)  
                    start = datetime.datetime.now()
                else:
                    print("alert not activated")    
                
                if type(plotting.get_xdata()) is not int:
                    next = len(plotting.get_xdata()) + 1
                else:
                    next = plotting.get_xdata()+1

                plotting.set_ydata(numpy.append(plotting.get_ydata(), data[jpl['name']]))
                plotting.set_xdata(numpy.insert(plotting.get_xdata(), (next-1), next))
               
                ax.relim()
                ax.autoscale_view()
                
                textstr = 'Average = %.2f\nMaximum=%.2f\nMinimum=%.2f'%(numpy.mean(dset[key]), max(dset[key]), min(dset[key])) 
                text.set_text(textstr)
                plt.draw()
        else: 
            try:          
                dset['{}'.format(key), dset.len()-1] = jpl[key]
            except Exception as e: 
                print('') 

    dset['average', dset.len()-1] = avg       
    dset.resize(dset.len()+1, 0)

    now = datetime.datetime.now()
    diff = now-start

    #Disable the additional model after 30 seconds (Need to include configurable time)
    if float(diff.total_seconds()) > timer:
          if status in 'additional':
              print('finishing data collection')
              h5_file.close()
              sys.exit(0)
          else:
              ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
              ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
              ssh.connect(switch_IP, username='group94', password = 'upoe94')
              stdin, stdout, stderr = ssh.exec_command("tclsh bootflash:poe_shutdown.tcl")
              print("Second module disabled!")
              terminal.kill()
              ssh.close() 
              start = datetime.datetime.now()
    else:
        print("Second module still working")
    
    print("Data successfully recorded in the database!")

#Testing dynamic datatype formatting

def create_comptype(jpl): 
    """
    Dynamic formatting for the compound type that defines the datatypes of the dataset columns
    """
    global temp_comptype
    data = json.loads(jpl['data']) 
    columns = []
    types = []
    i=0
    columns.extend([None]*len(jpl.keys()))
    types.extend([None]*len(jpl.keys()))
    a = []
    for x in range(0, len(jpl.keys())):
        a.append((str(x), 'i'))
    temp_comptype = numpy.dtype(a)
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
    comp_type = temp_comptype.descr
    columns[len(jpl.keys())-1] = 'average'
    types[len(jpl.keys())-1] = 'f'
    for x in range(0, len(comp_type)):
        comp_type[x] = (columns[x], types[x])
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

    """
    Verify if is necessary to trigger the alert, activating the additional module using a SSH connection
    """ 
    global plotting
    global plotting2
    global ax
    global text
    global obs_resource
    global terminal
    
    with open('config {}.json'.format(server_IP)) as config_file:
        config = json.load(config_file)
        length = len(config['sensors'])     
        for key in data.keys():
            for x in range(0, length-1):
                if key == config['sensors'][x]['name']:
                    sensor = config['sensors'][x]
                    obs_resource = key
                    if dset.attrs.__contains__(key):
                        if (float(data[key]) > sensor['max_limit']) | (float(data[key]) < sensor['min_limit']):
                            print('Alert activated!')
                            if status == 'main':
                                ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
                                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                                ssh.connect(switch_IP, username='group94', password = 'upoe94')
                                stdin, stdout, stderr = ssh.exec_command("tclsh bootflash:poe.tcl")
                                print("Second module enabled!")
                                ssh.close() 

                                add_num = len(config['server']['additional modules'])
                                if add_num == 1:
                                    ip = config['server']['additional modules'][0]['ip']
                                    terminal = subprocess.Popen(['gnome-terminal', '-x', 'python3', 'mod_client_stdio.py', '-s', '{}'.format(ip), '-o', '{}'.format(obs_resource)])
                                else:
                                    for y in range(0, add_num-1):
                                        ip = config['server']['additional modules'][y]['ip']
                                        terminal = subprocess.Popen(['gnome-terminal', '-x','python3', 'mod_client_stdio.py', '-s', '{}'.format(ip), '-o', '{}'.format(obs_resource)])
                            
                            
                            return False
    return True

def incoming_data(response, url):
    """
    Function used to deal with response

    :param response: response from CoAP server
    :param response: aiocoap.message.Message
    """
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

            else:
                insert_dataset(grp, url, create_comptype(jpayload))
                print("All data will be stored in the HDF5 file")

        except Exception as e:
            print("Failed to store in a dataset {}/ {}".format(url, e))
       
def end_observation(loop):
    """
    Callback function used for ending observation to resource on client side.

    :param BaseEventLoop loop: event loop for observing resource
    """
    # FIXME: method should actually end observation on server.
    #       Now, it only deals with client side
    global graph
    print("Observation ended by user interrupt...")
    # Terminate observation event loop
    loop.close()
    graph = False
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
        global power
        global h5_file
        global status
        global switch_IP

        if power != 0:
            ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(switch_IP, username='group94', password = 'upoe94')
            stdin, stdout, stderr = ssh.exec_command("tclsh bootflash:poe_shutdown.tcl")
            print("Second module disabled!")
            ssh.close() 

        if status == 'main':
            h5_file.flush()
            with open('config {}.json'.format(server_IP)) as config_file:
                config = json.load(config_file)
                add_num = len(config['server']['additional modules'])
                if add_num == 1:
                    ip = config['server']['additional modules'][0]['ip']
                    add_file = h5py.File("{}.hdf5".format(ip), "a")
                    subprocess.call(['h5merge','-i','{}'.format(add_file.filename), '-o', '{}'.format(h5_file.filename)])
                    os.remove("{}.hdf5".format(ip))
                else:
                    for y in range(0, add_num-1):
                        ip = config['server']['additional modules'][y]['ip']
                        add_file = h5py.File("{}.hdf5".format(ip), "a")
                        subprocess.call(['h5merge','-i','{}'.format(add_file.filename), '-o', '{}'.format(h5_file.filename)])
                        os.remove("{}.hdf5".format(ip))
        h5_file.close()
        print("Goodbye!")
        print("Exiting...")
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
        global start
        start = 0
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
                            start = datetime.datetime.now()
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

    """
    global grp
    global graph
    global obs_resource
    global obs_activated
    global power
    global switch_IP

    # Probe server first
    print("\nConnecting to server {}...".format(server_IP))
    # Initialization will be blocked here if server not available
    yield from Commands.do_probe()
    
    try:
        grp = create_grouph5()
    except Exception as e:
        print("Failed to create HDF5 file{}".format(e))

    print("\nProbing available resources...")
    for r in resources:
        # Test GET for each known resource
        yield from Commands.do_resource(r, 'GET')
        print("Success! Resource {} is available at path /{}\n".format(r, resources[r]['url']))
    print("Done probing...")

    # Print general info and help menu on console when client starts
    if obs_activated == True:
         yield from Commands.do_resource(obs_resource, 'GET', '-o')
         
    print("Initializing command prompt...\n")
    Commands.do_help()
    graph = False
    if power != 0:
        ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(switch_IP, username='group94', password = 'upoe94')
        stdin, stdout, stderr = ssh.exec_command("tclsh bootflash:poe_shutdown.tcl")
        print("Second module disabled!")
        ssh.close() 
        start = datetime.datetime.now()

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

def main(argv):
    """
    Main function of the client program

    Import parameters and configuration from config file, then start the event loop

    :var str server_IP: (global) server IP address
    :var dict resources: (global) list of available resources on server
    :var BaseEventloop client_event_loop: (global) store client main event loop object
    """
    global server_IP
    global resources
    global client_event_loop
    global not_alert
    global plotting
    global graph
    global visualize 
    global h5_file
    global obs_resource
    global obs_activated
    global timer
    global status
    global switch_IP
    
    import argparse
   
# Given the server's IP as parameter, the username and password, acquire the configuration json file using sftp and store it into the client folder until the next program execution (It's a little bit slow, maybe it will be necessary to optimize this feature

    not_alert = True
    plotting, = plt.plot([], [])
    graph = False
        	 
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('-s', '--server_ip', help="IP of the required module")
    p.add_argument('-o', '--observe', help="Observate a required resource")

    options = p.parse_args(argv)

    if options.server_ip:
        server_IP = options.server_ip
    if options.observe:
        obs_activated = True  
        obs_resource = options.observe
    else:
        obs_activated = False 
    if obs_activated == True:
        time.sleep(45)

    try:
        ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server_IP, username='pi', password = 'raspberry')
        sftp = ssh.open_sftp()
        sftp.get('POEModule-master/POEModule-master/config.json', 'config {}.json'.format(server_IP)) 
        sftp.close()
        ssh.close()

        with open('config {}.json'.format(server_IP)) as config_file:
            data = json.load(config_file)
            server_IP = data['server']['IP']
            status = data['server']['status']
            timer = data['server']['visualization time']
            switch_IP = data['server']['switch IP']
            print(switch_IP)
            # re-format each sensor entry for client to use
            for r in data['sensors']:
                resources[r['name']] = {i: r[i] for i in r if i != 'name'}
            # add default activeness as "false" - i.e. not observable
            for r in resources:
                if 'active' not in resources[r]:
                    resources[r]['active'] = False
    except Exception as e:
        print("Failed to parse config file from server: {}".format(e))
        print("Exiting client!!!")
        return

    # Creating HDF5 file or opening an existing one
    try:
        h5_file = h5py.File("{}.hdf5".format(server_IP), "a")
        print("HDF5 File succefully created or accessed")
    except:
        print("An error ocurred opening or creating the HDF5 file")
  
    #print("{}".format(resources))

    try:
        loop = asyncio.get_event_loop()
        # Keep a global record of the event loop for client
        client_event_loop = loop
        # Start client console
        loop.run_until_complete(client_console())

    except Exception as e:
        print("{}".format(e))

if __name__ == '__main__':
    main(sys.argv[1:])
