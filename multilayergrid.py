class SinglelayerGrid:
  def __init__(self, cellsX: int, cellsY: int):
    self.cellsX: int = cellsX
    self.cellsY: int = cellsY
    self.cells = []
    for w in range(cellsX):
      self.cells.push([])
      for h in range(celsY):
        self.cells[w].push(None)
  def addToGrid(self, x: int, y: int, value):
    self.cells[x][y] = value


class MultilayerGrid:
  def __init__(self):
    self.grids = SinglelayerGrid(1, 1)
    self.totalDepth = 1

  def addGrid(self, gridCellsX: int, gridCellsY: int, gridDepthCoords: []):
    #Constructs a new gird layer at location gridDepthCoords with the number of cells provided in the X and Y directions
    #gridDepthCoords is an array of arrays of type [x: int, y: int]. This is a path that tells this functon how to traverse the grid tree; it will start at the "top" grid and work "down". The coordinate pairs tell the function which grid cell to go into next. This is required even if only one grid cell exists to choose from. This does not attempt to check if a cell exists before "entering" it.
    grid = SinglelayerGrid(gridCellsX, gridCellsY)
    
    for c in gridDepthCoords:
      
