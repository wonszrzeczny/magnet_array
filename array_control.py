import serial
import time
import numpy as np
import matplotlib.pyplot as plt

import numpy as np
import itertools
import matplotlib.pyplot as plt
import copy

def load_data():
    vals = np.stack([np.load("magnet" + str(i)+ ".npy") for i in range(0,3)], axis=0)
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
            b += self.dB[i, cell.coords[i]]
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

def path_to_commands(path):
    start = path[0].coords.tolist()
    res = [[0,0,0]]*len(path)
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

        #magnetic sensor configuration
        self.sensor_serial = serial.Serial()
        self.sensor_serial.baudrate = 9600
        self.sensor_serial.port = 'COM5'
        self.sensor_serial.open()
        time.sleep(5)

        #fine graining, chamge as needed, currently motor is in x16 mode, max_step should be divisible by seg length
        self.max_step = 18000 * 16
        self.pos = [0, 0, 0]
        self.segment = 1000

    def get_pos(self):
        self.arduino_serial.write(b"pos")
        s = self.arduino_serial.readline().decode("utf-8").rstrip().strip()
        vals = [int(k) for k in s.split()]
        return vals

    def move(self, offset):
        command = "move " + " ".join(map(str, offset))
        print(str.encode(command))
        self.arduino_serial.write(str.encode(command))

    def turn_on(self):
        self.arduino_serial.write(b'on')

    def turn_off(self):
        self.arduino_serial.write(b'off')

    def read_field(self, samples = 1):
        vals = [0.0, 0.0, 0.0]
        for i in range(samples):
            self.sensor_serial.write(b'm')
            time.sleep(0.1)
            s = self.sensor_serial.readline().decode("utf-8").rstrip().strip()
            vals = [vals[i] + float(k)/samples for i,k in enumerate(s.split())]
        print(vals)
        return vals

    def sweep_axis(self, axis):
        res = np.zeros((self.max_step//self.segment, 3), dtype = float)
        offset = [0] * 3
        offset[axis] = self.segment
        for i in range(res.shape[0]):
            self.move(offset)
            res[i] = np.array(self.read_field(15))
        return res

    def calibrate(self):
        for i in range(0,3):
            res = self.sweep_axis(i)
            np.save("magnet" + str(i), res)

    def construct_grid(self):
        self.calibrate()
        vals = load_data()
        self.grid = Grid(vals)

    def trace_path(self, path):
        self.move([-x for x in self.get_pos()])
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
    def trace_field(self, target):
        paths = self.grid.find_paths(100, target)
        best_path = [x[0] for x in min(paths, key=lambda x: x[-1][1])]
        self.prediction = np.array([self.grid.B(cell) for cell in best_path])
        commands = path_to_commands(best_path)
        res = b.trace_path(commands)
        return res


b = array()
b.construct_grid() #calibration step, if you have data get rid of calibrate in the function, it takes a lot of time
target = np.stack([np.linspace(0,20, 300),np.zeros(300),np.zeros(300)], axis=1)
result = b.trace_field(target)



