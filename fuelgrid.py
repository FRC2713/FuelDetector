import fuelcluster

class FuelGrid: 
    fuel_chance_threshold: float = 80.0
    fuel_density_threshold: int = 1
    image_width: int = 640
    image_height: int = 480

    def __init__(self, width: int, height: int):
        self.grid_width: int = width - 1
        self.grid_height: int = height - 1
        self.grid = list[list[int]]
        self.cluster_grid = list[list[fuelcluster.FuelCluster]]
    
    def add_fuel(self, fuelString: str):
        fuelParams = fuelString.split(",")
        if(fuelParams[4] > FuelGrid.fuel_chance_threshold):
            self.grid[round(fuelParams[0] / (FuelGrid.image_width / self.grid_width))][round(fuelParams[1] / (FuelGrid.image_height / self.grid_height))] += 1
    
    def split_fuel_string(self, string: str):
        string_list = string.split(";")
        for fuel in string_list:
            FuelGrid.addFuel(self, fuel)
    def find_clusters(self):
        clusters: list[fuelcluster.FuelCluster] = []
        width: int = self.grid_width
        height: int = self.grid_height
        for w in width:
            for h in height:
                square: int = self.grid[w][h]
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
                    c.add_grid_cell(square)
                    self.cluster_grid[w][h] = c