from libhackrf import *
from time import sleep

hackrf = HackRF()

hackrf.sample_rate = 20e6
hackrf.center_freq = 88.5e6

sn = hackrf.get_serial_no()
print(sn)
samples = hackrf.read_samples(1e6)
print(samples)
# hackrf.rx_buffer_limit = 500000
# hackrf.start_rx()
# sleep(1)
# hackrf.stop_rx()

# print(hackrf.buffer)
# print(len(hackrf.buffer))
