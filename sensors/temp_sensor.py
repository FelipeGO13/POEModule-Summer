"""
    Created on Oct 5, 2012

    @author: Luca Nobili

    This modules reads Humidity and Temperature from a Sensirion SHT1x sensor. I has been tested
    both with an SHT11 and an SHT15.

    It is meant to be used in a Raspberry Pi and depends on this module (http://code.google.com/p/raspberry-gpio-python/).

    The module raspberry-gpio-python requires root privileges, therefore, to run this module you need to run your script as root.

    Example Usage:

    ``>>> from sht1x.Sht1x import Sht1x as SHT1x``
    ``>>> sht1x = SHT1x(11,7)``
    ``>>> sht1x.read_temperature_C()``
    ``25.22``
    ``>>> sht1x.read_humidity()``
    ``52.6564216``

    This file has been adapted and modified by UBC ECE 2014 Capstone Project #94

    Adapted on November 23, 2014 by Yaodong Yu
    Last modified on April 17, 2015 by Yaodong Yu
"""

import traceback
import sys
import time
import logging
import math

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

    # Conversion coefficients from SHT15 datasheet
    D1 = -40.0          # for 14 Bit @ 5V
    D2 = 0.01           # for 14 Bit DEGC

    C1 = -2.0468        # for 12 Bit
    C2 = 0.0367         # for 12 Bit
    C3 = -0.0000015955  # for 12 Bit
    T1 = 0.01           # for 14 Bit @ 5V
    T2 = 0.00008        # for 14 Bit @ 5V

    SHT15_PIN_SDA = 11  # Pin 11 = GPIO 17
    SHT15_PIN_SCLK = 7  # PIn 7 = GPIO 4

    class Sht1x(object):
        """
        SHT1X driver class to directly interact with SHT1X sensor with GPIOs
        """

        # I deliberately will not implement read_temperature_F because I believe in the
        #   in the Metric System (http://en.wikipedia.org/wiki/Metric_system)

        GPIO_BOARD = GPIO.BOARD
        GPIO_BCM = GPIO.BCM

        def __init__(self, dataPin, sckPin, gpioMode = GPIO_BOARD):
            """
            Constructor to initialize a driver instance

            :param int dataPin: Raspberry Pi GPIO pin used for data interface
            :param int sckPin: Raspberry Pi GPIO pin used for clock signal
            :param int gpioMode: GPIO mode to configure the RPi GPIO module
            """
            self.dataPin = dataPin
            self.sckPin = sckPin
            GPIO.setmode(gpioMode)

        # The following methods: __sendCommand, __clockTick, __waitForResult, __getData16Bit, __shiftIn,
        #                       __skipCrc, and __connectionReset
        # are low-level hardware interface methods to send commands and read from SHT1X sensor
        # See datasheet for details: https://www.adafruit.com/datasheets/Sensirion_Humidity_SHT1x_Datasheet_V5.pdf
        def __sendCommand(self, command):
            # Transmission start
            GPIO.setup(self.dataPin, GPIO.OUT)
            GPIO.setup(self.sckPin, GPIO.OUT)

            GPIO.output(self.dataPin, GPIO.HIGH)
            self.__clockTick(GPIO.HIGH)
            GPIO.output(self.dataPin, GPIO.LOW)
            self.__clockTick(GPIO.LOW)
            self.__clockTick(GPIO.HIGH)
            GPIO.output(self.dataPin, GPIO.HIGH)
            self.__clockTick(GPIO.LOW)

            for i in range(8):
                GPIO.output(self.dataPin, command & (1 << 7 - i))
                self.__clockTick(GPIO.HIGH)
                self.__clockTick(GPIO.LOW)

            self.__clockTick(GPIO.HIGH)

            GPIO.setup(self.dataPin, GPIO.IN)

            ack = GPIO.input(self.dataPin)
            logger.debug("ack1: %s", ack)
            if ack != GPIO.LOW:
                logger.error("nack1")

            self.__clockTick(GPIO.LOW)

            ack = GPIO.input(self.dataPin)
            logger.debug("ack2: %s", ack)
            if ack != GPIO.HIGH:
                logger.error("nack2")

        def __clockTick(self, value):
            GPIO.output(self.sckPin, value)
            # 100 nanoseconds
            time.sleep(.0000001)

        def __waitForResult(self):
            GPIO.setup(self.dataPin, GPIO.IN)

            for i in range(100):
                # 10 milliseconds
                time.sleep(.01)
                ack = GPIO.input(self.dataPin)
                if ack == GPIO.LOW:
                    break
            if ack == GPIO.HIGH:
                raise SystemError

        def __getData16Bit(self):
            GPIO.setup(self.dataPin, GPIO.IN)
            GPIO.setup(self.sckPin, GPIO.OUT)
            # Get the most significant bits
            value = self.__shiftIn(8)
            value *= 256
            # Send the required ack
            GPIO.setup(self.dataPin, GPIO.OUT)
            GPIO.output(self.dataPin, GPIO.HIGH)
            GPIO.output(self.dataPin, GPIO.LOW)
            self.__clockTick(GPIO.HIGH)
            self.__clockTick(GPIO.LOW)
            # Get the least significant bits
            GPIO.setup(self.dataPin, GPIO.IN)
            value |= self.__shiftIn(8)

            return value

        def __shiftIn(self, bitNum):
            value = 0
            for i in range(bitNum):
                self.__clockTick(GPIO.HIGH)
                value = value * 2 + GPIO.input(self.dataPin)
                self.__clockTick(GPIO.LOW)
            return value

        def __skipCrc(self):
            # Skip acknowledge to end trans (no CRC)
            GPIO.setup(self.dataPin, GPIO.OUT)
            GPIO.setup(self.sckPin, GPIO.OUT)
            GPIO.output(self.dataPin, GPIO.HIGH)
            self.__clockTick(GPIO.HIGH)
            self.__clockTick(GPIO.LOW)

        def __connectionReset(self):
            GPIO.setup(self.dataPin, GPIO.OUT)
            GPIO.setup(self.sckPin, GPIO.OUT)
            GPIO.output(self.dataPin, GPIO.HIGH)
            for i in range(10):
                self.__clockTick(GPIO.HIGH)
                self.__clockTick(GPIO.LOW)

        def _read_humidity(self, temperature):
            """
            Read SHT1X sensor with raw humidity reading and convert into percentage with temperature correction

            :param float temperature: temperature in Celsius degree
            :return: (float) humidity in percentage
            """
            humidityCommand = 0b00000101
            self.__sendCommand(humidityCommand)
            self.__waitForResult()
            rawHumidity = self.__getData16Bit()
            self.__skipCrc()
            GPIO.cleanup()

            # Apply linear conversion to raw value
            linearHumidity = C1 + C2 * rawHumidity + C3 * rawHumidity * rawHumidity
            # Correct humidity value for current temperature
            return (temperature - 25.0 ) * (T1 + T2 * rawHumidity) + linearHumidity

        def read_temperature_C(self):
            """
            Read SHT1X sensor for temperature and convert into Celsius degree

            :return: (float) temperature reading in Celsius degree
            """
            temperatureCommand = 0b00000011

            self.__sendCommand(temperatureCommand)
            self.__waitForResult()
            rawTemperature = self.__getData16Bit()
            self.__skipCrc()
            GPIO.cleanup()

            return rawTemperature * D2 + D1

        def read_humidity(self):
            """
            Wrapper method to read humidity from SHT1X sensor

            :return: (float) humidity in percentage
            """
            # Get current temperature for humidity correction
            temperature = self.read_temperature_C()
            return self._read_humidity(temperature)

        def calculate_dew_point(self, temperature, humidity):
            """
            Dew point calculation with temperature and humidity reading
            # Don't know what this method should be used for, haven't really used it
            """
            if temperature > 0:
                tn = 243.12
                m = 17.62
            else:
                tn = 272.62
                m = 22.46
            return tn * (math.log(humidity / 100.0) + (m * temperature) / (tn + temperature)) / \
                        (m - math.log(humidity / 100.0) - m * temperature / (tn + temperature))

    class WaitingSht1x(Sht1x):
        """
        Wrapper class to SHT1X driver, this class also ensures the sensor is not
            read too frequently (by hardware limitations).
        """

        __lastInvocationTime = 0

        def __init__(self, dataPin, sckPin):
            """
            Constructor to initialize a driver instance

            :param int dataPin: Raspberry Pi GPIO pin used for data interface
            :param int sckPin: Raspberry Pi GPIO pin used for clock signal
            """
            super(WaitingSht1x, self).__init__(dataPin, sckPin)

        def __wait(self):
            """
            Timer method to ensure a minimum of 1 second gap between two consecutive reading
            """
            lastInvocationDelta = time.time() - self.__lastInvocationTime

            # if we queried the sensor less then a second ago, wait until a second is passed
            if lastInvocationDelta < 1:
                time.sleep(1 - lastInvocationDelta)
            self.__lastInvocationTime = time.time()

        def read_temperature_C(self):
            """
            Read SHT1X sensor for temperature in Celsius degree

            :return: (float) temperature reading in Celsius degree
            """
            self.__wait()
            return super(WaitingSht1x, self).read_temperature_C()

        def read_humidity(self):
            """
            Read SHT1X sensor for humidity in percentage

            :return: (float) humidity in percentage
            """
            temperature = self.read_temperature_C()
            self.__wait()
            return super(WaitingSht1x, self)._read_humidity(temperature)

        def read_temperature_and_Humidity(self):
            """
            Read SHT1X sensor for both temperature in Celsius and humidity in percentage

            :return: (float, float ) temperature in Celsius, and humidity in percentage
            """
            temperature = self.read_temperature_C()
            self.__wait()
            humidity = super(WaitingSht1x, self)._read_humidity(temperature)
            return temperature, humidity

    class WaitingSht15(WaitingSht1x):
        """
        A class specifically for SHT15 type of HygroThermo sensor, which is a derivation from SHT1X
        """

        def __init__(self, dataPin=SHT15_PIN_SDA, sckPin=SHT15_PIN_SCLK):
            """
            Constructor to initialize a SHT15 driver instance

            :param int dataPin: Raspberry Pi GPIO pin used for data interface
            :param int sckPin: Raspberry Pi GPIO pin used for clock signal
            """
            super(WaitingSht15, self).__init__(dataPin, sckPin)
            self.__lastInvocationTime = 0


class WaitingSht15Mock():
    """
    Mock class of SHT15 sensor driver in case of running server on non Raspberry Pi platform for testing
    """

    import random
    random.seed()

    temperature = 25
    humidity = 99

    def read_temperature_and_Humidity(self):
        """
        Simulate read_temperature_and_Humidity method of WaitingSht15 class with randomly generated values

        :return: (float, float) simulated temperature in Celsius, and humidity in percentage
        """
        # Theoretical limit from datasheet
        # https://www.adafruit.com/datasheets/Sensirion_Humidity_SHT1x_Datasheet_V5.pdf
        self.temperature = self.random.uniform(-40.0, 123.8)
        self.humidity = self.random.uniform(0.0, 100.0)
        return self.temperature, self.humidity

    def read_humidity(self):
        """
        Simulate read_humidity method of WaitingSht15 class with randomly generated values

        :return: (float) simulated humidity in percentage
        """
        self.humidity = self.random.uniform(0.0, 100.0)
        return self.humidity

    def read_temperature_C(self):
        """
        Simulate read_temperature_C method of WaitingSht15 class with randomly generated values

        :return: (float) simulated temperature in Celsius
        """
        self.temperature = self.random.uniform(-40.0, 123.8)
        return self.temperature
