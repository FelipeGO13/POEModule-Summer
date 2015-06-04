"""
    Created on April 2, 2015
    Renamed from pir.py on April 17, 2015
    Last modified on April 17, 2015 by Yaodong Yu

    @author: Yaodong Yu

    This script is the driver file, providing interface with SE-10 motion sensor

    Reference: SE-10 datasheit et: https://www.sparkfun.com/datasheets/Sensors/Proximity/SE-10.pdf
"""

import traceback
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import platform
if platform.machine() != 'x86_64':
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        logger.warning("Could not import the RPi.GPIO package (http://pypi.python.org/pypi/RPi.GPIO). "
                       "Using a mock instead. Notice that this is useful only for the purpose of "
                       "debugging this module, but will not give the end user any useful result.")
        import RPiMock.GPIO as GPIO
    except:
        logger.warning("Could not import the RPi.GPIO package (http://pypi.python.org/pypi/RPi.GPIO). "
                       "Using a mock instead. Notice that this is useful only for the purpose of "
                       "debugging this module, but will not give the end user any useful result.")
        import RPiMock.GPIO as GPIO
        traceback.print_exc(file=sys.stdout)

    SE10_PIN = 13  # Pin 13 = GPIO 27

    class Se10(object):
        """
        SE-10 motion sensor driver class
        """

        def __init__(self, gpio=SE10_PIN , gpioMode=GPIO.BOARD):
            """
            Constructor to create an instance of the SE-10 motion sensor interface

            :param int gpio: GPIO used to connect SE-10 to Raspberry Pi
            :param int gpioMode: GPIO mode used to configure RPi GPIO module
            """
            self.gpio = gpio
            GPIO.setmode(gpioMode)

        def has_motion(self):
            """
            Get motion status

            :return: (bool) presence of motion
            """
            GPIO.setup(self.gpio, GPIO.IN)
            if GPIO.input(self.gpio) == GPIO.LOW:
                return False
            else:
                return True


class Se10Mock():
    """
    Mock class of SE-10 motion sensor in case of running server on non Raspberry Pi platform for testing
    """

    import random
    random.seed()

    motion = True

    def has_motion(self):
        """
        Simulated has_motion method of Se10 class with randomly generated values

        :return: (bool) simulated presence of motion
        """
        self.motion = bool(self.random.randint(0, 1))
        return self.motion