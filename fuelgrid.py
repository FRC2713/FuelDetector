import time
import fuelcluster
import ntcore
import ntinit

inst = ntinit.getNT("clusterClient")
time.sleep(1) # Make a delay long enough to read

fuelTable = inst.getTable("fuelDetector")
fuelValues = fuelTable.getStringTopic("fuelData").subscribe("")
fuelHeading= fuelTable.getDoubleTopic("clusterHeading").publish()
totalFuel = fuelTable.getIntegerTopic("totalFuel").publish()

class FuelGrid: 
    fuel_chance_threshold: float = 0.75
    fuel_density_threshold: int = 1
    image_width: int = 640
    image_height: int = 480

    def __init__(self, width: int, height: int, FOV: float):
        self.grid_width: int = width - 1
        self.grid_height: int = height - 1
        self.total_fuel: int = 0
        self.FOV: float = FOV
        self.grid: list[list[int]] = []
        for w in range(width):
            self.grid.append([])
            for h in range(height):
                self.grid[w].append(0)
        self.cluster_grid: list[list[fuelcluster.FuelCluster]] = []
        for w in range(width):
            self.cluster_grid.append([])
            for h in range(height):
                self.cluster_grid[w].append(None)
    
    def add_fuel(self, fuelString: str):
        if(not(len(fuelString) == 0)):
            fuelParams = fuelString.split(",")
            if(float(fuelParams[4]) > FuelGrid.fuel_chance_threshold):
                x = round(float(fuelParams[0]) / (FuelGrid.image_width / (self.grid_width)))
                y = round(float(fuelParams[1]) / (FuelGrid.image_height / (self.grid_height)))
                #print("(" + fuelParams[0] + ", " + fuelParams[1] + ")" + " (" + str(x) + ", " + str(y) + ")")

                #top_y = round((float(fuelParams[1]) - (float(fuelParams[3]) / 2)) / (FuelGrid.image_height / (self.grid_height)))
                #bottom_y = round((float(fuelParams[1]) + (float(fuelParams[3]) / 2)) / (FuelGrid.image_height / (self.grid_height)))
                #right_x = round((float(fuelParams[0]) + (float(fuelParams[2]) / 2)) / (FuelGrid.image_width / (self.grid_width)))
                #left_x = round((float(fuelParams[0]) - (float(fuelParams[2]) / 2)) / (FuelGrid.image_width / (self.grid_width)))

                self.grid[x][y] += 1
                self.total_fuel += 1

                #print(not(right_x == x))
                #if(not(right_x == x)):
                    #self.grid[right_x][y] += 1
                #if(not(left_x == x)):
                    #self.grid[left_x][y] += 1
                #if(not(top_y == y)):
                    #self.grid[x][top_y] += 1
                #if(not(bottom_y == y)):
                    #self.grid[x][bottom_y] += 1
    
    def split_fuel_string(self, string: str):
        string_list = string.split(";")
        for fuel in string_list:
            self.add_fuel(fuel)
    def find_clusters(self):
        clusters: list[fuelcluster.FuelCluster] = []
        width: int = self.grid_width
        height: int = self.grid_height
        for w in range(width + 1):
            for h in range(height + 1):
                square: int = self.grid[w][h]
                #print(str(self.grid[w][h]) + " fuels, at (" + str(w) + ", " + str(h) + ")")
                cluster: fuelcluster.FuelCluster = self.cluster_grid[w][h]
                if ((square >= FuelGrid.fuel_density_threshold) and not(cluster is None)):
                    if ((w + 1 < width) and not(self.cluster_grid[w + 1][h] is None)):
                        self.cluster_grid[w + 1][h] = cluster.add_grid_cell(w + 1, h, square)
                    elif ((w - 1 >= 0) and not(self.cluster_grid[w - 1][h] is None)):
                        self.cluster_grid[w - 1][h] = cluster.add_grid_cell(w - 1, h, square)
                    elif ((h + 1 < height) and not(self.cluster_grid[w][h + 1] is None)):
                        self.cluster_grid[w][h + 1] = cluster.add_grid_cell(w, h + 1, square)
                    elif ((h - 1 < height) and not(self.cluster_grid[w][h - 1] is None)):
                        self.cluster_grid[w][h - 1] = cluster.add_grid_cell(w, h - 1, square)
                    else:
                        print("ATTENTION: This statement is supposed to be unreachable.")
                else:
                    c: fuelcluster.FuelCluster = fuelcluster.FuelCluster()
                    c.add_grid_cell(w, h, square)
                    self.cluster_grid[w][h] = c
                    clusters.append(c)
        return clusters
    def largest_cluster(self, clusters: list[fuelcluster.FuelCluster]):
        largest = fuelcluster.FuelCluster()
        for cluster in clusters:
            if (cluster.fuel_count > largest.fuel_count):
                largest = cluster
        #print(largest.fuel_count)
        return largest
    def get_heading(self, cluster: fuelcluster.FuelCluster):
        #print(cluster.fuel_count)
        if (cluster.fuel_count > 0):
            cluster.avg_x

            avgX = (cluster.avg_x * (FuelGrid.image_width / self.grid_width + 1)) - (FuelGrid.image_width / 2)
            degreesPerPixel: float = self.FOV / FuelGrid.image_width
            #print(str(avgX) + ", " + str(cluster.avg_x))
            return -(avgX * degreesPerPixel)
        else:
            return 0 #Defualt value- assume that the nearest fuel cluster is directly in front of the robot

    def purge_grid(self):
        #Reset all grid values to defaults; should be called at the end or begining of every frame to avoid fuel that was previously there from influenciong current calculations
        self.grid = []
        for w in range(self.grid_width + 1):
            self.grid.append([])
            for h in range(self.grid_height + 1):
                self.grid[w].append(0)
        self.cluster_grid = []
        for w in range(self.grid_width + 1):
            self.cluster_grid.append([])
            for h in range(self.grid_height + 1):
                self.cluster_grid[w].append(None)
        self.total_fuel = 0


grid = FuelGrid(12, 12, 71)
print("Program started")
while True:
    values = fuelValues.get()
    #print(values)
    
    grid.split_fuel_string(values)
    #print(grid.total_fuel)
    clusters = grid.find_clusters()
    large = grid.largest_cluster(clusters)
    #print(large.fuel_count)
    heading: float = grid.get_heading(large)
    #print(heading)
    fuelHeading.set(heading)
    totalFuel.set(grid.total_fuel)
    grid.purge_grid()
