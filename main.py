import nidaqmx

with nidaqmx.Task() as task:
    task.di_channels.add_di_chan("Dev1/port0/line0")
    task.di_channels.add_di_chan("Dev1/port0/line1")

    while True:
        values = task.read()

        print(f"{values[0]}")
        print(f"{values[1]}")
