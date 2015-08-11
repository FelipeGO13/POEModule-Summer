"""
    Created on November 22, 2014
    Last modified on July 7, 2015 by Felipe Gabriel Osorio
    
    @author: Ruibing Zhao
    @author: Yaodong Yu
    @author: Felipe Gabriel Osorio
    @author: Yuan Liu
    @author: Xinran Ma

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
import inspect
import threading
import matplotlib.pylab as plt

from tkinter import *
from tkinter.ttk import *
from tkinter_async import *
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

class Gui_cancel(Frame):

    def __init__(self, master):
        global end_obs
          
        master.config(takefocus=True)
        master.title("Cancel observation")
        end_obs = False
        lbl = Label(master, text = "To stop the observation, please press the button below")
        lbl.grid(row=0, column = 0, pady =5)
        cancelBtn = Button(master, text="Cancel", command = obs_over)
        cancelBtn.grid(row=1, column=0, pady=5) 

    def hide(master):
        master.withdraw()

    def reveal(master):
        master.deiconify()

def tkinterGui():
    global cancel_obs
    global btnCancel
    global end_obs
    if (end_obs == False) & (btnCancel == False):
        cancel_obs = Tk()
        app = Gui_cancel(cancel_obs)
        btnCancel = True
        cancel_obs.mainloop()

def obs_over():

    global end_obs
    global Gui_cancel
    global cancel_obs

    Gui_cancel.hide(cancel_obs)
    end_obs = True
    
def gui_builder(root, get_cb, obs_cb, put_cb, post_cb, help_cb, respawn=Respawn.CONCURRENT):
  
    global rsc
    global rscAvl
    global display

    frame = Frame(root)
    frame.columnconfigure(1, weight=1)
    frame.columnconfigure(2, pad=5)
    frame.rowconfigure(6, weight = 1) 
    frame.rowconfigure(5, pad=5)    
    
    @asyncio.coroutine
    def submit_get():
        yield from get_cb()
        
    @asyncio.coroutine
    def submit_put():
        yield from put_cb()

    @asyncio.coroutine
    def submit_post():
        yield from post_cb()
  
    @asyncio.coroutine
    def submit_obs():
        yield from obs_cb()

    @asyncio.coroutine
    def submit_close():
        Commands.do_exit()
        os._exit(1)

    @asyncio.coroutine
    def submit_help():
        yield from help_cb()    

    rscLbl= Label (frame, text='Resources available: ')
    rscLbl.grid(row=0, column=0, padx=5, pady=5)
        
    rsc = ('')
                
    rscAvl = Combobox(frame, state='readonly')
    rscAvl.grid(row=0, column=1, pady=5, stick='w')

    getBtn = Button(frame, text="Get", command = spawn(submit_get, respawn = respawn))
    getBtn.grid(row=1, column=2, pady=5)

    putBtn = Button(frame, text="Put", command = spawn(submit_put, respawn = respawn))
    putBtn.grid(row=2, column=2, pady=5)

    postBtn = Button(frame, text="Post", command = spawn(submit_post, respawn = respawn))
    postBtn.grid(row=3, column=2, pady=5)

    obsBtn = Button(frame, text="Observe", command = spawn(submit_obs, respawn = respawn, debug = False))
    obsBtn.grid(row=4, column=2, pady=5)
         
    display = Text(frame, state="disabled")
    display.grid(row=1, column=0, columnspan=2, rowspan=6, padx=5, sticky=E+W+S+N)
        
    helpBtn = Button(frame, text='Help', command = spawn (submit_help))
    helpBtn.grid(row=7, column=0, padx = 5, pady=5, sticky=W)
        
    closeBtn = Button(frame, text='Close', command = spawn(submit_close))
    closeBtn.grid(row=7, column=2, padx = 5, pady=5)

    update_resources(resource_list)
    insertText("Welcome to the Sensor network manager\n")         

    return frame

@asyncio.coroutine
def tk_app():
  
    global rscAvl
    global resource_list
    
    root = Tk()
    root.title("Sensor Network Manager") 
    @asyncio.coroutine
    def set_get():
        print(rscAvl.get())
        yield from Commands.do_resource(rscAvl.get())

    @asyncio.coroutine
    def set_put():
        top = Toplevel()
        top.title('Put - {}'.format(rscAvl.get()))
         
        lab = Label(top, text='Define the parameter that you want to change')
        lab.grid(row = 0, column = 0, columnspan = 2,  pady=2, padx=2)

        labMsg = Label(top, text='Parameter')
        labMsg.grid(row = 1, column = 0)        

        msg = Entry(top)
        msg.grid(row = 1, column = 1, pady=2, padx=2)

        confirmBtn = Button(top, text = 'Confirm', command = spawn(lambda: comb_func1(top, msg.get())))
        confirmBtn.grid(row = 2, column = 0)
        cancelBtn = Button(top, text = 'Cancel', command = spawn(lambda: close_popup(top))).grid(row = 2, column = 1)  

    @asyncio.coroutine
    def set_post():
        
        top = Toplevel()
        top.title('Post')  

        obs = IntVar()      

        lab = Label(top, text = 'New resource addition').grid(row = 0, column = 0, columnspan = 1)

        labName =  Label(top, text = 'Resource name').grid(row = 1, column = 0, padx = 2, pady = 2)
        name = Entry(top)
        name.grid(row = 1, column = 1, padx = 2, pady = 2)

        labUrl = Label(top, text = 'Resource url').grid(row = 2, column = 0, padx = 2, pady = 2)
        url = Entry(top)
        url.grid(row = 2, column = 1, padx = 2, pady = 2)

        observable = Checkbutton(top, text = 'Observable', variable = obs,  onvalue = 1, offvalue = 0)
        observable.grid(row = 3, pady = 2, padx = 2)

        labFreq = Label(top, text = "Observe Frequency").grid(row =4, column = 0, padx = 2, pady = 2)
        freq = Entry(top)
        freq.grid(row = 4, column = 1, pady = 2, padx = 2)

        labMax = Label(top, text = "Maximum limit").grid(row = 5, column = 0, pady = 2, padx = 2)
        maxEntry = Entry(top)
        maxEntry.grid(row = 5, column = 1, pady = 2, padx = 2)

        labMin = Label(top, text = "Minimum limit").grid(row = 6, column = 0, pady = 2, padx = 2)
        minEntry = Entry(top)
        minEntry.grid(row = 6, column = 1, pady = 2, padx = 2)

        labAdc = Label(top, text = "ADC channel").grid(row = 7, column =0, pady = 2, padx = 2)
        adc  = Entry(top)
        adc.grid(row = 7, column = 1, pady = 2, padx = 2)

        confirmBtn = Button(top, text = 'Confirm', command = spawn(lambda: comb_func2(top, name.get(), adc.get(), url.get(), obs.get(), freq.get(), maxEntry.get(), minEntry.get()))).grid(row = 8, column = 0)

        cancelBtn = Button(top, text = 'Cancel', command = spawn(lambda: close_popup(top))).grid(row = 8, column = 1)

    @asyncio.coroutine
    def do_post(name, adc, url, obs, freq, maxLim, minLim):
        post_attr = ''
        frame = inspect.currentframe()
        args, _, _, values = inspect.getargvalues(frame)
        for i in args:
            print("{} = {}".format(i, values[i]))
            if (i == 'adc') & (values[i] != ''):
                post_attr += "-c{} ".format(int(values[i]))
            elif (i == 'url') & (values[i] != ''):
               post_attr += "-u {} ".format(values[i])
            elif (i == 'obs') & (values[i] == 1):
               post_attr += "-o "
            elif (i == 'freq') & (values[i] != ''):
                post_attr += "-f{} ".format(values[i])
            elif (i == 'maxLim') & (values[i] != ''):
                post_attr += "-m{} ".format(values[i])
            elif (i == 'minLim') & (values[i] != ''):
                post_attr += "-l{} ".format(values[i])
          
        yield from Commands.do_add(name, '{}'.format(post_attr))

    @asyncio.coroutine
    def set_help():

        help_txt = '\nThis program is the graphic management interface of the sensor network system.\n Users can conveniently and securely control the system, collecting data from the different resources,\n configure sensor parameter or add new sensors using the Sensor Network Manager.\n'

        help_rsc = 'All the available resources are displayed in the field at the top of the screen. \n To select one of them to manage, \nexpand the box clicking in the small arrow and click in the resource url. \n The resource selected can be modified at any time.\n'

        help_get = 'The GET command collects data from the selected resource in the resources field, displaying the obtained results in the screen, \nshowing a graph with all the last obtained data and, finally, saving the results in the HDF5 database. \n Execute a GET command only returns one result, \nif it is necessary to collect more than one set of data check the Observe command.\n'
       
        help_put = 'The PUT command allows the changing of a parameter of the seleceted resource in the resources field.\n Clicking in this button, a new window will be displayed containing a field to insert the parameter and its new value. \n To complete the modification just press the button "Confirm" \nand a message will be displayed in the screen confirm the success of the modification. \n '

        help_post = 'The POST command adds a new temporary resource, that can be accessed until the end of the application.\n Pressing the POST button a new window will be displayed, containing the following fields to be completed: \n Resource name - Name of the new resource\n Resource url - URL of the new resource that will be used by the management tools (Sensor Network Manager and Copper) for identification \n Observable - Defines observation status of the new resource \n Observe frequency - Defines the period of the observation in seconds \n Maximum and minimum limits: Define the measurement limits of the new resource \n ADC channel - Defines the number of the adc channel used by this new resource\n To complete the addition of the new resource just press the button "Confirm" \nand a message will be displayed in the screen confirm the success of the modification.'

        help_obs = 'The OBSERVE command collects data from the selected resource in the resources field, \n obtaining results several times following a pre-configured frequency. \n The OBSERVE command execution is similar to the GET command, however additional features are executed and they are: \n Real-Time monitoring - Executing a observe command a real-time graphical visualization will be displayed, presenting no only all the past results, \nbut also the current collected data, maximum and minimum values and average.\n Smart power management - A observe command also triggers the smart power management, \na feature that automatically enable additonal modules in case of unexpected events that generates abnormal data.\n During the observation is not possible to execute any other function of the Sensor Network Manager. \n To stop an observation press the "Cancel" button in the additional pop-up.'
 
        top = Toplevel()
        top.title("Sensor Network Manager Help\n")
        
        def help(title, txt):
            lblRscTitle.config(text = title)
            lblRsc.config(text = txt)
            
        lbl = Label(top, text = 'Welcome to the Sensor Network Manager', font = 'helvetica 12 bold')
        lbl.grid(row = 0, column = 0, columnspan = 5)
        
        lblContent = Label(top, justify = 'center', text = help_txt)
        lblContent.grid(row = 1, column = 0,  columnspan = 5)
   
        lblRscTitle = Label(top, font = "helvetica 10 bold")      
        lblRscTitle.grid(row = 4,  column = 0,  columnspan = 5)    

        lblRsc = Label(top, font = "helvetica 10", justify = 'center')      
        lblRsc.grid(row = 5,  column = 0,  columnspan = 5)    
        
        btnLbl = Label(top, text = 'To obtain more information about the possible commands and features select use the buttons below\n')
        btnLbl.grid(row = 2, column = 0,  columnspan = 5)
         
        rscBtn = Button(top, text = 'Resources', command  = lambda: help('\nResources', help_rsc))
        rscBtn.grid(row = 3, column = 0)
 
        getBtn = Button(top, text = 'Get', command  = lambda: help('\nCommands: Get', help_get))
        getBtn.grid(row = 3, column = 1)

        putBtn = Button(top, text = 'Put', command  = lambda: help('\nCommands: Put', help_put))
        putBtn.grid(row = 3, column = 2)

        postBtn = Button(top, text = 'Post', command  = lambda: help('\nCommands: Post', help_post))
        postBtn.grid(row = 3, column = 3)

        obsBtn = Button(top, text = 'Observe', command  = lambda: help('\nCommands: Observe', help_obs))
        obsBtn.grid(row = 3, column = 4)

    @asyncio.coroutine
    def comb_func2(top, name, adc, url, obs, freq, maxEntry, minEntry):

        yield from close_popup(top)
        yield from do_post(name, adc, url, obs, freq, maxEntry, minEntry)
        resource_list.append(name)
        update_resources(resource_list)

    @asyncio.coroutine
    def comb_func1(top, msg):

        yield from close_popup(top)
        yield from do_put(msg)
    
    @asyncio.coroutine
    def close_popup(top):
        top.destroy()
    
    @asyncio.coroutine
    def do_put(msg):
        
        yield from Commands.do_resource(rscAvl.get(), 'PUT', msg)

    @asyncio.coroutine
    def set_obs():
        
        global cancel
        global btnCancel
        global Gui_cancel
        global cancel_obs

        if btnCancel == False:
            cancel = threading.Thread(target=tkinterGui)
            cancel.start()
        else:
            Gui_cancel.reveal(cancel_obs)

        yield from Commands.do_resource(rscAvl.get(), 'GET', '-o')
 
    gui_builder(root, set_get, set_obs, set_put, set_post, set_help, Respawn.CONCURRENT).pack()

    yield from async_mainloop(root)

@asyncio.coroutine
def run():

    global grp
    global graph
    global obs_resource
    global obs_activated
    global power
    global switch_IP
    global probing
    global resource_list
    global display_text
 
    resource_list = []

    probing = True
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

    probing = False
    # Print general info and help menu on console when client starts

    if obs_activated == True:
         yield from Commands.do_resource(obs_resource, 'GET', '-o')
         
    print("Initializing client GUI...\n")
    Commands.do_help()
    graph = False
 
    yield from tk_app()

def insertText(text):

    global display

    display.configure(state="normal")
    display.insert(INSERT, '{}... \n'.format(text))
    display.configure(state="disabled")

def update_resources(resources):

    global rscAvl

    rscAvl.configure(values = resources)
              
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
    port = '2/5'
    with open('config {}.json'.format(server_IP)) as config_file:
        config = json.load(config_file)
        length = len(config['sensors'])
        time = config['server']['visualization time']
        if status == main:  
            port = config['server']['additional modules'][0]['port']
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
                    stdin, stdout, stderr = ssh.exec_command("show power inline gi {}".format(port))
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

def create_comptype(jpl): 
    """
    Dynamic formatting for the compound type that defines the datatypes of the dataset columns
    """
    global temp_comptype

    data = json.loads(jpl['data']) 
    columns = []
    types = []
    i = 0
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
                                insertText("Second module enabled!")
                                ssh.close() 
                                add_num = len(config['server']['additional modules'])

                                if add_num == 1:
                                    ip = config['server']['additional modules'][0]['ip']
                                    terminal = subprocess.Popen(['gnome-terminal', '-x', 'python3', 'mod_client_stdioV2.py', '-s', '{}'.format(ip), '-o', '{}'.format(obs_resource)])
                                else:

                                    for y in range(0, add_num-1):
                                        ip = config['server']['additional modules'][y]['ip']
                                        terminal = subprocess.Popen(['gnome-terminal', '-x','python3', 'mod_client_stdioV2.py', '-s', '{}'.format(ip), '-o', '{}'.format(obs_resource)])
                                
                            return False
    return True

def incoming_data(response, url):
    """
    Function used to deal with response

    :param response: response from CoAP server
    :param response: aiocoap.message.Message
    """
    global jpayload
    global probing
    global loop_obs

    jpayload = 0
    payload = response.payload.decode(UTF8)

    if (response.opt.content_format is not JSON_FORMAT_CODE):
        print("Result:\n{}: {}".format(response.code, payload))
        if probing == False:
            insertText("Result:\n{}: {}".format(response.code, payload))
    else:
        jpayload = json.loads(payload)
        print("Result (JSON):\n{}: {}".format(response.code, jpayload))
        if probing == False:
            insertText("Result (JSON):\n{}: {}".format(response.code, jpayload))    
       
        try:
            if (grp.__contains__(url)) & (probing == False):
                dset = grp.__getitem__(url)
                store_data(dset, jpayload) 
            elif (grp.__contains__(url)) & (probing == True):
                print("Resource available and ready to provide data")
            else:
                insert_dataset(grp, url, create_comptype(jpayload))
                print("All data will be stored in the HDF5 file")
    
        except Exception as e:
            print("Failed to store in a dataset {}/ {}".format(url, e))
       
    if end_obs == True:
        end_observation(loop_obs)    

def end_observation(loop_obs):

    """
    Callback function used for ending observation to resource on client side.

    :param BaseEventLoop loop: event loop for observing resource
    """
    # FIXME: method should actually end observation on server.
    #       Now, it only deals with client side

    global graph
    global end_obs

    print("Observation ended by user interrupt...")
    # Terminate observation event loop
    loop_obs.close()
    graph = False
    end_obs = False
    
    insertText("Observation loop ended in the client...")

@asyncio.coroutine
def post_impl(jargs, url):
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
        global resource_list

        if command:
            print(getattr(Commands, 'do_'+command).__doc__)
        else:
            commands = [cmd[3:] for cmd in dir(Commands)
                        if cmd.startswith('do_') and cmd != 'do_resource']
            print("Valid commands: " + ", ".join(commands))
            print("Valid resources: " + ", ".join(resources))
            resource_str = ", ".join(resources)
            resource_list = resource_str.split(", ")
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
        global gui
        
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
        os._exit(1)
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
                channel = int(options.channel[:1])
            except ValueError as e:
                raise ValueError("Channel must be integer")

        # default value of other options
        url = name
        active = False
        frequency = 0
        b_range = False
        min = None
        max = None
        print(url)
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
            yield from post_impl(json.dumps(payload), url)
        except Exception as e:
            raise RuntimeError("Failed to complete CoAP request: {}".format(e))

    @staticmethod
    @asyncio.coroutine
    def do_resource(name, code='GET', *args):
        global not_alert
        global loop_obs
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

        try:
            if code == 'GET':
                if payload.startswith('-o'):
                    if resource['active'] is True:
                        # Create new event loop for observation
                        loop_obs = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop_obs)
                        
                        try:
                            # Set keyboard interrupt Ctrl+c as method to end observation
                            for signame in ('SIGINT', 'SIGTERM'):
                                loop_obs.add_signal_handler(getattr(signal, signame),
                                                        functools.partial(end_observation, loop_obs))
                            print("Observation running forever...")
                            print("Press Ctrl + c to end observation")
                            start = datetime.datetime.now()
                            
                            loop_obs.run_until_complete(observe_impl(url))
                        finally:
                            # In case of exceptions, must terminate observation loop and
                            #   switch back to client event loop
                            loop_obs.close()
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
  
def main(argv):
    """
    Main function of the client program

    Import parameters and configuration from config file, then start the event loop

    :var str server_IP: (global) server IP address
    :var dict resources: (global) list of available resources on server
    :var BaseEventloop client_event_loop: (global) store client main event loop object
    :var boolean not_alert: (global) store alert status
    :var Matplotlib.pylab plotting: (global) initialize the plotting variable indicating its shape  
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
    global resource_list
    global gui
    global end_obs
    global btnCancel
    global power 


    import argparse
    
    end_obs = False
    not_alert = True
    btnCancel = False
    plotting, = plt.plot([], [])
    graph = False
    power = 0        
	 
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
    except Exception as e:
        print("An error ocurred opening or creating the HDF5 file {}".format(e))
  
    try:
        loop = asyncio.get_event_loop()
        # Keep a global record of the event loop for client
        client_event_loop = loop
        # Start client console
        loop.run_until_complete(run())
       
    except Exception as e:
        print("{}".format(e))

if __name__ == '__main__':
    main(sys.argv[1:])
