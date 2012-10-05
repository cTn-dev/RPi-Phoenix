#!/usr/bin/python

# Python Standard Library Imports
import time

# External Imports
import tornado.ioloop
import tornado.web
import tornado.escape

# Custom Imports
import config
import serial

# Time Tracking
script_started = time.time()


# Initialize serial object
ser = serial.Serial('/dev/ttyAMA0', 115200) # address of my meduino nano

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
    # all the rotor speeds are served via serila to our arduino
    # 1000 represents 1ms (which is the lowest acceptable value for ESCs)
    ser.write('1:' + str(1000 + (rotors['rotor-1'] * 10))  + '|')
    ser.write('2:' + str(1000 + (rotors['rotor-2'] * 10))  + '|')
    ser.write('3:' + str(1000 + (rotors['rotor-3'] * 10))  + '|')
    ser.write('4:' + str(1000 + (rotors['rotor-4'] * 10))  + '|')

    
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
        if state_temporary['elevator'] == 0:
            pass
        elif state_temporary['elevator'] > 0:
            rotors_temporary['rotor-3'] += state_temporary['elevator'] 
            rotors_temporary['rotor-4'] += state_temporary['elevator']
        elif state_temporary['elevator'] < 0:
            rotors_temporary['rotor-1'] += abs(state_temporary['elevator'])
            rotors_temporary['rotor-2'] += abs(state_temporary['elevator'])
        
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
            rotors_temporary['rotor-1'] += state_temporary['aileron']
            rotors_temporary['rotor-4'] += state_temporary['aileron']
        elif state_temporary['aileron'] < 0:        
            rotors_temporary['rotor-2'] += abs(state_temporary['aileron'])
            rotors_temporary['rotor-3'] += abs(state_temporary['aileron'])
    
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

print('All is ready! (' + str(time.time() - script_started) + ') seconds')

# Start the main tornado instance
tornado.ioloop.IOLoop.instance().start()