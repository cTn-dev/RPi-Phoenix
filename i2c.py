#!/usr/bin/python

# Python Standard Library Imports
import smbus

# External Imports
pass

# Custom Imports
pass

# ===========================================================================
# cTn I2C Base Class (an rewriten Adafruit_I2C pythone class clone)
# ===========================================================================

class ctn_i2c :

    def __init__(self, address, bus = smbus.SMBus(0), debug = False):
        self.address = address
        self.bus = bus
        self.debug = debug

    def reverseByteOrder(self, data):
        # Reverses the byte order of an int (16-bit) or long (32-bit) value
        # Courtesy Vishal Sapre
        dstr = hex(data)[2:].replace('L','')
        byteCount = len(dstr[::2])
        val = 0
        for i, n in enumerate(range(byteCount)):
            d = data & 0xFF
            val |= (d << (8 * (byteCount - i - 1)))
            data >>= 8
        return val
    
    def readBit(self, reg, bitNum):
        b = self.readU8(reg)
        data = b & (1 << bitNum)
        return data
    
    def writeBit(self, reg, bitNum, data):
        b = self.readU8(reg)
        
        if data != 0:
            b = (b | (1 << bitNum))
        else:
            b = (b & ~(1 << bitNum))
            
        return self.write8(reg, b)
    
    def writeBits(self, reg, bitStart, length, data):
        #      010 value to write
        # 76543210 bit numbers
        #    xxx   args: bitStart=4, length=3
        # 00011100 mask byte
        # 10101111 original value (sample)
        # 10100011 original & ~mask
        # 10101011 masked | value
        b = self.readU8(reg)
        mask = ((1 << length) - 1) << (bitStart - length + 1)
        data <<= (bitStart - length + 1)
        data &= mask
        b &= ~(mask)
        b |= data
            
        return self.write8(reg, b)
    
    def readBytes(self, reg, length, data):
        # in development
        pass
    
    def write8(self, reg, value):
        # Writes an 8-bit value to the specified register/address
        try:
            self.bus.write_byte_data(self.address, reg, value)
            if self.debug:
                print("I2C: Wrote 0x%02X to register 0x%02X" % (value, reg))
        except (IOError):
            print ("Error accessing 0x%02X: Check your I2C address" % self.address)
            return -1

    def writeList(self, reg, list):
        # Writes an array of bytes using I2C format"
        try:
            self.bus.write_i2c_block_data(self.address, reg, list)
        except (IOError):
            print ("Error accessing 0x%02X: Check your I2C address" % self.address)
        return -1

    def readU8(self, reg):
        # Read an unsigned byte from the I2C device
        try:
            result = self.bus.read_byte_data(self.address, reg)
            if self.debug:
                print ("I2C: Device 0x%02X returned 0x%02X from reg 0x%02X" % (self.address, result & 0xFF, reg))
            return result
        except (IOError):
            print ("Error accessing 0x%02X: Check your I2C address" % self.address)
            return -1

    def readS8(self, reg):
        # Reads a signed byte from the I2C device
        try:
            result = self.bus.read_byte_data(self.address, reg)
            if self.debug:
                print ("I2C: Device 0x%02X returned 0x%02X from reg 0x%02X" % (self.address, result & 0xFF, reg))
            if result > 127:
                return result - 256
            else:
                return result
        except (IOError):
            print ("Error accessing 0x%02X: Check your I2C address" % self.address)
            return -1

    def readU16(self, reg):
        # Reads an unsigned 16-bit value from the I2C device
        try:
            hibyte = self.bus.read_byte_data(self.address, reg)
            result = (hibyte << 8) + self.bus.read_byte_data(self.address, reg+1)
            if self.debug:
                print ("I2C: Device 0x%02X returned 0x%04X from reg 0x%02X" % (self.address, result & 0xFFFF, reg))
            return result
        except (IOError):
            print ("Error accessing 0x%02X: Check your I2C address" % self.address)
            return -1

    def readS16(self, reg):
        # Reads a signed 16-bit value from the I2C device
        try:
            hibyte = self.bus.read_byte_data(self.address, reg)
            if hibyte > 127:
                hibyte -= 256
            result = (hibyte << 8) + self.bus.read_byte_data(self.address, reg+1)
            if self.debug:
                print ("I2C: Device 0x%02X returned 0x%04X from reg 0x%02X" % (self.address, result & 0xFFFF, reg))
            return result
        except (IOError):
            print ("Error accessing 0x%02X: Check your I2C address" % self.address)
            return -1