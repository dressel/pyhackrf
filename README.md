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

# Example Use

To create a hackrf device:

```python
from libhackrf import *

hackrf = HackRF()
```

There is a 14 dB amplifier at the front of the HackRF that you can turn on or off.
I believe the default is off.

The LNA gain setting applies to the IF signal.
It can take values from 0 to 40 dB in 8 dB steps.

The VGA gain setting applies to the baseband signal.
It can take values from 0 to 62 dB in 2 dB steps.

The LNA and VGA gains are set to the nearest step below the desired value.
So if you try to set the LNA gain to 17-23 dB, the gain will be set to 16 dB.
The same applies for the VGA gain; trying to set the gain to 27 dB will result in 26 dB.
```python
# enable/disable the built-in amplifier:
hackrf.enable_amp()

# setting the LNA or VGA gains
hackrf.lna_gain = 8
hackrf.vga_gain = 22

# can also use setters or getters
hackrf.set_lna_gain(8)
hackrf.set_vga_gain(22)
```


# Spectral Power Density Example

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

