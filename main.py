import nidaqmx
import time
import numpy as np
import matplotlib.pyplot as plt
from collections import deque

DEVICE_READ_PIN = "Dev1/port1/line0"

SAMPLE_INTERVAL = 0.1  # Seconds
MAX_SAMPLES = 200      # Display the latest 200 samples

# Store measurements
times = deque(maxlen=MAX_SAMPLES)
values = deque(maxlen=MAX_SAMPLES)
derivatives = deque(maxlen=MAX_SAMPLES)

# Create graph window
plt.ion()

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7))
fig.suptitle("NI USB-6009 Live Data Monitor")

# Original signal
line1, = ax1.plot([], [], color="blue", label="Digital Input")
ax1.set_ylabel("Digital Value")
ax1.set_ylim(-0.2, 1.2)
ax1.set_title("Digital Input vs Time")
ax1.grid(True)
ax1.legend()

# Derivative
line2, = ax2.plot([], [], color="red", label="Derivative")
ax2.set_xlabel("Time (s)")
ax2.set_ylabel("dValue/dt (1/s)")
ax2.set_title("Derivative vs Time")
ax2.grid(True)
ax2.legend()

plt.tight_layout()
plt.show(block=False)

start_time = time.perf_counter()
last_sample_time = start_time

with nidaqmx.Task() as read_task:
    read_task.di_channels.add_di_chan(DEVICE_READ_PIN)
    read_task.start()

    try:
        while plt.fignum_exists(fig.number):
            current_time = time.perf_counter()
            elapsed_time = current_time - start_time

            # Read digital input
            value = int(read_task.read())

            # Store data
            times.append(elapsed_time)
            values.append(value)

            # Calculate derivative
            if len(values) > 1:
                dt = times[-1] - times[-2]

                if dt > 0:
                    derivative = (values[-1] - values[-2]) / dt
                else:
                    derivative = 0
            else:
                derivative = 0

            derivatives.append(derivative)

            # Update original signal
            line1.set_data(times, values)

            # Update derivative
            line2.set_data(times, derivatives)

            # Update time axis
            if len(times) > 1:
                ax1.set_xlim(times[0], times[-1] + 0.1)
                ax2.set_xlim(times[0], times[-1] + 0.1)

            # Automatically scale derivative axis
            ax2.relim()
            ax2.autoscale_view(scalex=False, scaley=True)

            # Refresh window
            fig.canvas.draw_idle()
            plt.pause(0.001)

            print(
                f"Time: {elapsed_time:.2f}s | "
                f"Value: {value} | "
                f"Derivative: {derivative:.2f}"
            )

            # Maintain sampling interval
            next_sample_time = last_sample_time + SAMPLE_INTERVAL
            sleep_time = next_sample_time - time.perf_counter()

            if sleep_time > 0:
                time.sleep(sleep_time)

            last_sample_time = time.perf_counter()

    except KeyboardInterrupt:
        print("Measurement stopped.")

plt.close(fig)