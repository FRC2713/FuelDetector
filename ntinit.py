import ntcore

def getNT(clientName: str):
    inst = ntcore.NetworkTableInstance.getDefault()
    inst.startClient4(clientName)
    inst.setServer("10.27.13.2", 5810)
    robotConnected = inst.getTable("fuelDetector").getBooleanTopic("robotConnected").subscribe(False)
    if(not(robotConnected.get())):
        inst.setServer("127.0.0.1")
        if(robotConnected.get()):
            return inst
        else:
            print("No NetworkTables server detected. Check IP addresses.")
    else:
        return inst