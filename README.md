# pyhackrf

A Python wrappper for libhackrf

# Description

Python bindings for native HackRF library libhackrf that aims to implement all features of HackRF accessible via its C interface, but via convenient Pythonic class.

Supports receive, transmit, sweep, setting all gains, baseband filter and bias tee.

# Quick Example

To take samples and plot the power spectral density:

```python
from libhackrf import HackRF
from pylab import *     # for plotting

hackrf = HackRF()

hackrf.sample_rate = 20e6
hackrf.center_freq = 88.5e6

samples = hackrf.read_samples(2e6)

# use matplotlib to estimate and plot the PSD
psd(samples, NFFT=1024, Fs=hackrf.sample_rate/1e6, Fc=hackrf.center_freq/1e6)
xlabel('Frequency (MHz)')
ylabel('Relative power (dB)')
show()
```

# More Example Use

First, import class from module
```python
from libhackrf import HackRF
```


Enumerate HackRF devices attached to host as strings of serial numbers:

```python
print(HackRF.enumerate())
# will output something like ['0000000000000000719031ac235bb14a']
```

Create device:

```python
hackrf = HackRF()
# If you have two HackRFs plugged in, you can open them with the device_index argument:
hackrf1 = HackRF(device_index = 0)
hackrf2 = HackRF(device_index = 1)
```

Configure receiver and read some data synchronously as IQ complex signal:

```python
hackrf.sample_rate = 20e6
hackrf.center_freq = 88.5e6
hackrf.baseband_filter = 5e6
samples = hackrf.read_samples(1e6)
print(len(samples))
```

Over 1 second, read at most 50000 samples asynchrously:

```python
hackrf.sample_count_limit = 50000
hackrf.start_rx()
sleep(1) # you can do other things in the meanwhile
hackrf.stop_rx()
```

Pipe output into callback function that calculates and prints signal amplitude. Stop after 1 second:

```python
import numpy as np

def pipe(data: bytes) -> bool:
    a = np.array(data).astype(np.int8).astype(np.float64).view(np.complex128)
    strength = np.sum(np.absolute(a)) / len(a)
    dbfs = 20 * math.log10(strength)
    print(f"dBFS: { dbfs }")
    return False    # pipe function may return True to stop rx immediately

hackrf.start_rx(pipe_function=pipe)
sleep(1)
hackrf.stop_rx()
```

Sweep in two ranges (120-200 MHz and 500-700 MHz), and pipe data into function. Stop after one scan.
data is dict {freq1: bytes1, freq2: bytes2, ...}

```python
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
```

Sample some data over 2 seconds, wait for some time, and replay them:

```python

hackrf.sample_rate = 2e6
hackrf.center_freq = 433.2e6
hackrf.amplifier_on = True
hackrf.vga_gain = 16
hackrf.lna_gain = 16

hackrf.start_rx()
sleep(2)
hackrf.stop_rx()

# the data are in hackrf.buffer now. Replay them from buffer at max gain:

sleep(4)
hackrf.txvga_gain = 47
hackrf.start_tx()
sleep(2)
hackrf.stop_tx()
```


### Gains

There is a 14 dB amplifier at the front of the HackRF that you can turn on or off.
The default is off.

The LNA gain setting applies to the IF signal.
It can take values from 0 to 40 dB in 8 dB steps.
The default value is 16 dB.

The VGA gain setting applies to the baseband signal.
It can take values from 0 to 62 dB in 2 dB steps.
The default value is 16 dB.

The LNA and VGA gains are set to the nearest step below the desired value.
So if you try to set the LNA gain to 17-23 dB, the gain will be set to 16 dB.
The same applies for the VGA gain; trying to set the gain to 27 dB will result in 26 dB.

The TXVGA gain for transmitter is set to 0-47 dB.

Bias tee can be used to power external antenna at 3.3 V (50 mA max).

```python
# enable/disable the built-in amplifier:
hackrf.amplifier_on = True

# setting the LNA or VGA gains
hackrf.lna_gain = 8
hackrf.vga_gain = 22

hackrf.txvga_gain = 40

```



