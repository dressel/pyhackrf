from libhackrf import *


hackrf = HackRF()

hackrf.sample_rate = 20e6
hackrf.center_freq = 88.5e6

sn = hackrf.get_serial_no()

samples = hackrf.read_samples()



#result = libhackrf.hackrf_set_sample_rate(dev, 20e6)
#print "set sample rate = ", result
#
#result = libhackrf.hackrf_set_lna_gain(dev, 8)
#print "set lna gain = ", result
#
#result = libhackrf.hackrf_set_vga_gain(dev, 20)
#print "set vga gain = ", result
#
#result = libhackrf.hackrf_start_rx(dev, rx_callback, None)
#print "starting rx... = ", result


#libhackrf.hackrf_exit()
