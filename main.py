import nidaqmx
device_write_range = "Dev1/port0/line0:7"
device_read_pin = "Dev1/port1/line0"

with nidaqmx.Task() as write_task, nidaqmx.Task() as read_task:
    write_task.do_channels.add_do_chan(device_write_range)
    read_task.di_channels.add_di_chan(device_read_pin)

    write_task.start()
    read_task.start()

    bit_data = 0b00000000
    write_task.write(bit_data)

    while True:
        state = read_task.read()
        print(f"Input state: {int(state)}")