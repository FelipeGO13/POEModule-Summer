import sys
import time
import logging
import json
import paramiko
import os
import subprocess

# IP is (local) 127.0.0.1
server_IP = 'localhost'
# ssh connection to get config file from server
ssh = paramiko.SSHClient() 

# logging configuration
logging.basicConfig(level=logging.INFO)

def validate_json(server_IP):
     """
     Validate the modified configuration file, checking syntax and requesting
     the modification of any error, re-opening the editor (gedit)
     """
     with open('config {}.json'.format(server_IP)) as config_file:
         try:
              data = json.load(config_file)
         except Exception as e:
              print("The configuration file presented an error {}, please review the configuration file".format(e))
              update_config(server_IP)

def update_config(server_IP):
    """
    Allows the user to modify the configuration file, opening it in a file editor (gedit).
    If the file is valid (verify using validate_json), the file is updated in the controller module
    using SFTP to complete the transference
    """
    try:
        edit = subprocess.call(['gedit', 'config {}.json'.format(server_IP)])
    except: 
        print("Failed to open gnome editor to configure file: {}".format(e))
    
    try:
        validate_json(server_IP)
    except Exception as e:
        return      
 
    try:
        ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server_IP, username='pi', password = 'raspberry')
        sftp = ssh.open_sftp()
        sftp.put('config {}.json'.format(server_IP), 'POEModule-master/POEModule-master/config.json') 
        sftp.close()
        ssh.close()
        print("Configuration file of the module {} updated".format(server_IP))
    except Exception as e:
        print("Failed to parse config file from server: {}".format(e))
        edit.kill()
        return

def download_config(server_IP):
    """
    Downloads the last version of the configuration file available in the controller module, using SFTP
    """
    try:
        ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server_IP, username='pi', password = 'raspberry')
        sftp = ssh.open_sftp()
        sftp.get('POEModule-master/POEModule-master/config.json', 'config {}.json'.format(server_IP)) 
        sftp.close()
        ssh.close()
        print("Configuration file of the module {} downloaded".format(server_IP))
    except Exception as e:
        print("Failed to parse config file from server: {}".format(e))
        print("Exiting client!!!")
        return

def main(argv):
"""
    Main function of the client program

    Check flags to execute the two possible functions 

    :var str server_IP: (global) server IP address
"""
    global server_IP
    
    import argparse
       	 
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('-s', '--server_ip', help="IP of the required module")
    p.add_argument('-e', '--edit', action='store_true', help="Allows the updating of the configuration file")
    options = p.parse_args(argv)   

    if options.server_ip:
        server_IP = options.server_ip
        download_config(server_IP)
    if options.edit:
        update_config(server_IP)

if __name__ == '__main__':
    main(sys.argv[1:])
