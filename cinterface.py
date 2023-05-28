from ctypes import *
from enum import Enum

LIBNAME = "libhackrf.so.0"
libhackrf = CDLL(LIBNAME)


class HackRfVendorRequest(Enum):
    HACKRF_VENDOR_REQUEST_SET_TRANSCEIVER_MODE = 1
    HACKRF_VENDOR_REQUEST_MAX2837_WRITE = 2
    HACKRF_VENDOR_REQUEST_MAX2837_READ = 3
    HACKRF_VENDOR_REQUEST_SI5351C_WRITE = 4
    HACKRF_VENDOR_REQUEST_SI5351C_READ = 5
    HACKRF_VENDOR_REQUEST_SAMPLE_RATE_SET = 6
    HACKRF_VENDOR_REQUEST_BASEBAND_FILTER_BANDWIDTH_SET = 7
    HACKRF_VENDOR_REQUEST_RFFC5071_WRITE = 8
    HACKRF_VENDOR_REQUEST_RFFC5071_READ = 9
    HACKRF_VENDOR_REQUEST_SPIFLASH_ERASE = 10
    HACKRF_VENDOR_REQUEST_SPIFLASH_WRITE = 11
    HACKRF_VENDOR_REQUEST_SPIFLASH_READ = 12
    HACKRF_VENDOR_REQUEST_CPLD_WRITE = 13
    HACKRF_VENDOR_REQUEST_BOARD_ID_READ = 14
    HACKRF_VENDOR_REQUEST_VERSION_STRING_READ = 15
    HACKRF_VENDOR_REQUEST_SET_FREQ = 16
    HACKRF_VENDOR_REQUEST_AMP_ENABLE = 17
    HACKRF_VENDOR_REQUEST_BOARD_PARTID_SERIALNO_READ = 18
    HACKRF_VENDOR_REQUEST_SET_LNA_GAIN = 19
    HACKRF_VENDOR_REQUEST_SET_VGA_GAIN = 20
    HACKRF_VENDOR_REQUEST_SET_TXVGA_GAIN = 21


class HackRfConstants(Enum):
    LIBUSB_ENDPOINT_IN = 0x80
    LIBUSB_ENDPOINT_OUT = 0x00
    HACKRF_DEVICE_OUT = 0x40
    HACKRF_DEVICE_IN = 0xC0
    HACKRF_USB_VID = 0x1D50
    HACKRF_USB_PID = 0x6089


class HackRfError(Enum):
    HACKRF_SUCCESS = 0
    HACKRF_TRUE = 1
    HACKRF_ERROR_INVALID_PARAM = -2
    HACKRF_ERROR_NOT_FOUND = -5
    HACKRF_ERROR_BUSY = -6
    HACKRF_ERROR_NO_MEM = -11
    HACKRF_ERROR_LIBUSB = -1000
    HACKRF_ERROR_THREAD = -1001
    HACKRF_ERROR_STREAMING_THREAD_ERR = -1002
    HACKRF_ERROR_STREAMING_STOPPED = -1003
    HACKRF_ERROR_STREAMING_EXIT_CALLED = -1004
    HACKRF_ERROR_OTHER = -9999
    # Python defaults to returning none
    HACKRF_ERROR = None


class TranscieverMode(Enum):
    HACKRF_TRANSCEIVER_MODE_OFF = 0
    HACKRF_TRANSCEIVER_MODE_RECEIVE = 1
    HACKRF_TRANSCEIVER_MODE_TRANSMIT = 2


p_hackrf_device = c_void_p

"""
Data structures from libhackrf are named in accordance with C code and prefixed with lib_
"""


class lib_hackrf_transfer(Structure):
    _fields_ = [
        ("device", p_hackrf_device),
        ("buffer", POINTER(c_byte)),
        ("buffer_length", c_int),
        ("valid_length", c_int),
        ("rx_ctx", c_void_p),
        ("tx_ctx", c_void_p),
    ]


class lib_read_partid_serialno_t(Structure):
    _fields_ = [("part_id", c_uint32 * 2), ("serial_no", c_uint32 * 4)]


class lib_hackrf_device_list_t(Structure):
    _fields_ = [
        ("serial_numbers", POINTER(c_char_p)),
        ("usb_board_ids", c_void_p),
        ("usb_device_index", POINTER(c_int)),
        ("devicecount", c_int),
        ("usb_devices", POINTER(c_void_p)),
        ("usb_devicecount", c_int),
    ]


# extern ADDAPI int ADDCALL hackrf_init();
libhackrf.hackrf_init.restype = c_int
libhackrf.hackrf_init.argtypes = []
# extern ADDAPI int ADDCALL hackrf_open(hackrf_device** device);
libhackrf.hackrf_open.restype = c_int
libhackrf.hackrf_open.argtypes = [POINTER(p_hackrf_device)]

# extern ADDAPI int ADDCALL hackrf_device_list_open
#   (hackrf_device_list_t *list, int idx, hackrf_device** device);
libhackrf.hackrf_device_list_open.restype = c_int
libhackrf.hackrf_device_list_open.arg_types = [
    POINTER(lib_hackrf_device_list_t),
    c_int,
    POINTER(p_hackrf_device),
]

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
libhackrf.hackrf_start_rx.argtypes = [
    p_hackrf_device,
    CFUNCTYPE(c_int, POINTER(lib_hackrf_transfer)),
    c_void_p,
]

# extern ADDAPI int ADDCALL hackrf_stop_rx(hackrf_device* device);
libhackrf.hackrf_stop_rx.restype = c_int
libhackrf.hackrf_stop_rx.argtypes = [p_hackrf_device]

# extern ADDAPI hackrf_device_list_t* ADDCALL hackrf_device_list();
libhackrf.hackrf_device_list.restype = POINTER(lib_hackrf_device_list_t)

# extern ADDAPI int ADDCALL hackrf_set_freq(hackrf_device* device,
# const uint64_t freq_hz);
libhackrf.hackrf_set_freq.restype = c_int
libhackrf.hackrf_set_freq.argtypes = [p_hackrf_device, c_uint64]


# extern ADDAPI int ADDCALL
# hackrf_board_partid_serialno_read(hackrf_device* device,
# read_partid_serialno_t* read_partid_serialno);
libhackrf.hackrf_board_partid_serialno_read.restype = c_int
libhackrf.hackrf_board_partid_serialno_read.argtypes = [
    p_hackrf_device,
    POINTER(lib_read_partid_serialno_t),
]

if libhackrf.hackrf_init() != 0:
    raise RuntimeError(f"Unable to initialize libhackrf {LIBNAME}.")
