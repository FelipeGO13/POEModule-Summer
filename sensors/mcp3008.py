"""
    Created on November 21, 2014
    Last modified on April 17, 2015 by Yaodong Yu

    @author: Ruibing Zhao
    @author: Yaodong Yu

    This script is the driver file, providing interface with 8-channel ADC converter MCP3008

    Reference: MCP3008 datasheet: https://www.adafruit.com/datasheets/MCP3008.pdf
"""

import platform

if platform.machine() != 'x86_64':
    import spidev

    class SPIDevice(object):
        """
        Base class for a generic SPI device
        """
        spi = spidev.SpiDev()

    class MCP3008(SPIDevice):
        """
        MCP3008 driver class derived from SPIDevice class
        """

        # Channel names and chip select
        MCP3008_CH0 = 0
        MCP3008_CH1 = 1
        MCP3008_CH2 = 2
        MCP3008_CH3 = 3
        MCP3008_CH4 = 4
        MCP3008_CH5 = 5
        MCP3008_CH6 = 6
        MCP3008_CH7 = 7

        MCP3008_CS0 = 0
        MCP3008_CS1 = 1

        # Commands and operation modes
        MCP3008_START = 0x01
        #MCP3008_DIFF = 0x0
        MCP3008_SINGLE = 0x8

        # Accelerometer definitions
        ACC_X_CH = MCP3008_CH0
        ACC_Y_CH = MCP3008_CH1
        ACC_Z_CH = MCP3008_CH2
        AXIS_X = 0
        AXIS_Y = 1
        AXIS_Z = 2
        # Joystick definitions
        JOYSTICK_LR_CH = MCP3008_CH3
        JOYSTICK_UD_CH = MCP3008_CH4

        # Digital data received is in range 0~1023:
        # Reference point zero acceleration on x, y, z axis,
        #   number below reference point represents negative acceleration
        ZERO_G_REF = [512, 502, 522]
        # delta per g (m/s^2)
        DELTA_PER_G = [102, 104, 102]

        def _read_channel_raw(self, channel):
            """
            Interface function directly read channel value from SPI bus

            :param int channel: channel to read from (0~7)
            :return: (int) raw data reading from channel (0~1023)
            """
            self.spi.open(0, self.MCP3008_CS0)

            # 3-byte command to read a 10 bit data from MCP3008:
            # 1st byte contains only Start Bit, then operation mode and channel select
            adc = self.spi.xfer2([self.MCP3008_START, (self.MCP3008_SINGLE + channel) << 4, 0])

            # last 10 bits out of 3 bytes are received data
            data = ((adc[1] & 0x03) << 8) + adc[2]

            self.spi.close()
            return data

        def _convert_raw_to_g(self, raw_acc, axis):
            """
            Algorithm to convert ADC raw reading to acceleration in units of g (9.8m/s^2)

            :param int raw_acc: raw ADC channel reading (0~1023)
            :param int axis: axis this data corresponds to (x, y or z)
            :return: (float) acceleration of indicated axis in units of g
            """
            return (float(raw_acc - self.ZERO_G_REF[axis])) / self.DELTA_PER_G[axis]

        def read_channel_raw(self, channel):
            """
            Wrapper function of reading raw channel data

            :param int channel: channel to read from (0~7)
            :return: (int) raw data reading from channel (0~1023)
            """
            return self._read_channel_raw(channel)

        # FIXME: This hierarchy may have some issues. Accelerometer device should be an individual class /
        #       based on MCP3008 channels
        def acceleration(self):
            """
            Acquire 3-axis acceleration readings from the accelerometer connected to the ADC

            :return: (float, float, float) 3 acceleration readings in units of g
            """
            # Raw data is converted to g (m/s^2) before output
            x = self._convert_raw_to_g(self._read_channel_raw(self.ACC_X_CH), self.AXIS_X)
            y = self._convert_raw_to_g(self._read_channel_raw(self.ACC_Y_CH), self.AXIS_Y)
            z = self._convert_raw_to_g(self._read_channel_raw(self.ACC_Z_CH), self.AXIS_Z)
            return x, y, z

        def joystick(self):
            """
            Acquire 2-axis joystick relative position

            :return: (int, int) relative positions of two axis of the joystick
            """
            leftright = self._read_channel_raw(self.JOYSTICK_LR_CH)
            updown = self._read_channel_raw(self.JOYSTICK_UD_CH)
            return leftright, updown


class MCP3008Mock():
    """
    Mock class of MCP3008 ADC converter in case of running server on non Raspberry Pi platform for testing
    """

    import random
    random.seed()

    # default parameters
    adc = [0xff, 0xff, 0xff]
    x = 1.0
    y = 0.0
    z = 0.0
    leftright = 516
    updown = 510

    def read_channel_raw(self, channel):
        """
        Simulate read_channel_raw method of MCP3008 class with randomly generated values

        :param int channel: channel to read from (0~7)
        :return: simulated channel reading (0~1023)
        """
        self.adc[1] = self.random.randint(0, 0xff)
        self.adc[2] = self.random.randint(0, 0xff)
        return ((self.adc[1] & 0x03) << 8) + self.adc[2]

    def acceleration(self):
        """
        Simulate acceleration method of MCP3008 class with randomly generated values

        :return: (float, float, float) simulated 3 acceleration readings in units of g
        """
        # Theoretical limits provided by datasheet
        # https://www.sparkfun.com/datasheets/Components/SMD/adxl335.pdf
        self.x = self.random.uniform(-3.0, 3.0)
        self.y = self.random.uniform(-3.0, 3.0)
        self.z = self.random.uniform(-3.0, 3.0)
        return self.x, self.y, self.z

    def joystick(self):
        """
        Simulate joystick method of MCP3008 class with randomly generated values

        :return: (int, int) simulated relative positions of two axis of the joystick
        """
        # Experimental limits at 3.3V
        self.leftright = self.random.randint(260, 763)
        self.updown = self.random.randint(253, 769)
        return self.leftright, self.updown
