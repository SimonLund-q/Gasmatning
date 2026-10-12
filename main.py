import nidaqmx
import time

device_write_range = "Dev1/port0/line0:7"
device_read_pin = "Dev1/port1/line0"
bit_data = 0b00000000

max_val = 255
min_val = 0
settle_time = 0.001


def read_state(num):
    data = bin(int(num))
    write_task.write(data)
    time.sleep(settle_time)
    return read_task.read()


def find_state(high, low):
    global min_val, max_val

    high_state = read_state(high)
    low_state = read_state(low)

    if high_state and not low_state:
        num = int((low + high) // 2)
        print(f"Current Voltage: {5 * num / 256}")

    if low_state:
        min_val = low - 1
    if high_state:
        max_val = high - 1

    if not low_state:
        min_val = low + 1
    if not high_state:
        max_val = high + 1


with nidaqmx.Task() as write_task, nidaqmx.Task() as read_task:
    write_task.do_channels.add_do_chan(device_write_range)
    read_task.di_channels.add_di_chan(device_read_pin)

    write_task.start()
    read_task.start()

while True:
    find_state(max_val, min_val)
