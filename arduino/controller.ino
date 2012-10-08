// Arduino standard library imports
#include <Wire.h>
#include <Servo.h>

// Custom library imports
#include "I2Cdev.h"
#include "PID_v1.h"
#include "HMC5883L.h"
#include "MPU6050_6Axis_MotionApps20.h"


// Create sensor objects
MPU6050 mpu;
HMC5883L mag;

// MPU control/status vars
bool dmpReady = false;  // set true if DMP init was successful
uint8_t mpuIntStatus;   // holds actual interrupt status byte from MPU
uint8_t devStatus;      // return status after each device operation (0 = success, !0 = error)
uint8_t packetSize;    // expected DMP packet size (default is 42 bytes)
uint16_t fifoCount;     // count of all bytes currently in FIFO
uint8_t fifoBuffer[64]; // FIFO storage buffer

// orientation/motion vars
Quaternion q;           // [w, x, y, z]         quaternion container
VectorFloat gravity;    // [x, y, z]            gravity vector
double ypr[3];          // [yaw, pitch, roll]   yaw/pitch/roll container and gravity vector
int16_t magv[3];        // [x, y, z]            magnetometer x/y/z

// Serial variables
char serial_buffer_command[10];      // used to storage command name
char serial_buffer_value[20];        // used to storage command value
uint8_t serial_command;
int8_t serial_com_i = 0;                // i used during serial communication
boolean serial_data = false;         // defines if we are receiveding command name or value
boolean serial_com_complete = false; // goes true after receiving the delimeter character |

// Servo PWM objects & PIN definitions
Servo esc_1;
Servo esc_2;
Servo esc_3;
Servo esc_4;

#define esc_1_pin 6  // rotor 1
#define esc_2_pin 9  // rotor 2
#define esc_3_pin 10 // rotor 3
#define esc_4_pin 11 // rotor 4

// Controller variables
int8_t throttle = 0;
int8_t rudder   = 0;
int8_t elevator = 0;
int8_t aileron  = 0;

// PID definitions
double yaw, pitch, roll, xPIDSpeed, yPIDSpeed, zPIDSpeed;

double offsetAngleYaw   = 0.00;
double offsetAnglePitch = -0.02; // Sensor offset for maggie
double offsetAngleRoll  = 0.00;

double targetAngleYaw   = 0.00;
double targetAnglePitch = 0.00;
double targetAngleRoll  = 0.00;

double Kp = 39.00;
double Ki = 10.00;
double Kd = 35.00;

PID yaw_pid(&ypr[0], &zPIDSpeed, &targetAngleYaw, Kp, Ki, Kd, DIRECT);
PID pitch_pid(&ypr[1], &yPIDSpeed, &targetAnglePitch, Kp, Ki, Kd, DIRECT);
PID roll_pid(&ypr[2], &xPIDSpeed, &targetAngleRoll, Kp, Ki, Kd, DIRECT);

// Measure battery voltage
#define BATTERY_V_PIN A0
uint16_t sensor_battery_voltage;
float battery_voltage;

// Blinking LED to indicate activity
#define LED_PIN 13
#define BLINK_INTERVAL 500 // interval at which to blink (milliseconds)
bool blinkState = false;
long previousMillis = 0;  // will store last time LED was updated

// Interrupt detection routine
volatile bool mpuInterrupt = false; // indicates whether MPU interrupt pin has gone high
void dmpDataReady() {
    mpuInterrupt = true;
}

// Read current FREE ram
int freeRam () {
    extern int __heap_start, *__brkval; 
    int v;
    
    return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval); 
}

void setup() {
    // Join i2c bus as master
    Wire.begin();
    
    // Initialize serial communication
    Serial.begin(115200);

    // Attach all of our servo objects to the correct pins
    Serial.println(F("Attaching servo control to ESC pins"));  
    esc_1.attach(esc_1_pin);
    esc_2.attach(esc_2_pin);
    esc_3.attach(esc_3_pin);
    esc_4.attach(esc_4_pin);
    
    // Set PWM high amplitude length to 1ms
    esc_1.writeMicroseconds(1000); 
    esc_2.writeMicroseconds(1000); 
    esc_3.writeMicroseconds(1000);     
    esc_4.writeMicroseconds(1000); 

    // Initialize device
    Serial.println(F("Initializing I2C devices"));
    mpu.initialize();    
    mag.initialize();

    // Define accelerometer offsets
    // THIS IS the correct place where to apply accelerometer offsets
    // DONT play with these values unleas you really have to and know what you are doing.
    //mpu.setXAccelOffset(-4348); // Default -4348
    //mpu.setYAccelOffset(1255);  // Default 1273
    //mpu.setZAccelOffset(1648); // Default 1648
    
    // Verify connection
    Serial.println(F("Testing device connections"));
    Serial.println(mpu.testConnection() ? F("MPU6050 connection successful") : F("MPU6050 connection failed"));
    Serial.println(mag.testConnection() ? F("HMC5883L connection successful") : F("HMC5883L connection failed"));
   
    // load and configure the DMP
    Serial.println(F("Initializing DMP"));
    devStatus = mpu.dmpInitialize();   
    
    // make sure it worked (returns 0 if so)
    if (devStatus == 0) {        
        // turn on the DMP, now that it's ready
        Serial.println(F("Enabling DMP"));
        mpu.setDMPEnabled(true);

        // enable Arduino interrupt detection
        Serial.println(F("Enabling interrupt detection"));
        attachInterrupt(0, dmpDataReady, RISING);
        mpuIntStatus = mpu.getIntStatus();    
        
        // set our DMP Ready flag so the main loop() function knows it's okay to use it
        Serial.println(F("DMP ready! Waiting for first interrupt"));
        dmpReady = true;

        // get expected DMP packet size for later comparison
        packetSize = mpu.dmpGetFIFOPacketSize();            
        
    } else {
        // ERROR!
        // 1 = initial memory load failed
        // 2 = DMP configuration updates failed
        // (if it's going to break, usually the code will be 1)
        Serial.print(F("DMP Initialization failed (code "));
        Serial.print(devStatus);
        Serial.println(F(")"));
    }
    
    // PID settings & limits
    yaw_pid.SetOutputLimits(-20, 20);
    yaw_pid.SetMode(AUTOMATIC);
    yaw_pid.SetSampleTime(10);
    
    pitch_pid.SetOutputLimits(-1000, 1000);
    pitch_pid.SetMode(AUTOMATIC);
    pitch_pid.SetSampleTime(10);
    
    roll_pid.SetOutputLimits(-1000, 1000);
    roll_pid.SetMode(AUTOMATIC);
    roll_pid.SetSampleTime(10);
    
    // Initialize the digital pin as output
    pinMode(LED_PIN, OUTPUT);
    
    // Report FREE ram
    Serial.print(F("Free RAM: "));
    Serial.println(freeRam ());   
}


void loop() {
    // Dont do anything unless dmp is fully initialized and ready
    if (!dmpReady) return;
    
    if (Serial.available() > 0) {
        // serial_data = false, we are reading command
        if (serial_data == false) {
            serial_buffer_command[serial_com_i] = Serial.read();

            if (serial_buffer_command[serial_com_i] == '[') {
                // this piece of code protects the command and data from being hi-jacked by some
                // left over data in the Serial.read(), it drops everything in the buffer prior
                // to the "wrapper-character"
                
                memset(serial_buffer_command, 0, sizeof(serial_buffer_command));
                serial_com_i = -1;
            } else if (serial_buffer_command[serial_com_i] == ':') {
                serial_buffer_command[serial_com_i] = '\0';
                
                // We read the last char coressponding to command
                serial_data = true;
                serial_com_i = -1;
            }                       
        } else if (serial_data == true) {
            serial_buffer_value[serial_com_i] = Serial.read();

            if (serial_buffer_value[serial_com_i] == ']') {
                serial_buffer_value[serial_com_i] = '\0';
                
                // We read the last char corresponding to value and transmission
                serial_com_i = -1;
                serial_com_complete = true;
            } 
        }
        
        serial_com_i++;
 
        // when the transmission completes, do something useful with recieved data and empty buffers
        if (serial_com_complete) {
            serial_data = false;
            serial_com_complete = false;
            
            //Serial.print(serial_buffer_command); 
            //Serial.print(serial_buffer_value);
            
            // atoi()   // string to integer
            // atol()   // string to long integer
            // atof()   // string to float/double
            // strtod() // string to double
            // strcmp() // string compared to string, 0 = strings match
            // strtok() // split string into tokens
            
            serial_command = (uint8_t) atoi(serial_buffer_command);
            
            switch (serial_command) {
                case 1: // throttle
                    throttle = (int8_t) atoi(serial_buffer_value);
                    
                    targetAngleYaw = (rudder / 180 * M_PI) + offsetAngleYaw;
                    targetAnglePitch = (elevator / 180 * M_PI) + offsetAnglePitch;
                    targetAngleRoll = (aileron / 180 * M_PI) + offsetAngleRoll;
                break;
                case 2: // rudder
                    rudder = (int8_t) atoi(serial_buffer_value);
                    targetAngleYaw = (rudder / 180 * M_PI) + offsetAngleYaw;
                break;
                case 3: // elevator
                    elevator = (int8_t) atoi(serial_buffer_value);
                    targetAnglePitch = (elevator / 180 * M_PI) + offsetAnglePitch;
                break;
                case 4: // aileron
                    aileron = (int8_t) atoi(serial_buffer_value);
                    targetAngleRoll = (aileron / 180 * M_PI) + offsetAngleRoll;
                break;
                case 5: // yaw PID offset
                    offsetAngleYaw = atof(serial_buffer_value);
                    targetAngleYaw = (rudder / 180 * M_PI) + offsetAngleYaw;
                break;
                case 6: // pitch PID offset
                    offsetAnglePitch = atof(serial_buffer_value);
                    targetAnglePitch = (elevator / 180 * M_PI) + offsetAnglePitch;
                break;
                case 7: // roll PID offset
                    offsetAngleRoll = atof(serial_buffer_value);
                    targetAngleRoll = (aileron / 180 * M_PI) + offsetAngleRoll;
                break;                
                case 8: // yaw PID tunings
                {
                    char * Kp_value = strtok(serial_buffer_value, ",");
                    char * Ki_value = strtok(NULL, ",");
                    char * Kd_value = strtok(NULL, ",");
                    
                    // apply the new PID settings
                    yaw_pid.SetTunings(atof(Kp_value), atof(Ki_value), atof(Kd_value));  
                }
                break;
                case 9: // pitch PID tunings
                {
                    char * Kp_value = strtok(serial_buffer_value, ",");
                    char * Ki_value = strtok(NULL, ",");
                    char * Kd_value = strtok(NULL, ",");
                    
                    // apply the new PID settings
                    pitch_pid.SetTunings(atof(Kp_value), atof(Ki_value), atof(Kd_value));    
                }
                break;
                case 10: // roll PID tunings
                {
                    char * Kp_value = strtok(serial_buffer_value, ",");
                    char * Ki_value = strtok(NULL, ",");
                    char * Kd_value = strtok(NULL, ",");
                    
                    // apply the new PID settings
                    roll_pid.SetTunings(atof(Kp_value), atof(Ki_value), atof(Kd_value));     
                }
                break;
                case 11: // request battery voltage
                    sensor_battery_voltage = analogRead(BATTERY_V_PIN);
                    battery_voltage = sensor_battery_voltage * (5.0 / 1023.0);
                    
                    Serial.print(F("["));
                    Serial.print(11);
                    Serial.print(F(":"));
                    Serial.print(battery_voltage);
                    Serial.println(F("]"));
                break;
                default:
                    // error message
                    Serial.println(F("Unrecognized command"));
            }
            
            // empty buffers
            memset(serial_buffer_command, 0, sizeof(serial_buffer_command));
            memset(serial_buffer_value, 0, sizeof(serial_buffer_value));
        }
    }     
    
    // Only run if mpuInterrupt gone HIGH or fifoCount >= packetSize
    // This allows loop to itterate freely (like in Blink Without Delay example)
    if (mpuInterrupt || fifoCount >= packetSize) {
        // reset interrupt flag and get INT_STATUS byte
        mpuInterrupt = false;
        mpuIntStatus = mpu.getIntStatus();

        // get current FIFO count
        fifoCount = mpu.getFIFOCount();

        // check for overflow (this should never happen unless our code is too inefficient)
        if ((mpuIntStatus & 0x10) || fifoCount == 1024) {
            // reset so we can continue cleanly
            mpu.resetFIFO();
            Serial.println(F("FIFO overflow!"));

            // otherwise, check for DMP data ready interrupt
        } else if (mpuIntStatus & 0x02 && fifoCount >= packetSize) {  
            // read a packet from FIFO
            mpu.getFIFOBytes(fifoBuffer, packetSize);
            
            // Track FIFO count here in case there is > 1 packet available
            // (this lets us immediately read more without waiting for an interrupt)
            fifoCount -= packetSize;

            // Get the latest magnetometer values
            mag.getHeading(&magv[0], &magv[1], &magv[2]);            
            
            // Calculate yaw/pitch/roll
            mpu.dmpGetQuaternion(&q, fifoBuffer);
            mpu.dmpGetGravity(&gravity, &q);
            mpu.dmpGetYawPitchRoll(ypr, &q, &gravity);  
            
            
            /*
            Serial.print(ypr[0]);
            Serial.print(" ");
            Serial.print(ypr[1]);
            Serial.print(" ");
            Serial.println(ypr[2]);
            */
            
            // display Euler angles in degrees
            /*
            Serial.print(ypr[0] * 180 / M_PI);
            Serial.print(F("\t"));
            Serial.print(ypr[1] * 180 / M_PI);
            Serial.print(F("\t"));
            Serial.print(ypr[2] * 180 / M_PI);
            Serial.print(F("\t"));
            Serial.print(magv[0]);
            Serial.print(F("\t"));
            Serial.print(magv[1]);
            Serial.print(F("\t"));
            Serial.println(magv[2]);
            */
            
            // only compute PID's if there is enough throttle
            if (throttle > 10) {            
                yaw_pid.Compute();
                pitch_pid.Compute();
                roll_pid.Compute();
            }
            
            // range should be from 1000 to 2000
            esc_1.writeMicroseconds(1000 + (throttle * 10) - yPIDSpeed - xPIDSpeed - zPIDSpeed);
            esc_2.writeMicroseconds(1000 + (throttle * 10) - yPIDSpeed + xPIDSpeed + zPIDSpeed);
            esc_3.writeMicroseconds(1000 + (throttle * 10) + yPIDSpeed + xPIDSpeed - zPIDSpeed);
            esc_4.writeMicroseconds(1000 + (throttle * 10) + yPIDSpeed - xPIDSpeed + zPIDSpeed);
        }
    }
    // Blinking LED indicating
    unsigned long currentMillis = millis();   
    if(currentMillis - previousMillis > BLINK_INTERVAL) {
        // save the last time you blinked the LED 
        previousMillis = currentMillis;
        
        blinkState = !blinkState;
        digitalWrite(LED_PIN, blinkState);
    }    
}