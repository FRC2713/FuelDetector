nst = ntinit.getNT("clusterClient")
time.sleep(1) # Make a delay long enough to read

fuelTable = inst.getTable("fuelDetector")
fuelValues = fuelTable.getStringTopic("fuelData").subscribe("")
fuelHeading= fuelTable.getDoubleTopic("clusterHeading").publish()
totalFuel = fuelTable.getIntegerTopic("totalFuel").publish()
