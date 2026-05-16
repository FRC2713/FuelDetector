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
  def getCell(self, x: int, y: int):
    return self.cells[x][y]

class MultilayerGrid:
  def __init__(self):
    self.grids = SinglelayerGrid(1, 1)
    self.totalDepth = 1

  def addGrid(self, gridCellsX: int, gridCellsY: int, gridDepthCoords: list[list[int, int]], finalCoords: list[int, int]):
    #Constructs a new gird layer at location gridDepthCoords with the number of cells provided in the X and Y directions
    #gridDepthCoords is a path that tells this functon how to traverse the grid tree; it will start at the "top" grid and work "down". The coordinate pairs tell the function which grid cell to go into next. This is required even if only one grid cell exists to choose from. This does not attempt to check if a cell exists before "entering" it.
    #finalCoords is the coordinates of which cell to add the grid to; do not include this in gridDepthCoords.
    grid = SinglelayerGrid(gridCellsX, gridCellsY)
    
    currentGrid = self.grids
    for c in gridDepthCoords:
      currentGrid = currentGrid.getCell(c[0], c[1])
    currentGrid.addToGrid(finalCoords[0], finalCoords[1], grid)
