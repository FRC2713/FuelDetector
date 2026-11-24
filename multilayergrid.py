class SubgridParams:
  def __init__(depth, div_x, div_y):
    self.div_x = div_x
    self.div_y = div_y
    self.subgrids = []

    for x in range(div_x):
      self.subgrids.append([])
      for y in range(div_y):
        self.subgrids.append(0)
    # print(self.subgrids); # Uncomment for debug
  
  def addGrid(x, y, subgrid):
    self.subgrids[x][y] = subgrid;
  def getParams(x, y):
    return self.subgrids[x][y]

class MultilayerGrid:
  # depth: how deep the grid is in the grid tree
  # div_x: how many times the grid should be divided horizontally (1 results in no division; values less than 1 are rounded up to 1)
  # div_y: how many times the grid should be divided vertically (1 results in no division; values less than 1 are rounded up to 1)
  # subgrid_params is a special object that defines the parameters for the MultilayerGrid objects that will be creaded as children of this one. Think of it as defining the shape of the tree.
  def __init__(depth, div_x, div_y, subgrid_params):
    self.depth = depth
    self.div_x = div_x
    self.div_y = div_y
    self.total_subgrids = div_x * div_y
    self.subgrid_params = subgrid_params
    self.subgrids = []
    self.OOI = [] # Objects of Intrest (aka fuel). See OOI class.
    
    for x in range(div_x):
      subgrids.append([])
      for y in range(div_y):
        params = self.subgrid_params.getParams(x, y)
        subgrids[x].append(MultilayerGrid(self.depth + 1, params.div_x, params.div_y, params.subgrids))
  def getTotalOOI():
    return len(self.OOI)
