import time
import datetime
import json
import serial
import wiringpi2 as wiringpi

arduino = serial.Serial('/dev/ttyAMA0', baudrate=115200, timeout=3.0)

gpio = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_GPIO)
gpio.pinMode(20, 0)
gpio.pinMode(21, 0)

path_BD_file = "//home//pi//json_station//prueba2.txt"
path_request_file = "//home//pi//json_station//request2.txt"
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
        #print (json.dumps({"nodeStatus":nodeStatus,"nodeId":nodeId,"vehicle":{"charger":vehicleCharger, "vehicle_id":vehicleId, "vehicleStatus":vehicleStatus}}))


def formatRequest ():
    x = 0
    campo2 = {"vehicle_id":0, "charger":0, "vehicleStatus":"RELEASED"}
    campo1 = {"nodeId":0, "nodeStatus":0, "nodeAvailability":0, "vehicle":campo2}
    nodes = []
    for i in range(1, 31):
        nodes.append(campo1)
     
    archivo = open(path_request_file, "w")
    json.dump({'stationId':0, 'updateTime':0, 'voltageSource24':0, 'voltageSource12':0, "nodes":nodes}, archivo, indent=4)
    archivo.close()
    archivo = open(path_request_file, "r")
    json_r = archivo.read()
    decoded_file = json.loads(json_r)
    while True:
        try:
            decoded_file["nodes"][x]["nodeId"] = x + 1
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
            if (decoded_file["nodes"][x]["nodeId"]) == (decoded_trama["Nn"]):
     
                if gpio.digitalRead(20) == 1:
                    (decoded_file["voltageSource24"]) = "ok"
                else:
                    (decoded_file["voltageSource24"]) = "no voltage"

                if gpio.digitalRead(21) == 1:
                    (decoded_file["voltageSource12"]) = "ok"
                else:
                    (decoded_file["voltageSource12"]) = "no voltage"    

                (decoded_file["updateTime"]) = time.time()
                (decoded_file["stationId"]) = (decoded_trama["Sn"])
                (decoded_file["nodes"][x]["vehicle"]["vehicle_id"]) = (decoded_trama["Bc"])
                (decoded_file["nodes"][x]["vehicle"]["charger"]) = (decoded_trama["Bv"])
                #(decoded_file["nodes"][x]["vehicle"]["vehicleStatus"]) = "LOCKED"
                (decoded_file["nodes"][x]["nodeStatus"]) = (decoded_trama["Ni"])
                (decoded_file["nodes"][x]["nodeAvailability"]) = (decoded_trama["Ep"])
                archivo = open(path_request_file, "w")
                json.dump(decoded_file, archivo, indent=4)
                archivo.close()
                break
            x += 1
        except IndexError:
            print ("Nodo no encontrado")
            break


def writeRequest():
    archivo = open(path_request_file, "r")
    json_r = archivo.read()
    decoded_file = json.loads(json_r)
    archivo.close()
    print (decoded_file)
    
    

def sendLocked ( frame):
    dataframe = frame
    decoded_trama = json.loads(dataframe)
    if decoded_trama["Ni"] == 0 or decoded_trama["Ni"] == 1 or decoded_trama["Ni"] == 3 or decoded_trama["Ni"] == 6:
        writeVehiclestatus (decoded_trama["Nn"], "LOCKED")
    else:
        writeVehiclestatus (decoded_trama["Nn"], "RELEASED")
    print (json.dumps({"nodeStatus":decoded_trama["Ni"], "nodeId":decoded_trama["Nn"], "vehicle":{"charger":decoded_trama["Bv"], "vehicle_id":decoded_trama["Bc"], "vehicleStatus":"LOCKED"}}))
        
        

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
            if (decoded_file["nodes"][x]["nodeId"]) == (node):
                (decoded_file["nodes"][x]["vehicle"]["vehicleStatus"]) = vehicle
                archivo = open(path_request_file, "w")
                json.dump(decoded_file, archivo, indent=4)
                archivo.close()
                break
 
            x += 1
        except IndexError:
            print ("Nodo no encontrado")
            break
    

      

#buscar.writeBD(1, 21016, "bike code", 100) # funcion para escribir datos en la base de usuario con el facility code, el user code, nombre de la columna y la informacion que se desea modificar de esa columna
#print (buscar.user(2223, 1438)) # devuelve un estring con "ok" si el usuario cumple para prestamo o "no" si el usuario no cumple para el prestamo

#formatRequest() # funcion para limpiar y crear el archivo que contiene el json de los request
#frame = '{"Sn":0,"Bc":4,"Bv":34,"Nn":5,"Ni":0,"Ep":0}'
#writeReq.writeRequest(frame) # funcion para escribir una trama de datos en el archivo que contiene el json request
#writeReq.sendLocked(frame)
#print (writeReq.nodeRules()) # devuelve una lista con el nodo que cumple con las condiciones para prestar y el numero del codigo de la bicicleta o un string diciendo que no hy nodods disponibles
#funcion.sendData("request", 0, 0, 0, 0, 0, 0) # funcion para enviar la informacion necesaria para realizar request, liberacion, prender luces o apagar cargadores, argumentos de funcion y nodo 
#buscar.clean_user_BD(frame) # usa la trama recibida request y busca el codigo de la bicicleta para lipiarlo de la base de datos
#writeReq.writeVehiclestatus(3, "ok") # escribe el estado ok o no de un vehiculo, esta funcion se aplica para el reporte de fallas
#rules = writeReq.nodeRules()
#funcion.sendData("releaseNode", rules[0], rules[1], rules[2], rules[3], rules[4], rules[5])


