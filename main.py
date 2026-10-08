import nidaqmx

with nidaqmx.Task() as task:
    ##task.ai_channels.add_ai_voltage_chan(
    ##    "Dev1/ai0",
    ##    min_val=0.0,
    ##    max_val=5.0
    ##)
    task.di_channels.add_di_chan(
        "Dev1/port0/line0",
    )


    while True:
        value = task.read()
        print(f"{value}")
        ## False -0.3v - 0.8v
        ## True 2.0v - 5.8v