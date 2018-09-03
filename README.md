# pyhackrf

A Python wrappper for libhackrf

# Description

I wanted something like [pyrtldsr](https://github.com/roger-/pyrtlsdr) for the HackRF.
That is, I wanted a convenient python interface that handled libhackrf for me.
The closest thing I found was [py-hackrf-ctypes](https://github.com/wzyy2/py-hackrf-ctypes), but it's about four years old and libhackrf has changed in that time.
Also, I wanted a more direct copy of pyrtlsdr as I've used it before.

I have mashed together elements from pyrtlsdr and py-hackrf-ctypes to get started.
Currently, you need to have the libhackrf.py file in the directory in which you are using it.
Eventually I'll make it a nice package like pyrtlsdr.

This package is nowhere near complete but it implements `read_samples`, which is equivalent to the version found in pyrtlsdr.

# Examples

```python
from libhackrf import *
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

