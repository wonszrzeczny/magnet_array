import serial
import time
import numpy as np
import matplotlib.pyplot as plt
import numpy as np
import itertools
import matplotlib.pyplot as plt
import copy

DOF = 3     # number of connected magnets, YOU NEED TO CHANGE ARDUINO CODE FOR COMPATIBILITY, currently 3

# by default sweep files are named magnetX.npy , change magic numbers for different names
def load_data():
    vals = np.stack([np.load("magnet" + str(i)+ ".npy") for i in range(0,DOF)], axis=0) # loading calibration files
    return vals

# here be dragons, pathfinding code

# cell is a helper class, effectively an array of magnet coords modulo max step number, comparisons and neighbours
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

# class for predicting field numbers and finding paths, if using a different model modify B function
# modify 'cost' for different loss functions, currently squared error, idk why tho
# all of the dimensions are tied to the linear model values array for convenience, if using a different model change
# the values in init

class Grid:
    def __init__(self, vals):
        self.vals = vals
        self.d, self.n = np.shape(vals)[0:2]
        self.B_0 = self.vals[0, 0]
        self.dB = vals - self.B_0 # dB[i,j,k] - change to field in kth direction when ith magnet is rotated to jth step
        print(np.max(self.dB))    # in linear model B(k, l, m,...) = B_0 + dB[0, k, :] + dB[0, l, :] + .. sum dB for all
        print(self.B_0)

    def B(self, cell):
        b = copy.deepcopy(self.B_0)
        for i in range(self.d):
            b += self.dB[i, cell.coords[i]] # linear contributions
        return b

    def cost(self, cell):
        return np.sum((self.target - self.B(cell)[:self.d])**2) # set self.target to desired field, bit messy this

    def next_cell(self, cell):  # find neighbour cell with smallest cost for given target field
        possibilities = cell.neighbours()
        cell = min(possibilities, key = self.cost)
        return cell

    def starting_sample(self, n, epoch=500):   # just picking best starting points by randomly sampling
        starting_cells = [Cell(self.d, self.n) for _ in range(n)]
        for _ in range(epoch):
            new_cells = [self.next_cell(cell) for cell in starting_cells]
            starting_cells = copy.deepcopy(new_cells)
        return starting_cells # could look for duplicates here and remove crappy local minima?

    def find_paths(self, n, trajectory):
        self.target = trajectory[0]
        start = self.starting_sample(n)
        routes = [[(a, self.cost(a))] for a in start]   # finding first points and building up on them
        for elem in trajectory[1:]:
            self.target = elem
            for route in routes:    # this is just greedily appending best coords
                cell_to_append = self.next_cell(route[-1][0])
                route.append((cell_to_append, route[-1][1]+self.cost(cell_to_append)))
        return routes


def path_to_commands(path): # convert numpy array of path coordinates to lists of moves
    start = path[0].coords.tolist()
    res = [[0]*DOF]*len(path)
    for i in range(0,len(path)-1):
        res[i+1] = (path[i+1].coords - path[i].coords).tolist()
    res[0] = start
    return res


class array:
    def __init__(self):

        # arduino configuration
        self.arduino_serial = serial.Serial()
        self.arduino_serial.baudrate = 9600
        self.arduino_serial.port = 'COM4'
        self.arduino_serial.open()
        time.sleep(5)

        # magnetic sensor configuration
        self.sensor_serial = serial.Serial()
        self.sensor_serial.baudrate = 9600
        self.sensor_serial.port = 'COM5'
        self.sensor_serial.open()
        time.sleep(5)

        # fine graining, chamge as needed, currently motor is in x16 mode, max_step should be divisible by seg length
        # keep in mind making it smaller will mean more measurements
        self.max_step = 18000 * 16
        self.pos = [0]*DOF
        self.segment = 1000

    # this is all talking with sensor/ arduino, feel free to use them in console
    def get_pos(self):
        self.arduino_serial.write(b"pos")
        s = self.arduino_serial.readline().decode("utf-8").rstrip().strip()
        vals = [int(k) for k in s.split()]
        return vals

    def move(self, offset): # offset is an array with len = DOF, this is in arduino units, not fine grained segments
        command = "move " + " ".join(map(str, offset))
        print(str.encode(command))
        self.arduino_serial.write(str.encode(command))

    def reset(self):    # go back to 0,0,0
        self.move([-x for x in self.get_pos()])
        time.sleep(10)
        print("back to start")

    def turn_on(self):
        self.arduino_serial.write(b'on')

    # that's just to stop it from melting, turns on the block pin not sure if it stops it from heating tho
    def turn_off(self):
        self.arduino_serial.write(b'off')

    # samples is how many measurements to average, more samples = longer
    def read_field(self, samples = 1):
        vals = [0.0]*DOF
        for i in range(samples):
            self.sensor_serial.write(b'm')
            time.sleep(0.1)
            s = self.sensor_serial.readline().decode("utf-8").rstrip().strip()
            vals = [vals[i] + float(k)/samples for i,k in enumerate(s.split())]
        print(vals)
        return vals

    # sweep along axis and take all segments measurements
    def sweep_axis(self, axis):
        res = np.zeros((self.max_step//self.segment, 3), dtype = float) # results for field
        offset = [0] * DOF
        offset[axis] = self.segment
        for i in range(res.shape[0]):
            self.move(offset)
            res[i] = np.array(self.read_field(15))
        return res

    # calibrate and save data for linear model (~15 minutes)
    def calibrate(self):
        for i in range(0,DOF):
            res = self.sweep_axis(i)
            np.save("magnet" + str(i), res)

    def construct_grid(self):
        self.calibrate()
        vals = load_data()
        self.grid = Grid(vals)

    def trace_path(self, path):
        self.reset()
        self.sensor_serial.flushInput()
        path = [[self.segment*val for val in elem] for elem in path]
        res = np.zeros((len(path),3), dtype = float)
        self.move(path[0])
        time.sleep(15)
        for i in range(1,len(path)):
            self.move(path[i])
            val = self.read_field(15)
            res[i] = np.array(val)
        return res

    # find best trajectory for target field and measure along the way
    def trace_field(self, target):
        paths = self.grid.find_paths(100, target)
        # saving what it came up with for inspection in the object, look it up in console
        self.best_path = [x[0] for x in min(paths, key=lambda x: x[-1][1])]
        self.prediction = np.array([self.grid.B(cell) for cell in self.best_path])
        commands = path_to_commands(self.best_path)
        self.res = b.trace_path(commands)
        return self.res

b = array()
b.construct_grid() # calibration step, if you have data get rid of calibrate() in the function, it takes a lot of time
# target format np.shape(step_number, k=3), where values are field targets at step number in k direction
target = np.stack([np.linspace(0,20, 300),np.zeros(300),np.zeros(300)], axis=1)
result = b.trace_field(target)



