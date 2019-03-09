FieldLogix GPS AutoScripter:
Designed to upload a given script file and test for GPS connectivity.


General Usage:
Run the program
select a script file for upload
script will be sent on all available ports
to change script close the progam and run it again.


Design decisions:
__init__():
Create a status array used later console output (useful for debugging).
Create a GUIstatus array used to track status of labels found in the Gui.

statusUpdater(statusIndex,message):
Function used for the repetative task of updating the status label found in the GUI.
It first attempts to change the current value found in GUIstatus but falls back
to inserting the value if it doesnt already exist.

selectSource():
Upon program start the user will be prompted to select a script file.
The file will be opened and read into memory to later be written to attached devices.
Prints to console if success or failure.

scanPorts():
gets a list of all attached serial com ports.
if the list is not empty it will print labels onto the GUI with an associated status label.
the status label retrieves its value from the stored value in the GUIstatus array.

findUnits():
This function is called to ensure that all attached ports are processed.
Creates a loop for all attached ports and invokes the handleUnit() function on each port.

handleUnit(port,statusIndex):
The main workhorse of the progam. This function is called on every port.

First it trys to read status arrays for current status.
If there is no status it defaults to NOT CONNECTED.

Opens the port on 115200 Baudrate. (The expected baudrate for a factory new unit).

when NOT CONNECTED the function sends AT!GXBREAK on current port and looks for the unit to echo back AT!GXBREAK.
if the unit echos back we send the script and the unit is now DOWNLOADING
if the unit doesnt respond it is assumed to be NOT CONNECTED.

While DOWNLOADING the function sets the baudrate to 9600 (the expected baudrate for a fully scripted device).
Now we send AT!GXBREAK, if the GPS echos back then it is confirmoed to be on 9600 baudrate and finished DOWNLOADING.
The state can change to WAITING FOR GPS

while WAITING FOR GPS we send AT!GXAPP POLL. It should respond with a valid GPS value.
otherwise we continue WAITING FOR GPS.
If we get valid GPS the state changes to READY TO REMOVE.

While READY TO REMOVE we continue to send AT!GXAPP POLL. If the unit responds its still connected so the state doesnt change.
Once the unit stops responding we declare it to be NOT CONNECTED. 
Now this port is ready for a new unit to be plugged to restart the entire process.
