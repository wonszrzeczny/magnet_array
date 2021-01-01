import serial
import time


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
        time.sleep(1)
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
        self.sensor_serial.flush()
        for i in range(samples):
            s = self.sensor_serial.readline().decode("utf-8").rstrip().strip()
            vals = [vals[i] + float(k)/samples for i,k in enumerate(s.split())]
        print(vals)
        return vals

b = array()
b.read_field(20)
b.turn_off()