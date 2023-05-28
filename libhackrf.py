from ctypes import *
import numpy as np
from cinterface import (
    libhackrf,
    p_hackrf_device,
    TranscieverMode,
    lib_hackrf_transfer,
    lib_read_partid_serialno_t,
)


class HackRF(object):
    _center_freq: int = 100e6
    _sample_rate: int = 20e6
    _amplifier_on: bool = False
    _lna_gain: int = 16
    _vga_gain: int = 16
    _device_opened = False
    _device_pointer: p_hackrf_device = p_hackrf_device(None)
    _transceiver_mode: TranscieverMode = TranscieverMode.HACKRF_TRANSCEIVER_MODE_OFF
    _rx_buffer_limit: int = 0
    buffer: bytearray = bytearray()

    @staticmethod
    def enumerate() -> list[str]:
        """
        Return array of serial numbers of the devices connected to the host as strings
        """
        r = libhackrf.hackrf_device_list()
        count = r.contents.devicecount
        return [s.decode("utf-8") for s in r.contents.serial_numbers[:count]]

    def __init__(self, device_index: int = 0):
        """
        Create instance for device_index, which corresponds to array obtained from enumerate()
        Will open device automatically
        """
        self.open(device_index)

        self.amplifier_on = False
        self.lna_gain = 16
        self.vga_gain = 16
        self.center_freq = 433.2e6
        self.sample_rate = 20e6
        # we need to keep this value in memory constantly because Python garbage collector tends to
        # delete it when it goes out of scope, and we get segfault in C library
        self._cfunc_rx_callback = CFUNCTYPE(c_int, POINTER(lib_hackrf_transfer))(
            self._rx_callback
        )

    def open(self, device_index: int = 0) -> None:
        """
        Open device to start communications
        """
        hdl = libhackrf.hackrf_device_list()
        result = libhackrf.hackrf_device_list_open(
            hdl, device_index, pointer(self._device_pointer)
        )
        if result != 0:
            raise RuntimeError(f"Error code {result} while opening HackRF")
        self._device_opened = True

    def close(self):
        """
        Close device communications
        """
        if not self._device_opened:
            return

        libhackrf.hackrf_close(self._device_pointer)
        self.device_opened = False

    def __del__(self):
        self.close()

    def _rx_callback(self, hackrf_transfer: lib_hackrf_transfer) -> int:
        """
        Callback function will populate self.buffer with samples.
        As specified in libhackrf docs, it should return nonzero when no more samples needed.
        Will return 1  when number of samples reaches self._rx_buffer_limit.
        Internal use only.
        """
        transfer_contents = hackrf_transfer.contents
        bytes = bytearray(
            cast(
                transfer_contents.buffer,
                POINTER(c_byte * transfer_contents.buffer_length),
            ).contents
        )
        if (
            self._rx_buffer_limit
            and len(self.buffer) + len(bytes) >= self._rx_buffer_limit
        ):
            self.buffer += bytes[: self._rx_buffer_limit - len(self.buffer)]
            self._transceiver_mode = TranscieverMode.HACKRF_TRANSCEIVER_MODE_OFF
            return 1
        self.buffer += bytes
        return 0

    def start_rx(self) -> None:
        """
        Start receving data, will collect up to rx_buffer_limit bytes of data. If this value is zero,
        user is responsible to stop data acquisition by executing stop_rx()
        """
        self.buffer.clear()
        self._transceiver_mode = TranscieverMode.HACKRF_TRANSCEIVER_MODE_RECEIVE
        # we need to keep it as a var in function scope, or garbage collector will get rid of it and lead to segfault in C
        result = libhackrf.hackrf_start_rx(
            self._device_pointer,
            self._cfunc_rx_callback,
            None,
        )
        if result != 0:
            raise RuntimeError(f"Error code {result} while starting rx")

    def stop_rx(self) -> None:
        """
        Stop receiving that was started by start_rx() (or also by read_samples() under multithreading/multiprocessing)
        """
        self._transceiver_mode = TranscieverMode.HACKRF_TRANSCEIVER_MODE_OFF
        result = libhackrf.hackrf_stop_rx(self._device_pointer)
        if result != 0:
            raise RuntimeError(f"Error code {result} while stopping rx")

    def read_samples(self, num_samples: int = 131072) -> np.array:
        """
        Synchrous function to read predefined number of samples into buffer and return them as numpy array
        """
        # prevent running forever
        if not num_samples:
            return np.array([])

        self._rx_buffer_limit = int(2 * num_samples)
        self.start_rx()

        while self._transceiver_mode != TranscieverMode.HACKRF_TRANSCEIVER_MODE_OFF:
            pass
        self.buffer = self.buffer[0 : self._rx_buffer_limit]
        # convert samples to iq
        values = np.array(self.buffer).astype(np.int8)
        iq = values.astype(np.float64).view(np.complex128)
        iq /= 127.5
        iq -= 1 + 1j
        return iq

    @property
    def center_freq(self) -> int:
        """
        Get current center frequency in Hertz
        """
        return self._center_freq

    @center_freq.setter
    def center_freq(self, freq: int) -> None:
        """
        Set center frequency in Hertz
        """
        freq = int(freq)
        result = libhackrf.hackrf_set_freq(self._device_pointer, freq)
        if result != 0:
            raise RuntimeError(
                "Error code %d when setting frequency to %d Hz" % (result, freq)
            )
        self._center_freq = freq

    @property
    def sample_rate(self) -> int:
        """
        Get current sampling rate in Hertz
        """
        return self._sample_rate

    @sample_rate.setter
    def sample_rate(self, rate: int) -> None:
        """
        Set sampling rate in Hertz
        """
        result = libhackrf.hackrf_set_sample_rate(self._device_pointer, rate)
        if result != 0:
            # TODO: make this error message better
            raise RuntimeError("Sample rate set failure")
        self._sample_rate = rate
        return

    @property
    def lna_gain(self) -> int:
        """
        Get current low noise amplifier gain.
        """
        return self.lna_gain

    @lna_gain.setter
    def lna_gain(self, gain: int) -> None:
        """
        Set low noise amplifier gain.
        """
        # rounds down to multiple of 8 (15 -> 8, 39 -> 32), etc.
        # internally, hackrf_set_lna_gain does the same thing
        # But we take care of it so we can keep track of the correct gain
        gain -= gain % 8
        result = libhackrf.hackrf_set_lna_gain(self._device_pointer, gain)
        if result != 0:
            raise RuntimeError(f"Error code {result} while setting LNA gain")
        self._lna_gain = gain

    @property
    def vga_gain(self) -> int:
        """
        Get current variable gain amplifier (VGA) gain value.
        """
        return self._vga_gain

    @vga_gain.setter
    def vga_gain(self, gain: int) -> None:
        """
        Set variable gain amplifier (VGA) gain value.
        """
        gain -= gain % 2
        result = libhackrf.hackrf_set_vga_gain(self._device_pointer, gain)
        if result != 0:
            raise RuntimeError(f"Error code {result} while setting VGA gain")
        self._vga_gain = gain

    @property
    def amplifier_on(self) -> bool:
        """
        Check if amplifier is on or off.
        """
        return self._amplifier_on

    @amplifier_on.setter
    def amplifier_on(self, enable: bool) -> None:
        """
        Enable and disable amplifier.
        """
        result = libhackrf.hackrf_set_amp_enable(
            self._device_pointer, 1 if enable else 0
        )
        if result != 0:
            raise RuntimeError(
                f"Error code {result} while turning amplifier to {enable}"
            )

    @property
    def rx_buffer_limit(self) -> int:
        """
        Get current receive buffer limit. 0 means that start_rx() will collect data until stop_rx() is called.
        """
        return self._rx_buffer_limit

    @rx_buffer_limit.setter
    def rx_buffer_limit(self, bytes: int) -> None:
        """
        Set receive buffer limit. start_rx() will stop collecting data when rx_buffer_limit is reached
        0 means that start_rx() will collect data until stop_rx() is called.
        """
        self._rx_buffer_limit = bytes

    def get_serial_no(self):
        sn = lib_read_partid_serialno_t()
        result = libhackrf.hackrf_board_partid_serialno_read(self._device_pointer, sn)
        if result != 0:
            raise RuntimeError(
                f"Error code {result} while reading device serial number"
            )
        return "".join([f"{sn.serial_no[i]:08x}" for i in range(4)])
