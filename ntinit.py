import time
import ntcore

def getNT(clientName: str):
    ntconf = "ntconfig.txt"
    robotIP = ntconf.readline()
    localIP = ntconf.readline()
    ntconf.close()
    print("Scanning for NetworkTables...")
    time.sleep(1)
    inst = ntcore.NetworkTableInstance.getDefault()
    inst.startClient4(clientName)
    inst.setServer(robotIP)
    robotConnected = inst.getTable("fuelDetector").getBooleanTopic("robotConnected").subscribe(False)
    time.sleep(0.1)
    connected = robotConnected.get()
    time.sleep(0.1)
    time.sleep(0.1) # Don't ask. I don't know.
    connected = robotConnected.get()
    print("robot connection found? " + str(connected))
    if(not(connected)):
        inst.setServer(localIP)
        time.sleep(0.1)
        time.sleep(0.1)
        connected = robotConnected.get()
        print()
        print("local connection found? " + str(connected))
        if(connected):
            print("Server found at " + localIP + " (local)")
            return inst
        else:
            print("No NetworkTables server detected. Check IP addresses.")
            return inst
    else:
        print("Server found at " + robotIP + " (robot)")
        return inst

def testNT(): 
    #Test code
    print("Testing NT servers")
    inst = getNT("NTTest")
    time.sleep(10)
