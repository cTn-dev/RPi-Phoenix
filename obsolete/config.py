#!/usr/bin/python

flight_mode = 'x'                # Frame type (x or +) - support for both is in development stage
accelerometer_duller_size = 3    # Default 6 - Duller size (higher the value smoother the output but slower responsivenes)
gyroscope_duller_size = 3        # Same as the above
sensor_refresh_rate = 20         # Pooling rate of installed sensors (bear in mind that lower pooling increases CPU usage)
stabilization_cutoff = 25        # Default 25 - Stabilization kick in and cut off value (representing % of throttle set by control interface)
stabilization_accuracy = 100      # Stabilization Accuracy
stabilization_amount = 0.01      # Stabilization Amount

# Custom Offset Definitions (this values are different for every quadcopter/multicopter!)
# Values defined below are for "Maggie"
accelerometer_offset = {
    'x' : -4378, # Default -4348
    'y' : 1255,  # Default 1273
    'z' : 1648}  # Default 1648
    
gyroscope_offset = {
    'x' : 0, # Default 0
    'y' : 0, # Default 0
    'z' : 0} # Default 0   