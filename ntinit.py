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
    connected = robotConnected.get()
    time.sleep(0.1)
    time.sleep(0.1) # Don't ask. I don't know.
    connected = robotConnected.get()
    print(connected)
    if(not(connected)):
        inst.setServer("127.0.0.1")
        time.sleep(0.1)
        time.sleep(0.1)
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