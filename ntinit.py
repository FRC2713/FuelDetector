import time
import ntcore

def getNT(clientName: str):
    print("Scanning for NetworkTables...")
    time.sleep(1)
    inst = ntcore.NetworkTableInstance.getDefault()
    inst.startClient4(clientName)
    inst.setServer("10.27.13.2")
    robotConnected = inst.getTable("fuelDetector").getBooleanTopic("robotConnected").subscribe(False)
    time.sleep(0.1)
    connected = robotConnected.get() # Ty: "The fuel detection algorithm needs to run on a coprocessor. Rewrite it in Python"
    time.sleep(0.1)
    time.sleep(0.1) # Don't ask.
    connected = robotConnected.get()
    print(connected)
    if(not(connected)):
        inst.setServer("127.0.0.1")
        time.sleep(0.1)
        time.sleep(0.1) # It works. I'm a Java & JavaScript person. I'm done with this.
        connected = robotConnected.get()
        print(connected)
        if(connected):
            print("Server found at 127.0.0.1 (localhost)")
            return inst
        else:
            print("No NetworkTables server detected. Check IP addresses.")
            return inst
    else:
        print("Server found at 10.27.13.2 (robot)")
        return inst

def testNT(): 
    #Test code
    print("Testing NT servers")
    inst = getNT("NTTest")
    time.sleep(10)