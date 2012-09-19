#!/usr/bin/python

# Python Standard Library Imports
pass

# External Imports
pass

# Custom Imports
import config
from i2c import ctn_i2c

class MPU6050():
    # Register map based on Jeff Rowberg <jeff@rowberg.net> source code at
    # https://github.com/jrowberg/i2cdevlib/blob/master/Arduino/MPU6050/MPU6050.h
    
    MPU6050_ADDRESS_AD0_LOW       = 0x68 # address pin low (GND), default for InvenSense evaluation board
    MPU6050_ADDRESS_AD0_HIGH      = 0x69 # address pin high (VCC)
    MPU6050_DEFAULT_ADDRESS       = MPU6050_ADDRESS_AD0_LOW

    MPU6050_RA_XG_OFFS_TC         = 0x00 # [7] PWR_MODE, [6:1] XG_OFFS_TC, [0] OTP_BNK_VLD
    MPU6050_RA_YG_OFFS_TC         = 0x01 # [7] PWR_MODE, [6:1] YG_OFFS_TC, [0] OTP_BNK_VLD
    MPU6050_RA_ZG_OFFS_TC         = 0x02 # [7] PWR_MODE, [6:1] ZG_OFFS_TC, [0] OTP_BNK_VLD
    MPU6050_RA_X_FINE_GAIN        = 0x03 # [7:0] X_FINE_GAIN
    MPU6050_RA_Y_FINE_GAIN        = 0x04 # [7:0] Y_FINE_GAIN
    MPU6050_RA_Z_FINE_GAIN        = 0x05 # [7:0] Z_FINE_GAIN
    MPU6050_RA_XA_OFFS_H          = 0x06 # [15:0] XA_OFFS
    MPU6050_RA_XA_OFFS_L_TC       = 0x07
    MPU6050_RA_YA_OFFS_H          = 0x08 # [15:0] YA_OFFS
    MPU6050_RA_YA_OFFS_L_TC       = 0x09
    MPU6050_RA_ZA_OFFS_H          = 0x0A # [15:0] ZA_OFFS
    MPU6050_RA_ZA_OFFS_L_TC       = 0x0B
    MPU6050_RA_XG_OFFS_USRH       = 0x13 # [15:0] XG_OFFS_USR
    MPU6050_RA_XG_OFFS_USRL       = 0x14
    MPU6050_RA_YG_OFFS_USRH       = 0x15 # [15:0] YG_OFFS_USR
    MPU6050_RA_YG_OFFS_USRL       = 0x16
    MPU6050_RA_ZG_OFFS_USRH       = 0x17 # [15:0] ZG_OFFS_USR
    MPU6050_RA_ZG_OFFS_USRL       = 0x18
    MPU6050_RA_SMPLRT_DIV         = 0x19
    MPU6050_RA_CONFIG             = 0x1A
    MPU6050_RA_GYRO_CONFIG        = 0x1B
    MPU6050_RA_ACCEL_CONFIG       = 0x1C
    MPU6050_RA_FF_THR             = 0x1D
    MPU6050_RA_FF_DUR             = 0x1E
    MPU6050_RA_MOT_THR            = 0x1F
    MPU6050_RA_MOT_DUR            = 0x20
    MPU6050_RA_ZRMOT_THR          = 0x21
    MPU6050_RA_ZRMOT_DUR          = 0x22
    MPU6050_RA_FIFO_EN            = 0x23
    MPU6050_RA_I2C_MST_CTRL       = 0x24
    MPU6050_RA_I2C_SLV0_ADDR      = 0x25
    MPU6050_RA_I2C_SLV0_REG       = 0x26
    MPU6050_RA_I2C_SLV0_CTRL      = 0x27
    MPU6050_RA_I2C_SLV1_ADDR      = 0x28
    MPU6050_RA_I2C_SLV1_REG       = 0x29
    MPU6050_RA_I2C_SLV1_CTRL      = 0x2A
    MPU6050_RA_I2C_SLV2_ADDR      = 0x2B
    MPU6050_RA_I2C_SLV2_REG       = 0x2C
    MPU6050_RA_I2C_SLV2_CTRL      = 0x2D
    MPU6050_RA_I2C_SLV3_ADDR      = 0x2E
    MPU6050_RA_I2C_SLV3_REG       = 0x2F
    MPU6050_RA_I2C_SLV3_CTRL      = 0x30
    MPU6050_RA_I2C_SLV4_ADDR      = 0x31
    MPU6050_RA_I2C_SLV4_REG       = 0x32
    MPU6050_RA_I2C_SLV4_DO        = 0x33
    MPU6050_RA_I2C_SLV4_CTRL      = 0x34
    MPU6050_RA_I2C_SLV4_DI        = 0x35
    MPU6050_RA_I2C_MST_STATUS     = 0x36
    MPU6050_RA_INT_PIN_CFG        = 0x37
    MPU6050_RA_INT_ENABLE         = 0x38
    MPU6050_RA_DMP_INT_STATUS     = 0x39
    MPU6050_RA_INT_STATUS         = 0x3A
    MPU6050_RA_ACCEL_XOUT_H       = 0x3B
    MPU6050_RA_ACCEL_XOUT_L       = 0x3C
    MPU6050_RA_ACCEL_YOUT_H       = 0x3D
    MPU6050_RA_ACCEL_YOUT_L       = 0x3E
    MPU6050_RA_ACCEL_ZOUT_H       = 0x3F
    MPU6050_RA_ACCEL_ZOUT_L       = 0x40
    MPU6050_RA_TEMP_OUT_H         = 0x41
    MPU6050_RA_TEMP_OUT_L         = 0x42
    MPU6050_RA_GYRO_XOUT_H        = 0x43
    MPU6050_RA_GYRO_XOUT_L        = 0x44
    MPU6050_RA_GYRO_YOUT_H        = 0x45
    MPU6050_RA_GYRO_YOUT_L        = 0x46
    MPU6050_RA_GYRO_ZOUT_H        = 0x47
    MPU6050_RA_GYRO_ZOUT_L        = 0x48
    MPU6050_RA_EXT_SENS_DATA_00   = 0x49
    MPU6050_RA_EXT_SENS_DATA_01   = 0x4A
    MPU6050_RA_EXT_SENS_DATA_02   = 0x4B
    MPU6050_RA_EXT_SENS_DATA_03   = 0x4C
    MPU6050_RA_EXT_SENS_DATA_04   = 0x4D
    MPU6050_RA_EXT_SENS_DATA_05   = 0x4E
    MPU6050_RA_EXT_SENS_DATA_06   = 0x4F
    MPU6050_RA_EXT_SENS_DATA_07   = 0x50
    MPU6050_RA_EXT_SENS_DATA_08   = 0x51
    MPU6050_RA_EXT_SENS_DATA_09   = 0x52
    MPU6050_RA_EXT_SENS_DATA_10   = 0x53
    MPU6050_RA_EXT_SENS_DATA_11   = 0x54
    MPU6050_RA_EXT_SENS_DATA_12   = 0x55
    MPU6050_RA_EXT_SENS_DATA_13   = 0x56
    MPU6050_RA_EXT_SENS_DATA_14   = 0x57
    MPU6050_RA_EXT_SENS_DATA_15   = 0x58
    MPU6050_RA_EXT_SENS_DATA_16   = 0x59
    MPU6050_RA_EXT_SENS_DATA_17   = 0x5A
    MPU6050_RA_EXT_SENS_DATA_18   = 0x5B
    MPU6050_RA_EXT_SENS_DATA_19   = 0x5C
    MPU6050_RA_EXT_SENS_DATA_20   = 0x5D
    MPU6050_RA_EXT_SENS_DATA_21   = 0x5E
    MPU6050_RA_EXT_SENS_DATA_22   = 0x5F
    MPU6050_RA_EXT_SENS_DATA_23   = 0x60
    MPU6050_RA_MOT_DETECT_STATUS  = 0x61
    MPU6050_RA_I2C_SLV0_DO        = 0x63
    MPU6050_RA_I2C_SLV1_DO        = 0x64
    MPU6050_RA_I2C_SLV2_DO        = 0x65
    MPU6050_RA_I2C_SLV3_DO        = 0x66
    MPU6050_RA_I2C_MST_DELAY_CTRL = 0x67
    MPU6050_RA_SIGNAL_PATH_RESET  = 0x68
    MPU6050_RA_MOT_DETECT_CTRL    = 0x69
    MPU6050_RA_USER_CTRL          = 0x6A
    MPU6050_RA_PWR_MGMT_1         = 0x6B
    MPU6050_RA_PWR_MGMT_2         = 0x6C
    MPU6050_RA_BANK_SEL           = 0x6D
    MPU6050_RA_MEM_START_ADDR     = 0x6E
    MPU6050_RA_MEM_R_W            = 0x6F
    MPU6050_RA_DMP_CFG_1          = 0x70
    MPU6050_RA_DMP_CFG_2          = 0x71
    MPU6050_RA_FIFO_COUNTH        = 0x72
    MPU6050_RA_FIFO_COUNTL        = 0x73
    MPU6050_RA_FIFO_R_W           = 0x74
    MPU6050_RA_WHO_AM_I           = 0x75  
   
    
    # construct a new object with the I2C address of the MPU6050
    def __init__(self, address = MPU6050_DEFAULT_ADDRESS, debug = False):
        self.i2c = ctn_i2c(address)
        self.address = address
        self.debug = debug
        if self.debug:
            print ("Waking up the MPU6050")        
        # Clear sleeping bit
        self.i2c.write8(self.MPU6050_RA_PWR_MGMT_1, 0x00)
        
        # Offset Settings
        self.setAccelOffsetX(config.accelerometer_offset['x'])
        self.setAccelOffsetY(config.accelerometer_offset['y'])
        self.setAccelOffsetZ(config.accelerometer_offset['z'])
        
        self.setGyroOffsetX(config.gyroscope_offset['x'])
        self.setGyroOffsetY(config.gyroscope_offset['y'])
        self.setGyroOffsetZ(config.gyroscope_offset['z'])   
        
        # Low-Pass Filter Configuration
        #
        #          |   ACCELEROMETER    |           GYROSCOPE
        # DLPF_CFG | Bandwidth | Delay  | Bandwidth | Delay  | Sample Rate
        # ---------+-----------+--------+-----------+--------+-------------
        # 0        | 260Hz     | 0ms    | 256Hz     | 0.98ms | 8kHz
        # 1        | 184Hz     | 2.0ms  | 188Hz     | 1.9ms  | 1kHz
        # 2        | 94Hz      | 3.0ms  | 98Hz      | 2.8ms  | 1kHz
        # 3        | 44Hz      | 4.9ms  | 42Hz      | 4.8ms  | 1kHz
        # 4        | 21Hz      | 8.5ms  | 20Hz      | 8.3ms  | 1kHz
        # 5        | 10Hz      | 13.8ms | 10Hz      | 13.4ms | 1kHz
        # 6        | 5Hz       | 19.0ms | 5Hz       | 18.6ms | 1kHz
        # 7        |   -- Reserved --   |   -- Reserved --   | Reserved        
        
        # Binary value used for Maggie is 5
        self.i2c.write8(self.MPU6050_RA_CONFIG, 0b000101)        

    
    """
    # this function is here only as "legacy support" and requires bitstring module to work    
    def int_to_16bit_tc(self, value):
        if value >= 0:
            bo = BitArray(uint = value, length = 16)
        else:
            bo = BitArray(uint = abs(value + 1), length = 16)
            bo.invert()
        
        str = bo.bin
        high = int(str[:8], 2)
        low =  int(str[8:16], 2)
        
        return high, low        
    """ 
     
    def readAccelOffsetX(self):
        result = self.i2c.readS16(self.MPU6050_RA_XA_OFFS_H)
        return result
    
    def setAccelOffsetX(self, value):
        self.i2c.write8(self.MPU6050_RA_XA_OFFS_H, value >> 8)
        self.i2c.write8(self.MPU6050_RA_XA_OFFS_L_TC, value & 0xFF) 
        return True   

    def readAccelOffsetY(self):
        result = self.i2c.readS16(self.MPU6050_RA_YA_OFFS_H)
        return result

    def setAccelOffsetY(self, value):
        self.i2c.write8(self.MPU6050_RA_YA_OFFS_H, value >> 8)
        self.i2c.write8(self.MPU6050_RA_YA_OFFS_L_TC, value & 0xFF) 
        return True        
        
    def readAccelOffsetZ(self):
        result = self.i2c.readS16(self.MPU6050_RA_ZA_OFFS_H)
        return result

    def setAccelOffsetZ(self, value):
        self.i2c.write8(self.MPU6050_RA_ZA_OFFS_H, value >> 8)
        self.i2c.write8(self.MPU6050_RA_ZA_OFFS_L_TC, value & 0xFF) 
        return True    
    
    def readGyroOffsetX(self):
        result = self.i2c.readS16(self.MPU6050_RA_XG_OFFS_USRH)
        return result        
        
    def setGyroOffsetX(self, value):
        self.i2c.write8(self.MPU6050_RA_XG_OFFS_USRH, value >> 8)
        self.i2c.write8(self.MPU6050_RA_XG_OFFS_USRL, value & 0xFF) 
        return True
        
    def readGyroOffsetY(self):
        result = self.i2c.readS16(self.MPU6050_RA_YG_OFFS_USRH)
        return result        
        
    def setGyroOffsetY(self, value):
        self.i2c.write8(self.MPU6050_RA_YG_OFFS_USRH, value >> 8)
        self.i2c.write8(self.MPU6050_RA_YG_OFFS_USRL, value & 0xFF) 
        return True
        
    def readGyroOffsetZ(self):
        result = self.i2c.readS16(self.MPU6050_RA_ZG_OFFS_USRH)
        return result        
        
    def setGyroOffsetZ(self, value):
        self.i2c.write8(self.MPU6050_RA_ZG_OFFS_USRH, value >> 8)
        self.i2c.write8(self.MPU6050_RA_ZG_OFFS_USRL, value & 0xFF) 
        return True
 
    def readTemperature(self):
        # The temperature sensor is -40 to +85 degrees Celsius.
        # It is a signed integer.
        # According to the datasheet: 
        #   340 per degrees Celsius, -512 at 35 degrees.
        #   At 0 degrees: -512 - (340 * 35) = -12412    
        result = self.i2c.readS16(self.MPU6050_RA_TEMP_OUT_H)
        result = (result + 12412) / 340
        
        return result
        
    def readGyro(self):
        x = self.i2c.readS16(self.MPU6050_RA_GYRO_XOUT_H)
        y = self.i2c.readS16(self.MPU6050_RA_GYRO_YOUT_H)
        z = self.i2c.readS16(self.MPU6050_RA_GYRO_ZOUT_H)
        
        return x, y, z
        
    def readAccel(self):
        x = self.i2c.readS16(self.MPU6050_RA_ACCEL_XOUT_H)
        y = self.i2c.readS16(self.MPU6050_RA_ACCEL_YOUT_H)
        z = self.i2c.readS16(self.MPU6050_RA_ACCEL_ZOUT_H)
        
        return x, y, z       