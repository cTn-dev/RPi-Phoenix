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
    ser.write('1:' + str(state['throttle']) + '|')
    ser.write('2:' + str(state['rudder'])  + '|')
    ser.write('3:' + str(state['elevator']) + '|')
    ser.write('4:' + str(state['aileron'])  + '|')

    
# Main flight control
def controll(name, value):
    global state
    
    if name == 'aileron':
        if value < 0:
            value = abs(value)
        elif value > 0:
            value = -value

    # New value
    if value >= -100 and value <= 100: # Protection against an itter lag on the client side
        state[name] = value

    rotor_handler()

    # Return True that will be passed back to the UI
    return True 
    

def connection_lost():
    # this is an emergency function that should stabilize the copter in the air & wait for connection to be re-established
    print('No activity in last 10 seconds, did we lost connection to the client?')
    
    # reset all of the controls except throttle to 0
    state['rudder'] = 0
    state['elevator'] = 0
    state['aileron'] = 0
    
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

        AliveHandler.connection_status = tornado.ioloop.IOLoop.instance().add_timeout(time.time() + 10, connection_lost)

    
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