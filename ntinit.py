import time
import ntcore

def getNT(clientName: str, ignore: bool):
    ntconf = open("ntconfig.txt")
    retryTime = float(ntconf.readline())
    print("Wait time: " + str(retryTime) + " seconds")
    robotIP = str(ntconf.readline())
    print("robot address: " + robotIP)
    localIP = str(ntconf.readline())
    print("local address: " + localIP)
    ntconf.close()


    time.sleep(1)
    i = 0
    startTime = time.time()
    while((time.time() - startTime) < retryTime):
        print("Scanning for NetworkTables... try number " + str(i + 1))
        time.sleep(1)
        inst = ntcore.NetworkTableInstance.getDefault()
        inst.startClient4(clientName)
        inst.setServer(robotIP)
        if(ignore): 
            print("Ignore flag set. Returning RobotIP NT server, may not be connected")
            return inst
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
            time.sleep(0.1)
            connected = robotConnected.get()
            print()
            print("local connection found? " + str(connected))
            if(connected):
                print("Server found at " + localIP + " (local)")
                return inst
        else:
            print("Server found at " + robotIP + " (robot)")
            return inst
        i += 1
    print("No NetworkTables server detected. Check IP addresses.")
    return inst

def testNT(): 
    #Test code
    print("Testing NT servers")
    inst = getNT("NTTest")
    time.sleep(10)
