import json
import urllib2
import pigpio
import time
import serial
from threading import Thread
import wiringpi2 as wiringpi
import data_processing_API_V2 as dp

gpio = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_GPIO)
arduino = serial.Serial('/dev/ttyAMA0', baudrate=115200, timeout=3.0)
go_out = 0
rules = []

class rfidReader(Thread):
    
    def __init__(self, flagL, txt="", txt1="", x=0):
        Thread.__init__(self)
        self.txt = txt
        self.txt1 = txt1
        self.x = x

    def run(self):
       
        while True:
            
            while arduino.inWaiting() > 0:
                self.txt = arduino.read(1)
                self.txt1 += self.txt
                #print self.txt
                #print self.txt1                
                if(self.txt == "}"):
                    #print self.txt1
                    dp.writeFrame(self.txt1)
                    #dp.clean_user_BD(self.txt1)
                    self.x += 1
                    self.txt2 = self.txt1
                    self.txt1 = ""
                    #print self.x
                self.txt = ""
                time.sleep(0.0008)
            if self.x == 1:
                self.decoded = json.loads(self.txt2)
                if self.decoded["Bc"] == 0:
                    if self.decoded["Ni"] == 0 or self.decoded["Ni"] == 1 or self.decoded["Ni"] == 3 or self.decoded["Ni"] == 6: 
                        dp.writeVehiclestatus(self.decoded["Nn"], "LOCKED")
                        print (json.dumps({"node":{"node_number":self.decoded["Nn"], "status":self.decoded["Ni"], "node_availability":self.decoded["Ep"]}}))
                        """
                        self.data = json.dumps({"node":{"node_number":self.decoded["Nn"], "status":self.decoded["Ni"], "node_availability":self.decoded["Ep"]}})
                        self.req = urllib2.Request('localhost:3000/nodes/confirm')
                        self.req.add_header('Content-Type', 'application/json')
                        self.responseConfirm = urllib2.urlopen(self.req, self.data)
                        """
                        self.responseConfirm = '{"received":"OK"}'
                        self.decoded_responseConfirm = json.loads(self.responseConfirm)
                        print (self.decoded_responseConfirm["received"])
                        self.txt1 = ""
                        self.txt2 = ""
                        self.x = 0
                        while arduino.inWaiting() > 0:
                            arduino.read()
                        arduino.flush()
                    else:
                        dp.writeVehiclestatus(self.decoded["Nn"], "RELEASED")
                        print (json.dumps({"node":{"node_number":self.decoded["Nn"], "status":self.decoded["Ni"], "node_availability":self.decoded["Ep"]}}))
                        """
                        self.data = json.dumps({"node":{"node_number":self.decoded["Nn"], "status":self.decoded["Ni"], "node_availability":self.decoded["Ep"]}})
                        self.req = urllib2.Request('localhost:3000/nodes/confirm')
                        self.req.add_header('Content-Type', 'application/json')
                        self.responseConfirm = urllib2.urlopen(self.req, self.data)
                        """
                        self.responseConfirm = '{"received":"OK"}'
                        self.decoded_responseConfirm = json.loads(self.responseConfirm)
                        print (self.decoded_responseConfirm["received"])
                        self.txt1 = ""
                        self.txt2 = ""
                        self.x = 0
                        while arduino.inWaiting() > 0:
                            arduino.read()
                        arduino.flush()
                else:
                    dp.sendLocked(self.txt2) 
                    self.txt1 = ""
                    self.txt2 = ""
                    self.x = 0
                    arduino.flush()
                    
            else:
                self.txt1 = ""
                self.txt2 = ""
                self.x = 0
                arduino.flush()
              
            if go_out == 1:
                break    


class decoder:

   """
   A class to read Wiegand codes 
   """

   def __init__(self, pi, gpio_0, gpio_1, callback, bit_timeout=5):

      self.pi = pi
      self.gpio_0 = gpio_0
      self.gpio_1 = gpio_1

      self.callback = callback

      self.bit_timeout = bit_timeout

      self.in_code = False

      self.pi.set_mode(gpio_0, pigpio.INPUT)
      self.pi.set_mode(gpio_1, pigpio.INPUT)

      self.pi.set_pull_up_down(gpio_0, pigpio.PUD_UP)
      self.pi.set_pull_up_down(gpio_1, pigpio.PUD_UP)

      self.cb_0 = self.pi.callback(gpio_0, pigpio.FALLING_EDGE, self._cb)
      self.cb_1 = self.pi.callback(gpio_1, pigpio.FALLING_EDGE, self._cb)

   def _cb(self, gpio, level, tick):

      """
      Accumulate bits until both gpios 0 and 1 timeout.
      """

      if level < pigpio.TIMEOUT:

         if self.in_code == False:
            self.bits = 1
            self.num = 0

            self.in_code = True
            self.code_timeout = 0
            self.pi.set_watchdog(self.gpio_0, self.bit_timeout)
            self.pi.set_watchdog(self.gpio_1, self.bit_timeout)
         else:
            self.bits += 1
            self.num = self.num << 1

         if gpio == self.gpio_0:
            self.code_timeout = self.code_timeout & 2 # clear gpio 0 timeout
         else:
            self.code_timeout = self.code_timeout & 1 # clear gpio 1 timeout
            self.num = self.num | 1

      else:

         if self.in_code:

            if gpio == self.gpio_0:
               self.code_timeout = self.code_timeout | 1 # timeout gpio 0
            else:
               self.code_timeout = self.code_timeout | 2 # timeout gpio 1

            if self.code_timeout == 3: # both gpios timed out
               self.pi.set_watchdog(self.gpio_0, 0)
               self.pi.set_watchdog(self.gpio_1, 0)
               self.in_code = False
               self.callback(self.bits, self.num)

   def cancel(self):

      """
      Cancel the Wiegand decoder.
      """

      self.cb_0.cancel()
      self.cb_1.cancel()

def callback(bits, value):
    #print("bits={} value={}".format(bits, value))
    value1 = ((value >> 17) & 0xFF)
    value2 = ((value >> 1) & 0xFFFF)
    print (json.dumps({"facility_code":value1, "user_code":value2}))
    """
    data = json.dumps({"facility_code":value1, "user_code":value2})
    req = urllib2.Request('localhost:3000/stations/is_valid_person')
    req.add_header('Content-Type', 'application/json')
    responseCR = urllib2.urlopen(req, data)
    """
    responseCR = '{"status":"OK", "message":"Success"}'
    decoded_responseCR = json.loads(responseCR)
        
    if decoded_responseCR["status"] == "OK":
        dp.sendData("request", 0)
        time.sleep(1.8)
        responseRequest = dp.transmitRequest()
        decoded_responseRequest = json.loads(responseRequest)

        if decoded_responseRequest["node_number"] != 0:
            dp.sendData("releaseNode", decoded_responseRequest["node_number"])

        else:
            print (decoded_responseRequest["message"])

    else:
        print (decoded_response["message"])
    

    """

    time.sleep(2)

    dp.sendData("turnLihgtsOn", 0)

    time.sleep(2)

    dp.sendData("turnLihgtsOff", 0)

    """

rfid = rfidReader(True)
rfid.start()
pi = pigpio.pi()
wieg = decoder(pi, 23, 22, callback)
raw_input()
go_out = 1
