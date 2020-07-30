#
# Copyright (c) 2012 Stephen P. Smith
# Copyright (c) 2013 2020 Charles E. Galey
#
# Permission is hereby granted, free of charge, to any person obtaining 
# a copy of this software and associated documentation files 
# (the "Software"), to deal in the Software without restriction, 
# including without limitation the rights to use, copy, modify, 
# merge, publish, distribute, sublicense, and/or sell copies of the Software, 
# and to permit persons to whom the Software is furnished to do so, 
# subject to the following conditions:

# The above copyright notice and this permission notice shall be included 
# in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS 
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR 
# IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Replace libraries by fake ones
import sys
import fake_rpi

sys.modules['RPi'] = fake_rpi.RPi     # Fake RPi
sys.modules['RPi.GPIO'] = fake_rpi.RPi.GPIO # Fake GPIO
sys.modules['smbus'] = fake_rpi.smbus # Fake smbus (I2C)


from multiprocessing import Process, Pipe, Queue, current_process
from subprocess import Popen, PIPE, call
from datetime import datetime
import web, time, random, json, serial, os, ledstrip
import RPi.GPIO as GPIO


class param:
    mode = "auto"
    cycle_time = 2.0
    short_time = 350.0
    short_cycle = 350.0
    duty_cycle = 0.0
    temp_range = 3.0
    set_point = 40.0
    led_mode = "halloween"
    brew_1 = ([0, 0, 0])
    brew_1[0] = 0
    brew_1[1] = 0
    brew_1[2] = 0
    brew_2 = ([0, 0, 0])
    brew_2[0] = 255
    brew_2[1] = 69
    brew_2[2] = 0
    brew_3 = ([0, 0, 0])
    brew_3[0] = 0
    brew_3[1] = 0
    brew_3[2] = 0


def add_global_hook(parent_conn, statusQ):
    
    g = web.storage({"parent_conn" : parent_conn, "statusQ" : statusQ})
    def _wrapper(handler):
        web.ctx.globals = g
        return handler()
    return _wrapper
            

class raspibrew: 
    def __init__(self):
                
        self.mode = param.mode
        self.led_mode = param.led_mode
        self.cycle_time = param.cycle_time
        self.duty_cycle = param.duty_cycle
        self.set_point = param.set_point
        self.short_cycle = param.short_cycle
        self.short_time = param.short_time
        self.temp_range = param.temp_range

    def GET(self):

        return render.raspibrew(self.mode, self.set_point, self.duty_cycle, self.cycle_time, self.led_mode, \
                                self.temp_range, self.short_cycle, self.short_time )
        
    def POST(self):
        data = web.data()
        #print data
        datalist = data.split("&")
        for item in datalist:
            datalistkey = item.split("=")
            if datalistkey[0] == "mode":
                self.mode = datalistkey[1]
            if datalistkey[0] == "ledmode":
                self.led_mode = datalistkey[1]
            if datalistkey[0] == "setpoint":
                self.set_point = float(datalistkey[1])
            if datalistkey[0] == "temprange":
                self.temp_range = float(datalistkey[1])
            if datalistkey[0] == "dutycycle":
                self.duty_cycle = float(datalistkey[1])
            if datalistkey[0] == "shortcycle":
                self.short_cycle = float(datalistkey[1])
            if datalistkey[0] == "shorttime":
                self.short_time = float(datalistkey[1])
            if datalistkey[0] == "cycletime":
                self.cycle_time = float(datalistkey[1])
         
        web.ctx.globals.parent_conn.send([self.mode, self.set_point, self.duty_cycle, self.cycle_time, self.led_mode, \
                                self.temp_range, self.short_cycle, self.short_time])  
        
def gettempFunc(conn):
    p = current_process()
    print('Starting:', p.name, p.pid)
    while (True):
        t = time.time()
        time.sleep(.5) #.1+~.83 = ~1.33 seconds
        num = tempdata()
        elapsed = "%.2f" % (time.time() - t)
        conn.send([num, elapsed])
        
def heatFunc(cycle_time, duty_cycle, conn):
    p = current_process()
    print('Starting:', p.name, p.pid)
    #bus = SMBus(0)
    #bus.write_byte_data(0x26,0x00,0x00) #set I/0 to write
#    hled = ledstrip.strand()
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(11, GPIO.OUT)
    while (True):
        while (conn.poll()): #get last
            cycle_time, duty_cycle = conn.recv()
        conn.send([cycle_time, duty_cycle])  
        if duty_cycle == 0:
            print("Compressor Off")
#            hled.fill(0,0,0,0,1)
            GPIO.output(11, GPIO.LOW)
            time.sleep(cycle_time)
        else:
            print("Compressor On")
#            hled.fill(255,0,0,0,1)
            GPIO.output(11, GPIO.HIGH)
            time.sleep(cycle_time)
        #y = datetime.now()
        #time_sec = y.second + y.microsecond/1000000.0
        #print("%s Thread time (sec) after LED off: %.2f" % (self.getName(), time_sec)

#def ledFunc(led_mode, brew_1, brew_2, brew_3, conn):
#    p = current_process()
#    print('Starting:', p.name, p.pid)
#    led = ledstrip.strand()
#    led_d = 0
#    led_h = 0
#    while (True):
#        while (conn.poll()): #get last
#            led_mode, brew_1, brew_2, brew_3 = conn.recv()
#        conn.send([led_mode, brew_1, brew_2, brew_3])
#        led.fill(brew_1[1],brew_1[2],brew_1[3],1,3)
#        led.fill(brew_2[1],brew_2[2],brew_2[3],4,6)
#        led.fill(brew_3[1],brew_3[2],brew_3[3],7,9)
#        if led_mode == "default":
#            if led_d == 1:
#                pass
#            if led_d == 0:
#                led_h == 0
#                led_d == 1
#                led.even(255,255,0)
#                led.odd(0,0,255)
#        if led_mode == "halloween":
#            if led_h == 1:
#                pass
#            if led_h == 0:
#                led_h == 1
#                led_d == 0
#                led.even(255,165,0)
#                led.odd(128,0,128)
#        conn.send([led_mode, brew_1, brew_2, brew_3]) #shows its alive 

def tempControlFunc(mode, cycle_time, duty_cycle, set_point, led_mode, temp_range, short_cycle, short_time, brew_1, brew_2, brew_3, statusQ, conn):
               
        p = current_process()
        print('Starting:', p.name, p.pid)
        parent_conn_temp, child_conn_temp = Pipe()            
        ptemp = Process(name = "gettempFunc", target=gettempFunc, args=(child_conn_temp,))
        ptemp.daemon = True
        ptemp.start()    
        parent_conn_heat, child_conn_heat = Pipe()           
        pheat = Process(name = "heatFunc", target=heatFunc, args=(cycle_time, duty_cycle, child_conn_heat))
        pheat.daemon = True
        pheat.start() 
 #       parent_conn_led, child_conn_led = Pipe()
 #       pled = Process(name = "ledFunc", target=ledFunc, args=(led_mode, brew_1, brew_2, brew_3, child_conn_led))
 #       pled.start() 

        temp_F_ma_list = []
        temp_F_ma = 0.0
        short_time_1 = 0

        while (True):
            readytemp = False
            while parent_conn_temp.poll():
                temp_C, elapsed = parent_conn_temp.recv() #non blocking receive    
                temp_F = (9.0/5.0)*temp_C + 32
                
                temp_F_ma_list.append(temp_F) 
                
                #print temp_F_ma_list
                #smooth temp data
                #
                if (len(temp_F_ma_list) == 1):
                    temp_F_ma = temp_F_ma_list[0]
                elif (len(temp_F_ma_list) == 2):
                    temp_F_ma = (temp_F_ma_list[0] + temp_F_ma_list[1]) / 2.0
                elif (len(temp_F_ma_list) == 3):
                    temp_F_ma = (temp_F_ma_list[0] + temp_F_ma_list[1] + temp_F_ma_list[2]) / 3.0
                elif (len(temp_F_ma_list) == 4):
                    temp_F_ma = (temp_F_ma_list[0] + temp_F_ma_list[1] + temp_F_ma_list[2] + temp_F_ma_list[3]) / 4.0
                else:    
                    temp_F_ma = (temp_F_ma_list[0] + temp_F_ma_list[1] + temp_F_ma_list[2] + temp_F_ma_list[3] + \
                                                                                            temp_F_ma_list[4]) / 5.0
                    temp_F_ma_list.pop(0) #remove oldest element in list
                    #print("Temp F MA %.2f" % temp_F_ma
                
  
                temp_C_str = "%3.2f" % temp_C
                temp_F_str = "%3.2f" % temp_F
                time.sleep(.005) #wait 5msec
                readytemp = True
            if readytemp == True:
                if mode == "auto":
                    short_time, duty_cycle = sct(set_point, short_time, short_cycle, temp_range, duty_cycle, temp_F)
                    parent_conn_heat.send([cycle_time, duty_cycle]) 
                if mode == "off":
                    pass
                if (not statusQ.full()):    
                    statusQ.put([temp_F_str, elapsed, mode, cycle_time, duty_cycle, set_point, led_mode, \
                                temp_range, short_cycle, short_time]) #GET request
                readytemp == False   
                
            while parent_conn_heat.poll(): #non blocking receive
                cycle_time, duty_cycle = parent_conn_heat.recv()   
                     
            readyPOST = False
            while conn.poll(): #POST settings
                mode, cycle_time, duty_cycle_temp, set_point, led_mode, \
                                temp_range, short_cycle, short_time = conn.recv()
                readyPOST = True
            if readyPOST == True:
                if mode == "auto":
                    print("auto selected")
                    short_time, duty_cycle = sct(set_point, short_time, short_cycle, temp_range, duty_cycle, temp_F)
                    parent_conn_heat.send([cycle_time, duty_cycle])    
                if mode == "off":
                    print("off selected")
                    duty_cycle = 0
                    parent_conn_heat.send([cycle_time, duty_cycle])
                readyPOST = False
            time.sleep(.01)
                    
class getrand:
    def __init__(self):
        pass
    def GET(self):
        #global parent_conn  
        while parent_conn.poll(): #get last
            randnum, mode, cycle_time, duty_cycle, set_point = parent_conn.recv()
        #controlData = parent_conn.recv()
        out = json.dumps({"temp" : randnum,
                          "mode" : mode,
                    "cycle_time" : cycle_time,
                    "duty_cycle" : duty_cycle,
                     "set_point" : set_point})  
        return out
        #return randomnum()
        
    def POST(self):
        pass

def sct(set_point, short_time, short_cycle, temp_range, duty_cycle, temp_F):
    short_time = short_time+1.0
    max_temp = set_point+temp_range
    min_temp = set_point-temp_range

    if temp_F >= max_temp:
        if short_time >= short_cycle:
            duty_cycle=1.0
        else:
            pass
    if temp_F <= min_temp:
        if short_time <= short_cycle:
            duty_cycle=0.0
        else:
            duty_cycle=0.0
            short_time=0
    else:
        pass
    return short_time, duty_cycle

class getstatus:
    
    def __init__(self):
        pass    

    def GET(self):
        #blocking receive
 
        if (statusQ.full()): #remove old data
            for i in range(statusQ.qsize()):
                temp, elapsed, mode, cycle_time, duty_cycle, set_point, led_mode, \
                    temp_range, short_cycle, short_time = web.ctx.globals.statusQ.get() 
        temp, elapsed, mode, cycle_time, duty_cycle, set_point, led_mode, \
            temp_range, short_cycle, short_time = web.ctx.globals.statusQ.get() 
            
        out = json.dumps({ "temp" : temp,
                        "elapsed" : elapsed,
                           "mode" : mode,
                     "cycle_time" : cycle_time,
                     "duty_cycle" : duty_cycle,
                      "set_point" : set_point,
                      "led_mode"  : led_mode,
                      "temp_range"     : temp_range, 
                    "short_cycle" : short_cycle,
                    "short_time"  : short_time})  
        return out
        #return tempdata()
       
    def POST(self):
        pass
    
def randomnum():
    time.sleep(.5)
    return random.randint(0,200)

def tempdata():
    ##change 28-000002b2fa07 to your own temp sensor id
    ##pipe = Popen(["cat","/sys/bus/w1/devices/w1_bus_master1/28-000004148401/w1_slave"], stdout=PIPE)
    pipe = Popen(["cat","/sys/bus/w1/devices/w1_bus_master1/28-000004148401/w1_slave"], stdout=PIPE)
    result = pipe.communicate()[0]
    result_list = result.split("=")
    temp_C = float(result_list[-1])/1000 # temp in Celcius
    #temp_F = (9.0/5.0)*temp_C + 32
    #return "%3.2f" % temp_C
    return temp_C

if __name__ == '__main__':
    
    os.chdir("/var/www")
     
    call(["modprobe", "w1-gpio"])
    call(["modprobe", "w1-therm"])
    call(["modprobe", "i2c-dev"])
    
    urls = ("/", "raspibrew",
        "/getrand", "getrand",
        "/getstatus", "getstatus")

    render = web.template.render("templates/")

    app = web.application(urls, globals()) 
    
    statusQ = Queue(2)       
    parent_conn, child_conn = Pipe()
    p = Process(name = "tempControlFunc", target=tempControlFunc, args=(param.mode, param.cycle_time, param.duty_cycle, param.set_point,    \
                                                              param.led_mode, param.temp_range, param.short_cycle, param.short_time, param.brew_1, param.brew_2, param.brew_3, statusQ, child_conn))
    p.start()
    
    app.add_processor(add_global_hook(parent_conn, statusQ))
     
    app.run()


