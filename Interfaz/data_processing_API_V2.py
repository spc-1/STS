import time
import datetime
import json
import urllib2
import serial
import wiringpi2 as wiringpi

arduino = serial.Serial('/dev/ttyAMA0', baudrate=115200, timeout=3.0)

gpio = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_GPIO)
gpio.pinMode(20, 0)
gpio.pinMode(21, 0)

path_BD_file = "//home//pi//json_station//prueba2.txt"
path_request_file = "//home//pi//json_station//request3.txt"
flag_request = 0

def sendData( func, nod):
    global flag_request
    flag_request = 0
    ciclos = 0
    
    function = func
    nodeId = nod
    
    if function == "request":
        arduino.write("*C$")
        time.sleep(1.7)
        arduino.write("*R$")
            
        while ciclos < 800:
            time.sleep(0.001)
            #print flag_request
            if flag_request == 1:
                break
            else:
                ciclos += 1
        if flag_request == 0:
            arduino.write("*C$")
            time.sleep(1.7)
            arduino.write("*R$")
        else:
            flag_request = 0
      
    elif function == "turnLihgtsOn":
        arduino.write("*E$")
        arduino.write("*E$")

    elif function == "turnLihgtsOff":
        arduino.write("*A$")
        arduino.write("*A$")

    elif function == "turnChargersOff":
        arduino.write("*C$")
        arduino.write("*C$")

    elif function == "releaseNode":
        arduino.write("*"+str(nodeId)+"$")
        arduino.write("*"+str(nodeId)+"$")
        #writeVehiclestatus (nodeId, vehicleStatus)
        #print (json.dumps({"nodes_attributestatus":status,"node_number":nodeId,"vehicles_attributes":{"charge":vehicleCharger, "vin":vehicleId, "status":vehicleStatus}}))


def formatRequest ():
    x = 0
    campo2 = {"vin":0, "charge":0, "status":"RELEASED"}
    campo1 = {"node_number":0, "status":0, "node_availability":0, "vehicles_attributes":campo2}
    nodes = []
    for i in range(1, 31):
        nodes.append(campo1)
     
    archivo = open(path_request_file, "w")
    json.dump({"station":{'station_number':0, 'voltage_source_24':0, 'voltage_source_12':0, "nodes_attributes":nodes}}, archivo, indent=4)
    archivo.close()
    archivo = open(path_request_file, "r")
    json_r = archivo.read()
    decoded_file = json.loads(json_r)
    while True:
        try:
            decoded_file["station"]["nodes_attributes"][x]["node_number"] = x + 1
            x += 1
                
        except IndexError:
            break
    archivo.close()
    archivo = open(path_request_file, "w")
    json.dump(decoded_file, archivo, indent=4)
    archivo.close()


def writeFrame ( frame):
    global flag_request
    flag_request = 1
    #print flag_request
    dataframe = frame
    decoded_trama = json.loads(dataframe)
    #print (decoded_trama)
    archivo = open(path_request_file, "r")
    json_r = archivo.read()
    decoded_file = json.loads(json_r)
    #print (decoded_file)
    archivo.close()
    x = 0
    while True:
        try:
            if (decoded_file["station"]["nodes_attributes"][x]["node_number"]) == (decoded_trama["Nn"]):
     
                if gpio.digitalRead(20) == 1:
                    (decoded_file["station"]["voltage_source_24"]) = "ok"
                else:
                    (decoded_file["station"]["voltage_source_24"]) = "no voltage"

                if gpio.digitalRead(21) == 1:
                    (decoded_file["station"]["voltage_source_12"]) = "ok"
                else:
                    (decoded_file["station"]["voltage_source_12"]) = "no voltage"    

                
                (decoded_file["station"]["station_number"]) = (decoded_trama["Sn"])
                (decoded_file["station"]["nodes_attributes"][x]["vehicles_attributes"]["vin"]) = (decoded_trama["Bc"])
                (decoded_file["station"]["nodes_attributes"][x]["vehicles_attributes"]["charge"]) = (decoded_trama["Bv"])
                 
                if decoded_trama["Bc"] == 0:
                    if decoded_trama["Ni"] == 0 or decoded_trama["Ni"] == 1 or decoded_trama["Ni"] == 3 or decoded_trama["Ni"] == 6: 
                        (decoded_file["station"]["nodes_attributes"][x]["vehicles_attributes"]["status"]) = "LOCKED"
                    else:
                        (decoded_file["station"]["nodes_attributes"][x]["vehicles_attributes"]["status"]) = "RELEASED"
                else:
                    (decoded_file["station"]["nodes_attributes"][x]["vehicles_attributes"]["status"]) = "LOCKED"

                #(decoded_file["station"]["nodes_attributes"][x]["vehicles_attributes"]["status"]) = "LOCKED"


                (decoded_file["station"]["nodes_attributes"][x]["status"]) = (decoded_trama["Ni"])
                (decoded_file["station"]["nodes_attributes"][x]["node_availability"]) = (decoded_trama["Ep"])
                archivo = open(path_request_file, "w")
                json.dump(decoded_file, archivo, indent=4)
                archivo.close()
                break
            x += 1
        except IndexError:
            print ("Nodo no encontrado")
            break


def transmitRequest():
    archivo = open(path_request_file, "r")
    json_r = archivo.read()
    archivo.close()
    """
    req = urllib2.Request('localhost:3000/stations/1')
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req, json_r)
    """
    response = '{"node_number":1, "message":"Success"}'
    print (json_r)
    return response
    
    
    

def sendLocked ( frame):
    dataframe = frame
    decoded_trama = json.loads(dataframe)
    if decoded_trama["Ni"] == 0 or decoded_trama["Ni"] == 1 or decoded_trama["Ni"] == 3 or decoded_trama["Ni"] == 6:
        writeVehiclestatus (decoded_trama["Nn"], "LOCKED")
    else:
        writeVehiclestatus (decoded_trama["Nn"], "RELEASED")

    print (json.dumps({"node":{"status":decoded_trama["Ni"], "node_number":decoded_trama["Nn"], "vehicles_attributes":{"charge":decoded_trama["Bv"], "vin":decoded_trama["Bc"], "status":"LOCKED"}}}))
    
    """
    data = json.dumps({"node":{"status":decoded_trama["Ni"], "node_number":decoded_trama["Nn"], "vehicles_attributes":{"charge":decoded_trama["Bv"], "vin":decoded_trama["Bc"], "status":"LOCKED"}}})
    req = urllib2.Request('localhost:3000/nodes/return')
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req, data)
    """
    response = '{"received":"OK"}'
    decoded_response = json.loads(response)
    print (decoded_response["received"])    

def writeVehiclestatus ( nod, vehic):
    node = nod
    vehicle = vehic
    archivo = open(path_request_file, "r")
    json_r = archivo.read()
    decoded_file = json.loads(json_r)
    #print (decoded_file)
    archivo.close()
    x = 0

    while True:
        try:
            if (decoded_file["station"]["nodes_attributes"][x]["node_number"]) == (node):
                (decoded_file["station"]["nodes_attributes"][x]["vehicles_attributes"]["status"]) = vehicle
                archivo = open(path_request_file, "w")
                json.dump(decoded_file, archivo, indent=4)
                archivo.close()
                break
 
            x += 1
        except IndexError:
            print ("Nodo no encontrado")
            break
    

#formatRequest() # funcion para limpiar y crear el archivo que contiene el json de los request
