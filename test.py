from libhackrf import HackRF
from time import sleep
import numpy as np
import math


hackrf = HackRF()

hackrf.sample_rate = 20e6
hackrf.center_freq = 433.2e6
hackrf.amplifier_on = False


def pipe(data: bytes) -> bool:
    a = np.array(data).astype(np.int8).astype(np.float64).view(np.complex128)
    strength = np.sum(np.absolute(a)) / len(a)
    dbfs = 20 * math.log10(strength)
    print(f"{ dbfs }")
    return False


hackrf.start_rx(pipe_function=pipe)
sleep(1)
hackrf.stop_rx()


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
        (120, 200),
        (500, 700),
    ],
    pipe_function=pipe,
)
"""

"""
Get serial number

sn = hackrf.get_serial_no()
print(sn)
"""
