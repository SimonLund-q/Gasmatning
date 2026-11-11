import nidaqmx
import time
import csv
import os
import tempfile
import matplotlib.pyplot as plt

from datetime import datetime
from matplotlib.animation import FuncAnimation
from collections import deque

DEVICE_READ_PIN = "Dev1/ai0"

SAMPLE_INTERVAL = 100  # Milliseconds
MAX_SAMPLES = 200
SMOOTHING_WINDOW = 10

# Graph data
times = deque(maxlen=MAX_SAMPLES)
raw_values = deque(maxlen=MAX_SAMPLES)
smooth_values = deque(maxlen=MAX_SAMPLES)
derivatives = deque(maxlen=MAX_SAMPLES)

# Moving average buffer
recent_values = deque(maxlen=SMOOTHING_WINDOW)


# File settings
FILE_NAME = r"C:\Users\simon\PycharmProjects\ALT_Gasmatning\daq_readings.txt"

SAVE_DURATION = 30 * 60
CLEANUP_INTERVAL = 60

recorded_data = deque()
last_cleanup = time.monotonic()

CSV_HEADER = [
    "Timestamp",
    "Time (s)",
    "Raw Voltage (V)",
    "Smoothed Voltage (V)",
    "Derivative (V/s)"
]

# Clear the file when the program starts
with open(FILE_NAME, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(CSV_HEADER)

print(f"Saving measurements to: {FILE_NAME}")


def save_data(row):
    global last_cleanup

    recorded_data.append(row)

    # Append the newest measurement immediately
    with open(FILE_NAME, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(row)

    # Remove old measurements from memory
    current_time = row[1]
    cutoff = current_time - SAVE_DURATION

    while recorded_data and recorded_data[0][1] < cutoff:
        recorded_data.popleft()

    # Rewrite file once per minute
    now = time.monotonic()

    if now - last_cleanup >= CLEANUP_INTERVAL:
        try:
            with open(FILE_NAME, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(CSV_HEADER)
                writer.writerows(recorded_data)

            last_cleanup = now
            print("Recording file cleaned successfully.")

        except PermissionError as error:
            print(f"Could not clean recording file: {error}")


# Create figure
fig = plt.figure(figsize=(14, 8))
fig.suptitle("NI USB-6009 Analog Voltage Monitor")

gs = fig.add_gridspec(2, 2)

ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[1, :])

# Raw voltage
line1, = ax1.plot([], [], color="blue", label="Raw Voltage")
ax1.set_title("Raw Analog Voltage")
ax1.set_ylabel("Voltage (V)")
ax1.set_xlabel("Time (s)")
ax1.grid(True)
ax1.legend()

# Smoothed voltage
line2, = ax2.plot([], [], color="green", label="Smoothed Voltage")
ax2.set_title("Smoothed Voltage (10 Samples)")
ax2.set_ylabel("Voltage (V)")
ax2.set_xlabel("Time (s)")
ax2.grid(True)
ax2.legend()

# Derivative
line3, = ax3.plot([], [], color="red", label="Derivative")
ax3.set_title("Derivative of Smoothed Voltage")
ax3.set_ylabel("dV/dt (V/s)")
ax3.set_xlabel("Time (s)")
ax3.grid(True)
ax3.legend()

fig.tight_layout(rect=[0, 0, 1, 0.95])

start_time = time.perf_counter()

# Initialize DAQ
read_task = nidaqmx.Task()

read_task.ai_channels.add_ai_voltage_chan(
    DEVICE_READ_PIN,
    min_val=-10.0,
    max_val=10.0
)

read_task.start()


def update(frame):
    current_time = time.perf_counter()
    elapsed_time = current_time - start_time

    # Read analog voltage
    voltage = read_task.read()

    # Store raw data
    times.append(elapsed_time)
    raw_values.append(voltage)

    # Calculate moving average
    recent_values.append(voltage)
    smooth_voltage = sum(recent_values) / len(recent_values)

    smooth_values.append(smooth_voltage)

    # Calculate derivative
    if len(smooth_values) > 1:
        dt = times[-1] - times[-2]

        if dt > 0:
            derivative = (
                smooth_values[-1] - smooth_values[-2]
            ) / dt
        else:
            derivative = 0
    else:
        derivative = 0

    derivatives.append(derivative)

    # Record measurement
    timestamp = datetime.now().isoformat(
        sep=" ", timespec="milliseconds"
    )

    save_data([
        timestamp,
        elapsed_time,
        voltage,
        smooth_voltage,
        derivative
    ])

    # Update graphs
    line1.set_data(list(times), list(raw_values))
    line2.set_data(list(times), list(smooth_values))
    line3.set_data(list(times), list(derivatives))

    # Show latest 20 seconds
    xmin = max(0, elapsed_time - 20)
    xmax = max(20, elapsed_time)

    for ax in (ax1, ax2, ax3):
        ax.set_xlim(xmin, xmax)
        ax.relim()
        ax.autoscale_view(scalex=False, scaley=True)


    return line1, line2, line3


ani = FuncAnimation(
    fig,
    update,
    interval=SAMPLE_INTERVAL,
    blit=False,
    cache_frame_data=False
)

try:
    plt.show(block=True)

finally:
    read_task.close()
    plt.close(fig)
    print("DAQ task closed.")
