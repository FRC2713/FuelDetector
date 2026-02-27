class FuelCluster:
    def add_grid_cell(self, cell_x: int, cell_y: int, cell_fuel_count: int):
        FuelCluster.update_fuel_count(self, cell_fuel_count)
        weighted_cell = cell_fuel_count / self.fuel_count
        weighted_cluster = self.fuel_count - cell_fuel_count / self.fuel_count
        if(self.avg_x is None):
            self.avg_x = ((self.avg_x * weighted_cluster) + (cell_x * weighted_cell)) / 2
        else:
            self.avg_x = cell_x
        if(self.avg_y is None):
            self.avg_y = ((self.avg_y * weighted_cluster) + (cell_y * weighted_cell)) / 2
        else:
            self.avg_y = cell_y

    def update_fuel_count(self, fuels: int):
        # This should never be called outside this class. It will not adjust the average position of the cluster, leading to a potentially incorrect heading
        if(self.fuel_count is None):
            self.fuel_count = fuels
        else:
            self.fuel_count += fuels