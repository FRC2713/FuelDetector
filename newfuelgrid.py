import time
import ntinit
import MultilayerGrid

nst = ntinit.getNT("clusterClient")
time.sleep(1) # Make a delay long enough to read

fuelTable = inst.getTable("fuelDetector")
fuelValues = fuelTable.getStringTopic("fuelData").subscribe("")
fuelHeading= fuelTable.getDoubleTopic("clusterHeading").publish()
totalFuel = fuelTable.getIntegerTopic("totalFuel").publish()

class FuelClustering:
  fuel_chance_threshold: float = 0.70 #Minimum confidence for fuel to be considered
  def __init__(self, imgWidth: int, imgHeight: int, FOV: float, grid: MultilayerGrid):
    self.imageWidth: int = imgWidth;
    self.imageHeight: int = imgHeight;
    self.FOV: float = FOV;
    

print("Program started")
