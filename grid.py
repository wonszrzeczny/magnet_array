import numpy as np
import itertools
import matplotlib.pyplot as plt
import copy

def load_Rays_data():
    vals = np.stack([np.load("magnet" + str(i)+ ".npy") for i in range(1,5)], axis=0)
    return vals

class Cell:
    def __init__(self, d, n, coords = None ):
        self.d = d
        self.n = n
        if coords is None: coords= np.random.randint(0,n, size=d)
        self.coords = coords % n

    def next_cell(self, delta):
        return Cell(self.d, self.n, coords = self.coords + delta)

    def neighbours(self):
        return [self.next_cell(np.array(delta)) for delta in itertools.product([-1,0,1], repeat=self.d) ]

    def __eq__(self, other):
        return self.coords == other.coords

    def __str__(self):
        return str(self.coords)

class Grid:
    def __init__(self, vals):
        self.vals = vals
        self.d, self.n = np.shape(vals)[0:2]
        self.B_0 = self.vals[0, 0]
        self.dB = vals - self.B_0
        print(np.max(self.dB))
        print(self.B_0)

    def B(self, cell):
        b = copy.deepcopy(self.B_0)
        for i in range(self.d):
            b+= self.dB[i, cell.coords[i]]
        return b

    def cost(self, cell):
        return np.sum((self.target - self.B(cell)[:self.d])**2)

    def next_cell(self, cell):
        possibilities = cell.neighbours()
        cell = min(possibilities, key = self.cost)
        return cell

    def starting_sample(self, n, epoch=500):   #just picking best starting points by randomly sampling
        starting_cells = [Cell(self.d, self.n) for _ in range(n)]
        for _ in range(epoch):
            new_cells = [self.next_cell(cell) for cell in starting_cells]
            starting_cells = copy.deepcopy(new_cells)
        return starting_cells

    def find_paths(self, n, trajectory):
        self.target = trajectory[0]
        start = self.starting_sample(n)
        routes = [[(a, self.cost(a))] for a in start]
        for elem in trajectory[1:]:
            self.target = elem
            for route in routes:
                cell_to_append = self.next_cell(route[-1][0])
                route.append((cell_to_append, route[-1][1]+self.cost(cell_to_append)))
        return routes

def gen_data(d, n):
    x = np.linspace(0, 6.28, n)
    vals = np.random.rand(d,2,6)*20
    d = np.arange(1,7)
    phase = np.einsum("i,j->ji",x,d)
    sins = np.sin(phase)
    return np.einsum("ji,mdj->mid", sins, vals)

#plt.plot(gen_data(4,1000))
vals=gen_data(4,1000)
print(vals.shape)
target = np.stack([np.linspace(0,20, 1000),np.zeros(1000)], axis=1)
plt.plot(load_Rays_data()[3,:,2])
plt.show()
#grid = Grid(vals)
#path = grid.find_paths(1, target)[0]
#plt.plot(np.array([grid.B(cell[0]) for cell in path]))
#plt.show()
#print(grid.B(path[0][0]))

