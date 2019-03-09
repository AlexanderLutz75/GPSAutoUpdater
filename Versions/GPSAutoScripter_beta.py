from tkinter import *
from tkinter import filedialog

import serial
import serial.tools.list_ports
import time
import re

    
class GPSUpdater:
    def __init__(self):
        self.status = []
        self.GUIstatus=[]

    def statusUpdater(self,statusIndex,message): #helper function used to accomplish the repetative task of updating the status array
        try:
            self.status[statusIndex] = message
            self.GUIstatus[statusIndex].initialize(message)
            root.update()
        except Exception:
            self.status.insert(statusIndex,message)
            self.GUIstatus[statusIndex].initialize(message)
            root.update()


        
    def selectSource(self):
        file = filedialog.askopenfilename()
        if(file)=='':
            print("no file selected")
            return
        txtfile=open(file,"r")
        if(txtfile)=='':
            print("file opening failed")
            return
        self.message=txtfile.read()
        txtfile.close()
        print("file slected and ready for upload")

    def scanPorts(self):
        self.ports = list(serial.tools.list_ports.comports())
        self.ports.sort()
        self.ports[0]="NOT A GPS"
        if(self.ports==[]): #keeps scanning for ports until one connects
            print("no devices connected, Waiting for device")
            time.sleep(1)
            self.scanPorts()
        for index, p in enumerate(self.ports):
            Label(root, text=p[0]).grid(row=(index+1),column=0) # com port label creation           
            self.var = StringVar() #create a empty stringVar
            self.GUIstatus.insert(index,self.var) #put into the array as a placeholder
            Label(root, textvariable=self.GUIstatus[index]).grid(row=(index+1),column=1) #status label creation uses the GUIstatus as text
            
    def findUnits(self): #Creates the logic for checking all connected units
        for index, p in enumerate(self.ports):
            print("----------------------------------------")          
            self.handleUnit(p[0],index) #pass the status index    
            print(self.status[index] + ": " + p[0])      
            print(self.status) #prints the entire status array for debugging.

    def handleUnit(self,port,statusIndex):  #Opens a single COM port and updates the status
        #unfortunately the first pass will crash because the status array doesnt exist yet.
        #This try-except block attempts to work around that.
        try:
            #try to read status array index
            currentStatus = self.status[statusIndex]
        except:
            #if the status array index doesnt exist it is created
            self.status.insert(statusIndex,"NOT CONNECTED")
            self.GUIstatus[statusIndex].initialize("NOT CONNECTED")
            root.update()

        #-------------Port opening------------------------------
        print("opening serial port: " + str(port))
        #create the serial connection to the GPS
        try:
            ser = serial.Serial(port, 115200, timeout=1)
        except Exception:
            print("Cannot open port")
            time.sleep(1)
            return
            
        #--------------------------------------------------------
        #---------------is this port a factory reset GPS unit?-----------------
        #Since a programmed GPS is 9600 this will not restart the upload process
        if(self.status[statusIndex] == "NOT CONNECTED"):
            print("checking for gps on: " + str(port))
            checkIfGPS = "AT!GXBREAK"
            ser.write(checkIfGPS.encode())
            response = ser.readline()
            print(response)
            if(response == b'AT!GXBREAK'): #is connected
                print("GPS detected on :" + str(port))
                self.statusUpdater(statusIndex,"READY")
            if(response == b''):
                self.statusUpdater(statusIndex,"NOT CONNECTED")
            if(response == b'\x00\x00'): #if interupted while waiting we need to skip
                self.statusUpdater(statusIndex,"WAITING FOR GPS")
            
                
        #--------------------------------------------------------
        #-----------------is the unit ready for upload?----------
        if(self.status[statusIndex] == "READY"):
            ser.write(self.message.encode()) 
            #check if the commands actually got written
            while True: #read responses until its finishd
                response =  ser.readline()
                print(response)

                if(response == b'AT!GXAPP SETPARAM UART_BAUD=3; AT!GXAPP SETPARAM UART_FUNCTION=15;\n'):
                    print("Standard Script sent on: " + str(port))
                    self.statusUpdater(statusIndex,"DOWNLOADING")
                    break
                if(response == b'AT!GXAPP GETFILE VIAFTP 64.87.28.100 FILENAME G604_08_02kX_KEYCRC_757E.gxe OTAP;'):
                    print("Upgrade Script sent on: " + str(port))
                    self.statusUpdater(statusIndex,"DOWNLOADING")
                    break
                   
        #------------------------------------------------------------
        #----------------send poll to see if download finished-------
        if(self.status[statusIndex] == "DOWNLOADING"):
            
            try:
                ser.baudrate = 115200
            except Exception:
                print("Couldnt Open port at 115200 baud")
            
            try:
                ser.baudrate = 9600
            except Exception:
                print("Couldnt Open port at 9600 baud")
                
            print("Sending BREAK to check if download finished")
            checkIfGPS = "AT!GXBREAK"
            ser.write(checkIfGPS.encode())
            response = ser.readline()
            print("the response to AT!BREAK is: " + str(response))
            if(response == b''): #Means GPS is not on 9600 baud yet.
                self.statusUpdater(statusIndex,"DOWNLOADING")
            if(response == b'AT!GXBREAK'): #means GPS accepts inputs again
                self.statusUpdater(statusIndex,"WAITING FOR GPS")
        #--------------When finished we need to check for disconects--------------
        #The GPS should be on 9600 while we send on 9600
        if(self.status[statusIndex] == "WAITING FOR GPS"):
            try:
                ser.baudrate = 9600
            except Exception:
                print("Couldnt Open port at 9600 baud")
               
            poll = "AT!GXAPP POLL"
            ser.write(poll.encode())
            response =  ser.read(2000)
            print("the response to AT!POLL is: " + str(response))

            #Keep spamming the unit with POLL until it provides GPS coordinates
            GPScoordinates = re.search('LL:(.+?),', str(response))
            if GPScoordinates: #resonds to poll
                GotGPS = GPScoordinates.group(1)
                if(float(GotGPS) > 0): #GPS coordinates aquired.
                    print("Remove this UNIT: " + str(port))
                    self.statusUpdater(statusIndex,"READY TO REMOVE")
            else: #doesnt respond to the poll so we keep waiting
                print("Unit waiting for GPS: " + str(port))
                self.statusUpdater(statusIndex,"WAITING FOR GPS")

        #The GPS should be fully programmed and ready to be removed
        if(self.status[statusIndex] == "READY TO REMOVE"):
            try:
                ser.baudrate = 9600
            except Exception:
                print("Couldnt Open port at 9600 baud")
            poll = "AT!GXAPP POLL"
            ser.write(poll.encode())
            response =  ser.readline()
            
            if(response != b''):#if the GPS answers then its ready to be removed but still connected
                print("Remove this unit: " + str(port))
                self.statusUpdater(statusIndex,"READY TO REMOVE")
                    
            if(response == b''): #if the GPS doenst answer its not connected
                print("Completed unit has been unplugged: " + str(port))
                self.statusUpdater(statusIndex,"NOT CONNECTED")
                  
#Python Main method
if __name__ == "__main__":
    root = Tk()
    root.title("FieldLogix GPS Updater")
    root.geometry("250x250")
    Label(root, text="PORT NUMBER: ").grid(row=0,column=0)
    Label(root, text="STATUS: ").grid(row=0,column=1)
    
    myUpdater = GPSUpdater()
    
    #Select Source
    myUpdater.selectSource()
    #Scan available com ports
    myUpdater.scanPorts()
    #check unit status THIS REPEATS FORVEVER
    while(True): 
        myUpdater.findUnits()
        root.update()
        time.sleep(1)

    

 
