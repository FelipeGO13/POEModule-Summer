"""
    Created on November 21, 2014
    Last modified on April 16, 2015 by Yaodong Yu

    @author: Yaodong Yu

    This is a command line tool developed as a CoAP client for demonstration of UBC ECE 2014 Capstone Project #94.
    The implementation of this CoAP client is based on aiocoap module

    Reference: https://aiocoap.readthedocs.org/

    Python3.4 is required
"""

import json
import datetime

from defs import *

# payload wrapper fields
NAME_FIELD = 'name'
ACTIVE_FIELD = 'active'
SAMPLE_R_FIELD = 'rate'
DATA_FIELD = 'data'
TIME_FIELD = 'time'


class PayloadWrapper:
    """
    PayloadWrapper is helper class to fill PayloadTable class object with given resource data
    """

    @staticmethod
    def wrap(data, wrapper):
        """
        Fill PayloadTable with given data, jsonize and encode it

        :param json data: resource data to be filled in
        :param PayloadTable wrapper: table to be filled
        :return: filled, jsonized and encoded PayloadTable
        """
        wrapper.set_time(str(datetime.datetime.now()))
        wrapper.set_data(data)

        # FIXME: PayloadWrapper shouldn't deal with json or encoding the table
        return json.dumps(wrapper).encode(UTF8)


class PayloadTable(dict):
    """
    PayloadWrapper class is to create a dictionary wrapper to hold resource data and customized header information
        such as sensor name and properties and data timestamp
    """

    def __init__(self, name='', is_active=False, rate=0):
        """
        Constructor of PayloadTable class. By default, it creates an empty table

        :param str name: resource name
        :param bool is_active: whether resource is active (observable)
        :param int rate: sample rate of the resource
        """
        dict.__init__(self)
        dict.__setitem__(self, NAME_FIELD, name)
        dict.__setitem__(self, ACTIVE_FIELD, is_active)
        dict.__setitem__(self, SAMPLE_R_FIELD, rate)
        dict.__setitem__(self, DATA_FIELD, '')
        dict.__setitem__(self, TIME_FIELD, '')

    def __missing__(self, key):
        """
        Overwrite default callback function handling missing key by dict.__getitem()__

        :param key: key to search in the dictionary
        :type key: str (but can be other types by definition of dict in Python)
        :raise KeyError: key not found
        """
        raise KeyError("The key {} not defined".format(key))

    def set_name(self, name):
        """
        Set name field of the table

        :param str name: resource name
        """
        dict.__setitem__(self, NAME_FIELD, name)

    def set_active(self, is_active):
        """
        Set activeness field of the table

        :param bool active: whether resource is observable
        """
        dict.__setitem__(self, ACTIVE_FIELD, is_active)

    def set_sample_rate(self, rate):
        """
        Set sample rate field of the table

        :param int rate: frequency to observe the resource
        """
        dict.__setitem__(self, SAMPLE_R_FIELD, rate)

    def set_data(self, data):
        """
        Set data field of the table

        :param json data: resource data
        """
        dict.__setitem__(self, DATA_FIELD, data)

    def set_time(self, time):
        """
        Set time field of the table

        :param str time: timestamp in string format
        """
        dict.__setitem__(self, TIME_FIELD, time)


