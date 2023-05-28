from libhackrf import *
from time import sleep
import numpy as np
import math

hackrf = HackRF()

hackrf.sample_rate = 20e6
hackrf.center_freq = 433.2e6


"""
Reading data
----------------
"""

"""
Read 1M samples
samples = hackrf.read_samples(1e6)
print(len(samples))

"""


"""
Over 1 second, read at most 50000 samples

hackrf.sample_count_limit = 50000
hackrf.start_rx()
sleep(1)
hackrf.stop_rx()

"""


"""
Sweep and pipe data into function. Stop after one scan.

def pipe(data):
    print(data)
    return True


hackrf.start_sweep(
    [
        FrequencyBand(120, 200),
        FrequencyBand(500, 700),
    ],
    pipe_function=pipe,
)
"""

"""
Get serial number

sn = hackrf.get_serial_no()
print(sn)
"""
