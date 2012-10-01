#!/usr/bin/python

# GPL license should be here

# Python Standard Library Imports
import socket
import subprocess
import os
import sys
import time

# External Imports
import tornado.ioloop
import tornado.web
import tornado.escape

# Custom Imports
import config
from drivers import pca9685
from sensors import mpu6050


# Time Tracking
script_started = time.time()


# Function definitions      
class Duller(object):
    # Duller Class (used to smooth out values)  
    average = 0.0
    
    def __init__(self, size):
        self.size = size
        self.history = [0] * self.size
        
    def update(self, value):
        del self.history[0]
        self.history.append(value)
        self.average = sum(self.history) / self.size
        return self.average   


def rotor_handler():
    # Explanation for the numeric values
    # 1 second = 1000 ms
    # PWM frequency is 50hz, 1000 ms / 50 = 20ms amplitude width
    # Servo duty cycle from 0% to 100% equals 1ms to 2ms amplitude high
    # 1 amplitude width = 20 ms = 4096, 1ms = from 0 to 203.8 = 204.8
    # 1% of duty cycle = 2.04 which is then multiplied by rotor values and stabilization values
    # Tadaaa O.o
    
    # rotor-1
    pwm.setPWM(0, 0, int(203.8 + (2.04 * (rotors['rotor-1'] + stabilization['rotor-1']))))
    # rotor-2
    pwm.setPWM(1, 0, int(203.8 + (2.04 * (rotors['rotor-2'] + stabilization['rotor-2']))))
    # rotor-3
    pwm.setPWM(2, 0, int(203.8 + (2.04 * (rotors['rotor-3'] + stabilization['rotor-3']))))
    # rotor-4
    pwm.setPWM(3, 0, int(203.8 + (2.04 * (rotors['rotor-4'] + stabilization['rotor-4']))))  
    
    
def sensors():
    # This function acts like an async loop (that is called every X ms by the tornado IOLoop)
    accel_x, accel_y, accel_z = mpu.readAccel() 
    
    ax = accel_x_duller.update(accel_x)
    ay = accel_y_duller.update(accel_y)
    
    gyro_x, gyro_y, gyro_z = mpu.readGyro()
    
    gx = gyro_x_duller.update(gyro_x)
    gy = gyro_y_duller.update(gyro_y)
    
    # Used for debugging
    #print(x)
    #print(y)
    
    # Stabilization kicks in only after rotors are already running
    # This protects the multicopter from an inicial unwanted tilt due to not-leveled surface
    # stabilization_cutoff is uniqe for every multicopter and should be defined in the configuration file
    if config.stabilization_cutoff < state['throttle']:
        # Flight stabilisation depending on the flight mode
        #
        # change_required variable indicates if there should be an stabilization value change
        # if there wasn't and quadcopter/multicopter is leveled this variable stays False
        # which skips executing additional lines of code required to round the stabilization values and update servo driver
        # this helps decrease the cpu usage by "alot"    
        change_required = False
        
        if config.flight_mode == 'x':
            # Currently in development
            if ax > config.stabilization_accuracy or ax < -config.stabilization_accuracy:
                change_required = True
                
                if ax > config.stabilization_accuracy:
                    # Right too high
                    stabilization['rotor-2'] -= config.stabilization_amount
                    stabilization['rotor-3'] -= config.stabilization_amount
                else:
                    # Left too high
                    stabilization['rotor-1'] -= config.stabilization_amount
                    stabilization['rotor-4'] -= config.stabilization_amount                    
            if ay > config.stabilization_accuracy or ay < -config.stabilization_accuracy:
                change_required = True
                
                if ay > config.stabilization_accuracy:
                    # Front too high
                    stabilization['rotor-1'] -= config.stabilization_amount
                    stabilization['rotor-2'] -= config.stabilization_amount                      
                else:
                    # Back too high
                    stabilization['rotor-3'] -= config.stabilization_amount
                    stabilization['rotor-4'] -= config.stabilization_amount                  
        elif config.flight_mode == '+':
            # Sadly this is still broken =(
            # + mode is temporarily abandoned untill i get another frame sorry =(
            if ax > config.stabilization_accuracy or ax < -config.stabilization_accuracy:
                change_required = True
                
                if ax < config.stabilization_accuracy:
                    # Right too high
                    if stabilization['rotor-2'] > 0:
                        stabilization['rotor-2'] -= config.stabilization_amount
                    else:
                        stabilization['rotor-1'] += config.stabilization_amount
                        stabilization['rotor-3'] += config.stabilization_amount
                        stabilization['rotor-4'] += config.stabilization_amount
                else:
                    # Left too high
                    if stabilization['rotor-4'] > 0:
                        stabilization['rotor-4'] -= config.stabilization_amount
                    else:
                        stabilization['rotor-1'] += config.stabilization_amount
                        stabilization['rotor-2'] += config.stabilization_amount
                        stabilization['rotor-3'] += config.stabilization_amount
                        
            if ay > config.stabilization_accuracy or ay < -config.stabilization_accuracy:
                change_required = True
                
                if ay < config.stabilization_accuracy:
                    # Back too high
                    if stabilization['rotor-3'] > 0:
                        stabilization['rotor-3'] -= config.stabilization_amount
                    else:
                        stabilization['rotor-1'] += config.stabilization_amount
                        stabilization['rotor-2'] += config.stabilization_amount
                        stabilization['rotor-4'] += config.stabilization_amount
                else:
                    # Front too high
                    if stabilization['rotor-1'] > 0:
                        stabilization['rotor-1'] -= config.stabilization_amount
                    else:
                        stabilization['rotor-2'] += config.stabilization_amount
                        stabilization['rotor-3'] += config.stabilization_amount
                        stabilization['rotor-4'] += config.stabilization_amount
        
        if change_required:
            # Debug
            print(stabilization)
            
            # Smooth out the values        
            #stabilization['rotor-1'] = round(stabilization['rotor-1'], 2)
            #stabilization['rotor-2'] = round(stabilization['rotor-2'], 2)
            #stabilization['rotor-3'] = round(stabilization['rotor-3'], 2)
            #stabilization['rotor-4'] = round(stabilization['rotor-4'], 2)
        
            # update rotor handler with the latest stabilization changes
            rotor_handler()    

            
# Main flight control
def controll(name, value):
    global state
    global rotors
    
    # Temporary objects
    state_temporary = dict(state)   
    rotors_temporary = dict(rotors)
    
    # New value
    state_temporary[name] = value
    
    # Controls are applied in layers
    # Current priority is
    #
    # 1. throttle
    # 2. elevator
    # 3. rudder
    # 4. aileron
    
    # throttle
    rotors_temporary['rotor-1'] = state_temporary['throttle']
    rotors_temporary['rotor-2'] = state_temporary['throttle']
    rotors_temporary['rotor-3'] = state_temporary['throttle']
    rotors_temporary['rotor-4'] = state_temporary['throttle']
    
    
    # Flight Modes
    
    # X Flight Mode
    if config.flight_mode == 'x':
        # This section is not ready yet, because "Maggie" is build in + Flight Mode
        pass
    
    # + Flight Mode
    elif config.flight_mode == '+':
        if state_temporary['elevator'] == 0:
            pass
        elif state_temporary['elevator'] > 0:
            rotors_temporary['rotor-3'] += state_temporary['elevator']    
        elif state_temporary['elevator'] < 0:
            rotors_temporary['rotor-1'] += abs(state_temporary['elevator'])
        
        if state_temporary['rudder'] == 0:
            pass
        elif state_temporary['rudder'] > 0:
            rotors_temporary['rotor-2'] += state_temporary['rudder']
            rotors_temporary['rotor-4'] += state_temporary['rudder']
        elif state_temporary['rudder'] < 0:
            rotors_temporary['rotor-1'] += abs(state_temporary['rudder']) 
            rotors_temporary['rotor-3'] += abs(state_temporary['rudder'])
        
        if state_temporary['aileron'] == 0:
            pass
        elif state_temporary['aileron'] > 0:            
            rotors_temporary['rotor-4'] += state_temporary['aileron']
        elif state_temporary['aileron'] < 0:        
            rotors_temporary['rotor-2'] += abs(state_temporary['aileron'])
    
    
    for val in rotors_temporary.values():
        # Protection loop (no values below 0 are allowed)
        if val < 0 or val > 100:
            print("You can't do that !!! " + name + ' ' + str(val))
            
            # Return False back to the UI
            return False
            
    # all went fine
    # update global objects with latest data
    state[name] = value
    rotors = dict(rotors_temporary)
    
    # execute rotor_handler (so the latest changes would be applied immediatly)
    rotor_handler()

    # Return True that will be passed back to the UI
    return True 
    

def connection_lost():
    # this is an emergency function that should stabilize the copter in the air & wait for connection to be re-established
    print('No activity in last 5 seconds, did we lost connection to the client?')
    
    # reset all of the controls except throttle to 0
    state['rudder'] = 0
    state['elevator'] = 0
    state['aileron'] = 0
    
    # set the copter into "static" mode until connection is restored
    rotors['rotor-1'] = state['throttle']
    rotors['rotor-2'] = state['throttle']
    rotors['rotor-3'] = state['throttle']
    rotors['rotor-4'] = state['throttle']
    
    # update our rotors
    rotor_handler()
    

# Driver initialization
pwm = pca9685.PCA9685(0x40)
pwm.setPWMFreq(50)

# Sensor initialization
mpu = mpu6050.MPU6050()
print('Accelerometer offsets ... x: %s' % mpu.readAccelOffsetX()),
print('y: %s' % mpu.readAccelOffsetY()),
print('z: %s' % mpu.readAccelOffsetZ()),
print('Duller: %s' % config.accelerometer_duller_size)

print('Gyroscope offsets ... x: %s' % mpu.readGyroOffsetX()),
print('y: %s' % mpu.readGyroOffsetY()),
print('z: %s' % mpu.readGyroOffsetZ()),
print('Duller: %s' % config.gyroscope_duller_size)

accel_x_duller = Duller(config.accelerometer_duller_size)
accel_y_duller = Duller(config.accelerometer_duller_size)
accel_z_duller = Duller(config.accelerometer_duller_size)

gyro_x_duller = Duller(config.gyroscope_duller_size)
gyro_y_duller = Duller(config.gyroscope_duller_size)
gyro_z_duller = Duller(config.gyroscope_duller_size)

    
# Default Controller values that are served to front-end interface after initial load
state = {
    'throttle' : 0,
    'rudder'   : 0,
    'elevator' : 0,
    'aileron'  : 0}

# Raw rotor "load" that are applied via rotor_handler    
rotors = {
    'rotor-1' : 0,
    'rotor-2' : 0,
    'rotor-3' : 0,
    'rotor-4' : 0}

# Raw stabilization values that are added/applied on top of the raw rotor loads    
stabilization = {
    'rotor-1' : 0,
    'rotor-2' : 0,
    'rotor-3' : 0,
    'rotor-4' : 0}

   
# Tornado class definitions.
class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.redirect('/static/index.html')


class FaviconHandler(tornado.web.RequestHandler):
    def get(self):
        self.finish('')
        
        
class CommandHandler(tornado.web.RequestHandler):
    def get(self, name, value):
        print('Received command ' + name + ' = ' + value)
        value = int(value)
        status = controll(name, value)
        self.finish(str(status).lower())
        
        
class CurrentStateHandler(tornado.web.RequestHandler):
    def get(self):
        self.finish(tornado.escape.json_encode(state))


class AliveHandler(tornado.web.RequestHandler):  
    connection_status = None
    
    def get(self):
        if AliveHandler.connection_status:
            tornado.ioloop.IOLoop.instance().remove_timeout(AliveHandler.connection_status)

        AliveHandler.connection_status = tornado.ioloop.IOLoop.instance().add_timeout(time.time() + 5, connection_lost)

    
print('Starting QuadRotor Remote Control Interface ...')
server = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/favicon.ico', FaviconHandler),
    (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': './static'}),
    (r'/command/(throttle|rudder|elevator|aileron)/(-?[0-9]+)', CommandHandler),
    (r'/state', CurrentStateHandler),
    (r'/alive', AliveHandler)
])

server.listen(80)

# Async loops
sensors_loop = tornado.ioloop.PeriodicCallback(sensors, config.sensor_refresh_rate)
sensors_loop.start()

print('All is ready! (' + str(time.time() - script_started) + ') seconds')

# Start the main tornado instance
tornado.ioloop.IOLoop.instance().start()