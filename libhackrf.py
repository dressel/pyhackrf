# TODO: only use transfer->valid_length in callbacks
# TODO: make error messages more informative

from ctypes import *
import logging
import os
import numpy as np
import time

try:
    from itertools import izip
except ImportError:
    izip = zip

path = os.path.dirname(__file__)
logging.basicConfig()
logger = logging.getLogger('HackRf Core')
logger.setLevel(logging.DEBUG)

#libhackrf = CDLL('/usr/local/lib/libhackrf.so')
libhackrf = CDLL('libhackrf.so.0')

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

HackRfVendorRequest = enum(
    HACKRF_VENDOR_REQUEST_SET_TRANSCEIVER_MODE=1,
    HACKRF_VENDOR_REQUEST_MAX2837_WRITE=2,
    HACKRF_VENDOR_REQUEST_MAX2837_READ=3,
    HACKRF_VENDOR_REQUEST_SI5351C_WRITE=4,
    HACKRF_VENDOR_REQUEST_SI5351C_READ=5,
    HACKRF_VENDOR_REQUEST_SAMPLE_RATE_SET=6,
    HACKRF_VENDOR_REQUEST_BASEBAND_FILTER_BANDWIDTH_SET=7,
    HACKRF_VENDOR_REQUEST_RFFC5071_WRITE=8,
    HACKRF_VENDOR_REQUEST_RFFC5071_READ=9,
    HACKRF_VENDOR_REQUEST_SPIFLASH_ERASE=10,
    HACKRF_VENDOR_REQUEST_SPIFLASH_WRITE=11,
    HACKRF_VENDOR_REQUEST_SPIFLASH_READ=12,
    HACKRF_VENDOR_REQUEST_CPLD_WRITE=13,
    HACKRF_VENDOR_REQUEST_BOARD_ID_READ=14,
    HACKRF_VENDOR_REQUEST_VERSION_STRING_READ=15,
    HACKRF_VENDOR_REQUEST_SET_FREQ=16,
    HACKRF_VENDOR_REQUEST_AMP_ENABLE=17,
    HACKRF_VENDOR_REQUEST_BOARD_PARTID_SERIALNO_READ=18,
    HACKRF_VENDOR_REQUEST_SET_LNA_GAIN=19,
    HACKRF_VENDOR_REQUEST_SET_VGA_GAIN=20,
    HACKRF_VENDOR_REQUEST_SET_TXVGA_GAIN=21)

HackRfConstants = enum(
    LIBUSB_ENDPOINT_IN=0x80,
    LIBUSB_ENDPOINT_OUT=0x00,
    HACKRF_DEVICE_OUT=0x40,
    HACKRF_DEVICE_IN=0xC0,
    HACKRF_USB_VID=0x1d50,
    HACKRF_USB_PID=0x6089)

HackRfError = enum(
    HACKRF_SUCCESS=0,
    HACKRF_TRUE=1,
    HACKRF_ERROR_INVALID_PARAM=-2,
    HACKRF_ERROR_NOT_FOUND=-5,
    HACKRF_ERROR_BUSY=-6,
    HACKRF_ERROR_NO_MEM=-11,
    HACKRF_ERROR_LIBUSB=-1000,
    HACKRF_ERROR_THREAD=-1001,
    HACKRF_ERROR_STREAMING_THREAD_ERR=-1002,
    HACKRF_ERROR_STREAMING_STOPPED=-1003,
    HACKRF_ERROR_STREAMING_EXIT_CALLED=-1004,
    HACKRF_ERROR_OTHER=-9999,
    # Python defaults to returning none
    HACKRF_ERROR=None)

HackRfTranscieverMode = enum(
    HACKRF_TRANSCEIVER_MODE_OFF=0,
    HACKRF_TRANSCEIVER_MODE_RECEIVE=1,
    HACKRF_TRANSCEIVER_MODE_TRANSMIT=2)

# Data structures
_libusb_device_handle = c_void_p
_pthread_t = c_ulong

p_hackrf_device = c_void_p

class hackrf_transfer(Structure):
        _fields_ = [("device", p_hackrf_device),
                ("buffer", POINTER(c_byte)),
                ("buffer_length", c_int),
                ("valid_length", c_int),
                ("rx_ctx", c_void_p),
                ("tx_ctx", c_void_p) ]

class read_partid_serialno_t(Structure):
        _fields_ = [("part_id", c_uint32*2),
                ("serial_no", c_uint32*4) ]

class hackrf_device_list_t(Structure):
        _fields_ = [("serial_numbers", POINTER(c_char_p)),
                ("usb_board_ids", c_void_p),
                ("usb_device_index", POINTER(c_int)),
                ("devicecount", c_int),
                ("usb_devices", POINTER(c_void_p)),
                ("usb_devicecount", c_int) ]

#
#_callback = CFUNCTYPE(c_int, POINTER(hackrf_transfer))
_callback = CFUNCTYPE(c_int, POINTER(hackrf_transfer))


# extern ADDAPI int ADDCALL hackrf_init();
libhackrf.hackrf_init.restype = c_int
libhackrf.hackrf_init.argtypes = []
# extern ADDAPI int ADDCALL hackrf_exit();
libhackrf.hackrf_exit.restype = c_int
libhackrf.hackrf_exit.argtypes = []
# extern ADDAPI int ADDCALL hackrf_open(hackrf_device** device);
libhackrf.hackrf_open.restype = c_int
libhackrf.hackrf_open.argtypes = [POINTER(p_hackrf_device)]
# extern ADDAPI int ADDCALL hackrf_open_by_serial
#   (const char* const desired_serial_number, hackrf_device** device);
# TODO: check that this one works
f = libhackrf.hackrf_open_by_serial
f.restype = c_int
f.argtypes = [POINTER(p_hackrf_device)]

#extern ADDAPI int ADDCALL hackrf_device_list_open
#   (hackrf_device_list_t *list, int idx, hackrf_device** device);
f = libhackrf.hackrf_device_list_open
f.restype = c_int
f.arg_types = [POINTER(hackrf_device_list_t), c_int, POINTER(p_hackrf_device)]
#f.arg_types = [hackrf_device_list_t, c_int, POINTER(p_hackrf_device)]

# extern ADDAPI int ADDCALL hackrf_close(hackrf_device* device);
libhackrf.hackrf_close.restype = c_int
libhackrf.hackrf_close.argtypes = [p_hackrf_device]



# extern ADDAPI int ADDCALL hackrf_set_sample_rate(hackrf_device*
# device, const double freq_hz);
libhackrf.hackrf_set_sample_rate.restype = c_int
libhackrf.hackrf_set_sample_rate.argtypes = [p_hackrf_device, c_double]

# GAIN SETTINGS
# extern ADDAPI int ADDCALL hackrf_set_amp_enable(hackrf_device*
# device, const uint8_t value);
libhackrf.hackrf_set_amp_enable.restype = c_int
libhackrf.hackrf_set_amp_enable.argtypes = [p_hackrf_device, c_uint8]
# extern ADDAPI int ADDCALL hackrf_set_lna_gain(hackrf_device* device,
# uint32_t value);
libhackrf.hackrf_set_lna_gain.restype = c_int
libhackrf.hackrf_set_lna_gain.argtypes = [p_hackrf_device, c_uint32]
# extern ADDAPI int ADDCALL hackrf_set_vga_gain(hackrf_device* device,
# uint32_t value);
libhackrf.hackrf_set_vga_gain.restype = c_int
libhackrf.hackrf_set_vga_gain.argtypes = [p_hackrf_device, c_uint32]

# START AND STOP RX
# extern ADDAPI int ADDCALL hackrf_start_rx(hackrf_device* device,
# hackrf_sample_block_cb_fn callback, void* rx_ctx);
libhackrf.hackrf_start_rx.restype = c_int
libhackrf.hackrf_start_rx.argtypes = [p_hackrf_device, _callback, c_void_p]
# extern ADDAPI int ADDCALL hackrf_stop_rx(hackrf_device* device);
libhackrf.hackrf_stop_rx.restype = c_int
libhackrf.hackrf_stop_rx.argtypes = [p_hackrf_device]

#extern ADDAPI hackrf_device_list_t* ADDCALL hackrf_device_list();
f = libhackrf.hackrf_device_list
f.restype = POINTER(hackrf_device_list_t)
f.argtypes = []


def hackrf_device_list():
    return libhackrf.hackrf_device_list()



# dictionary containing all hackrf_devices in use
_hackrf_dict = dict()
def get_dict():
    return _hackrf_dict


def read_samples_cb(hackrf_transfer):

    # let's access the contents
    c = hackrf_transfer.contents

    # c.device is an int representing the pointer to the hackrf device
    # we can get the pointer with p_hackrf_device(c.device)
    this_hackrf = _hackrf_dict[c.device]

    if len(this_hackrf.buffer) == this_hackrf.num_bytes:
        this_hackrf.still_sampling = False
        return 0

    # like == case, but cut down the buffer to size
    if len(this_hackrf.buffer) > this_hackrf.num_bytes:
        this_hackrf.still_sampling = False
        this_hackrf.buffer = this_hackrf.buffer[0:this_hackrf.num_bytes]
        return 0

    # grab the buffer data and concatenate it
    values = cast(c.buffer, POINTER(c_byte*c.buffer_length)).contents
    this_hackrf.buffer = this_hackrf.buffer + bytearray(values)

    #print("len(bd) = ",len(this_hackrf.buffer))

    return 0


rs_callback = _callback(read_samples_cb)



## extern ADDAPI int ADDCALL hackrf_start_tx(hackrf_device* device,
## hackrf_sample_block_cb_fn callback, void* tx_ctx);
#libhackrf.hackrf_start_tx.restype = c_int
#libhackrf.hackrf_start_tx.argtypes = [POINTER(hackrf_device), _callback, c_void_p]
## extern ADDAPI int ADDCALL hackrf_stop_tx(hackrf_device* device);
#libhackrf.hackrf_stop_tx.restype = c_int
#libhackrf.hackrf_stop_tx.argtypes = [POINTER(hackrf_device)]
# extern ADDAPI int ADDCALL hackrf_is_streaming(hackrf_device* device);
libhackrf.hackrf_is_streaming.restype = c_int
libhackrf.hackrf_is_streaming.argtypes = [p_hackrf_device]
## extern ADDAPI int ADDCALL hackrf_max2837_read(hackrf_device* device,
## uint8_t register_number, uint16_t* value);
#libhackrf.hackrf_max2837_read.restype = c_int
#libhackrf.hackrf_max2837_read.argtypes = [
#    POINTER(hackrf_device), c_uint8, POINTER(c_uint16)]
## extern ADDAPI int ADDCALL hackrf_max2837_write(hackrf_device* device,
## uint8_t register_number, uint16_t value);
#libhackrf.hackrf_max2837_write.restype = c_int
#libhackrf.hackrf_max2837_write.argtypes = [POINTER(hackrf_device), c_uint8, c_uint16]
## extern ADDAPI int ADDCALL hackrf_si5351c_read(hackrf_device* device,
## uint16_t register_number, uint16_t* value);
#libhackrf.hackrf_si5351c_read.restype = c_int
#libhackrf.hackrf_si5351c_read.argtypes = [
#    POINTER(hackrf_device), c_uint16, POINTER(c_uint16)]
## extern ADDAPI int ADDCALL hackrf_si5351c_write(hackrf_device* device,
## uint16_t register_number, uint16_t value);
#libhackrf.hackrf_si5351c_write.restype = c_int
#libhackrf.hackrf_si5351c_write.argtypes = [POINTER(hackrf_device), c_uint16, c_uint16]
## extern ADDAPI int ADDCALL
## hackrf_set_baseband_filter_bandwidth(hackrf_device* device, const
## uint32_t bandwidth_hz);
#libhackrf.hackrf_set_baseband_filter_bandwidth.restype = c_int
#libhackrf.hackrf_set_baseband_filter_bandwidth.argtypes = [
#    POINTER(hackrf_device), c_uint32]
## extern ADDAPI int ADDCALL hackrf_rffc5071_read(hackrf_device* device,
## uint8_t register_number, uint16_t* value);
#libhackrf.hackrf_rffc5071_read.restype = c_int
#libhackrf.hackrf_rffc5071_read.argtypes = [
#    POINTER(hackrf_device), c_uint8, POINTER(c_uint16)]
## extern ADDAPI int ADDCALL hackrf_rffc5071_write(hackrf_device*
## device, uint8_t register_number, uint16_t value);
#libhackrf.hackrf_rffc5071_write.restype = c_int
#libhackrf.hackrf_rffc5071_write.argtypes = [POINTER(hackrf_device), c_uint8, c_uint16]
## extern ADDAPI int ADDCALL hackrf_spiflash_erase(hackrf_device*
## device);
#libhackrf.hackrf_spiflash_erase.restype = c_int
#libhackrf.hackrf_spiflash_erase.argtypes = [POINTER(hackrf_device)]
## extern ADDAPI int ADDCALL hackrf_spiflash_write(hackrf_device*
## device, const uint32_t address, const uint16_t length, unsigned char*
## const data);
#libhackrf.hackrf_spiflash_write.restype = c_int
#libhackrf.hackrf_spiflash_write.argtypes = [
#    POINTER(hackrf_device), c_uint32, c_uint16, POINTER(c_ubyte)]
## extern ADDAPI int ADDCALL hackrf_spiflash_read(hackrf_device* device,
## const uint32_t address, const uint16_t length, unsigned char* data);
#libhackrf.hackrf_spiflash_read.restype = c_int
#libhackrf.hackrf_spiflash_read.argtypes = [
#    POINTER(hackrf_device), c_uint32, c_uint16, POINTER(c_ubyte)]
## extern ADDAPI int ADDCALL hackrf_cpld_write(hackrf_device* device,
##         unsigned char* const data, const unsigned int total_length);
#libhackrf.hackrf_cpld_write.restype = c_int
#libhackrf.hackrf_cpld_write.argtypes = [POINTER(hackrf_device), POINTER(c_ubyte), c_uint]
## extern ADDAPI int ADDCALL hackrf_board_id_read(hackrf_device* device,
## uint8_t* value);
#libhackrf.hackrf_board_id_read.restype = c_int
#libhackrf.hackrf_board_id_read.argtypes = [POINTER(hackrf_device), POINTER(c_uint8)]
## extern ADDAPI int ADDCALL hackrf_version_string_read(hackrf_device*
## device, char* version, uint8_t length);
#libhackrf.hackrf_version_string_read.restype = c_int
#libhackrf.hackrf_version_string_read.argtypes = [POINTER(hackrf_device), POINTER(c_char), c_uint8]
# extern ADDAPI int ADDCALL hackrf_set_freq(hackrf_device* device,
# const uint64_t freq_hz);
libhackrf.hackrf_set_freq.restype = c_int
libhackrf.hackrf_set_freq.argtypes = [p_hackrf_device, c_uint64]
#
## extern ADDAPI int ADDCALL hackrf_set_freq_explicit(hackrf_device* device,
##         const uint64_t if_freq_hz, const uint64_t lo_freq_hz,
##         const enum rf_path_filter path);,
## libhackrf.hackrf_set_freq_explicit.restype = c_int
## libhackrf.hackrf_set_freq_explicit.argtypes = [c_uint64,
## c_uint64, ]
#
## extern ADDAPI int ADDCALL
## hackrf_set_sample_rate_manual(hackrf_device* device, const uint32_t
## freq_hz, const uint32_t divider);
#libhackrf.hackrf_set_sample_rate_manual.restype = c_int
#libhackrf.hackrf_set_sample_rate_manual.argtypes = [
#    POINTER(hackrf_device), c_uint32, c_uint32]
#
# extern ADDAPI int ADDCALL
# hackrf_board_partid_serialno_read(hackrf_device* device,
# read_partid_serialno_t* read_partid_serialno);
f = libhackrf.hackrf_board_partid_serialno_read
f.restype = c_int
f.argtypes = [p_hackrf_device, POINTER(read_partid_serialno_t)]

## extern ADDAPI int ADDCALL hackrf_set_txvga_gain(hackrf_device*
## device, uint32_t value);
#libhackrf.hackrf_set_txvga_gain.restype = c_int
#libhackrf.hackrf_set_txvga_gain.argtypes = [POINTER(hackrf_device), c_uint32]
## extern ADDAPI int ADDCALL hackrf_set_antenna_enable(hackrf_device*
## device, const uint8_t value);
#libhackrf.hackrf_set_antenna_enable.restype = c_int
#libhackrf.hackrf_set_antenna_enable.argtypes = [POINTER(hackrf_device), c_uint8]
#
## extern ADDAPI const char* ADDCALL hackrf_error_name(enum hackrf_error errcode);
## libhackrf.hackrf_error_name.restype = POINTER(c_char)
## libhackrf.hackrf_error_name.argtypes = []
#
## extern ADDAPI const char* ADDCALL hackrf_board_id_name(enum hackrf_board_id board_id);
## libhackrf.hackrf_board_id_name.restype = POINTER(c_char)
## libhackrf.hackrf_board_id_name.argtypes = []
#
## extern ADDAPI const char* ADDCALL hackrf_filter_path_name(const enum rf_path_filter path);
## libhackrf.hackrf_filter_path_name.restype = POINTER(c_char)
## libhackrf.hackrf_filter_path_name.argtypes = []
#


class HackRF(object):
    
    _center_freq = 100e6
    _sample_rate = 20e6
    device_opened = False

    def __init__(self, device_index=0):
        self.open(device_index)
        
        # TODO: initialize defaults here
        self.disable_amp()
        self.set_lna_gain(16)
        self.set_vga_gain(16)

        self.buffer = bytearray()
        self.num_bytes = 16*262144

    def open(self, device_index=0):

        # pointer to device structure
        self.dev_p = p_hackrf_device(None)

        hdl = hackrf_device_list()
        result = libhackrf.hackrf_device_list_open(hdl, device_index, pointer(self.dev_p))
        if result != 0:
            raise IOError('Error code %d when opening HackRF' % (result))

        # This is how I used to do it...
        # Note I only pass in the dev_p here, but it worked.
        # But above, I have to pass in a pointer(self.dev_p)
        # They should both take the same thing
        #result = libhackrf.hackrf_open(self.dev_p)
        #if result != 0:
        #    raise IOError('Error code %d when opening HackRF' % (result))

        # self.dev_p.value returns the integer value of the pointer

        _hackrf_dict[self.dev_p.value] = self
        #print("self.dev_p.value = ", self.dev_p.value)

        self.device_opened = True

    def close(self):
        if not self.device_opened:
            return

        libhackrf.hackrf_close(self.dev_p)
        self.device_opened = False

    def __del__(self):
        print("del function is being called")
        self.close()

    # sleep_time in seconds
    # I used to have just pass in the while loop
    def read_samples(self,num_samples=131072,sleep_time=0.05):

        num_bytes = 2*num_samples
        self.num_bytes = int(num_bytes)

        self.buffer = bytearray()

        # start receiving
        result = libhackrf.hackrf_start_rx(self.dev_p, rs_callback, None)
        if result != 0:
            raise IOError("Error in hackrf_start_rx")
        self.still_sampling = True      # this does get called

        while self.still_sampling:
            if sleep_time:
                time.sleep(sleep_time)

        # stop receiving
        result = libhackrf.hackrf_stop_rx(self.dev_p)
        if result != 0:
            raise IOError("Error in hackrf_stop_rx")

        # convert samples to iq
        iq = bytes2iq(self.buffer)

        return iq


    # setting the center frequency
    def set_freq(self, freq):
        freq = int(freq)
        result = libhackrf.hackrf_set_freq(self.dev_p, freq)
        if result != 0:
            raise IOError('Error code %d when setting frequency to %d Hz'\
                    % (result, freq))

        self._center_freq = freq
        return

    def get_freq(self):
        return self._center_freq

    center_freq = property(get_freq, set_freq)


    # sample rate
    def set_sample_rate(self, rate):
        result = libhackrf.hackrf_set_sample_rate(self.dev_p, rate)
        if result != 0:
            # TODO: make this error message better
            raise IOError('Sample rate set failure')
        self._sample_rate = rate
        return

    def get_sample_rate(self):
        return self._sample_rate

    sample_rate = property(get_sample_rate, set_sample_rate)

    def get_serial_no(self):
        return get_serial_no(self.dev_p)

    def enable_amp(self):
        result = libhackrf.hackrf_set_amp_enable(self.dev_p, 1)
        if result != 0:
            # TODO: make this a better message
            raise IOError("error enabling amp")
        return 0

    def disable_amp(self):
        result = libhackrf.hackrf_set_amp_enable(self.dev_p, 0)
        if result != 0:
            # TODO: make this a better message
            raise IOError("error disabling amp")
        return 0

    # rounds down to multiple of 8 (15 -> 8, 39 -> 32), etc.
    # internally, hackrf_set_lna_gain does the same thing
    # But we take care of it so we can keep track of the correct gain
    def set_lna_gain(self, gain):
        gain -= (gain % 8)    # round DOWN to multiple of 8
        result = libhackrf.hackrf_set_lna_gain(self.dev_p, gain)
        if result != 0:
            # TODO: make this a better message
            raise IOError("error setting lna gain")
        self._lna_gain = gain
        print("LNA gain set to",gain,"dB.")
        return 0

    def get_lna_gain(self):
        return self._lna_gain

    lna_gain = property(get_lna_gain, set_lna_gain)

    def set_vga_gain(self, gain):
        gain -= (gain % 2)
        result = libhackrf.hackrf_set_vga_gain(self.dev_p, gain)
        if result != 0:
            # TODO: make this a better message
            raise IOError("error setting vga gain")
        self._vga_gain = gain
        print("VGA gain set to",gain,"dB.")
        return 0

    def get_vga_gain(self):
        return self._vga_gain

    vga_gain = property(get_vga_gain, set_vga_gain)

    # rx_cb_fn is a callback function (in python)
    def start_rx(self, rx_cb_fn):
        rx_cb = _callback(rx_cb_fn)
        result = libhackrf.hackrf_start_rx(self.dev_p, rx_cb, None)
        if result != 0:
            raise IOError("start_rx failure")

    def stop_rx(self):
        result = libhackrf.hackrf_stop_rx(self.dev_p)
        if result != 0:
            raise IOError("stop_rx failure");



# returns serial number as a string
# it is too big to be a single number, so make it a string
# the returned string matches the hackrf_info output
def get_serial_no(dev_p):
    sn = read_partid_serialno_t()
    result = libhackrf.hackrf_board_partid_serialno_read(dev_p, sn)
    if result != 0:
        raise IOError("Error %d while getting serial number" % (result))


    # convert the serial number to a string
    sn_str = ""
    for i in xrange(0,4): 
        sni = sn.serial_no[i]
        if sni == 0:
            sn_str += "00000000"
        else:
            sn_str += hex(sni)[2:-1]

    return sn_str

# converts byte array to iq values
def bytes2iq(data):
    values = np.array(data).astype(np.int8)
    iq = values.astype(np.float64).view(np.complex128)
    iq /= 127.5
    iq -= (1 + 1j)

    return iq




# really, user shouldn't have to call this function at all
result = libhackrf.hackrf_init()
if result != 0:
    print("error initializing the hackrf library")
