from ctypes import *
import numpy as np
from collections.abc import Callable
from cinterface import (
    libhackrf,
    p_hackrf_device,
    TransceiverMode,
    lib_hackrf_transfer,
    lib_read_partid_serialno_t,
    ERRORS,
    BASEBAND_FILTER_VALID_VALUES,
)
import struct


class HackRF(object):
    _center_freq: int = 100e6
    _sample_rate: int = 20e6
    _filter_bandwidth: int
    _amplifier_on: bool = False
    _bias_tee_on: bool = False
    _lna_gain: int = 16
    _vga_gain: int = 16
    _txvga_gain: int = 10
    _device_opened = False
    _device_pointer: p_hackrf_device = p_hackrf_device(None)
    _transceiver_mode: TransceiverMode = TransceiverMode.HACKRF_TRANSCEIVER_MODE_OFF
    # function that will be called on incoming data. Argument is data bytes.
    # return value True means that we need to stop data acquisiton
    _rx_pipe_function: Callable[[bytes], int] = None
    # function that will be called on incoming data during sweep. Argument is dict like {center_freq1: bytes1, center_freq2: bytes2, ...}
    # return value True means that we need to stop data acquisiton
    _sweep_pipe_function: Callable[[dict], int] = None
    # counts samples that already have been stored or transferred to pipe function
    _sample_count: int = 0
    # set limit of samples to be stored or transferred to pipe function
    _sample_count_limit: int = 0
    # data collected in rx mode
    buffer: bytearray()

    @staticmethod
    def enumerate() -> list[str]:
        """
        Return array of serial numbers of the devices connected to the host as strings
        """
        r = libhackrf.hackrf_device_list()
        count = r.contents.devicecount
        return [s.decode("utf-8") for s in r.contents.serial_numbers[:count]]

    def _check_error(self, code: int) -> None:
        if code == 0 or code == -1004 or code == 1:
            return
        self._transceiver_mode = TransceiverMode.HACKRF_TRANSCEIVER_MODE_OFF
        self._bias_tee_on = False
        self.close()
        raise RuntimeError(
            ERRORS.get(code, f"libhackrf returned unknown error code {code}")
        )

    def __init__(self, device_index: int = 0):
        """
        Create instance for device_index, which corresponds to array obtained from enumerate()
        Will open device automatically and set parameters to the safe defaults.
        """
        self.open(device_index)

        self.amplifier_on = False
        self.bias_tee = False
        self.lna_gain = 16
        self.vga_gain = 16
        self.txvga_gain = 10
        self.center_freq = 433.2e6
        self.sample_rate = 20e6
        # we need to keep these values in memory constantly because Python garbage collector tends to
        # delete them when they go out of scope, and we get segfaults in C library
        self._cfunc_rx_callback = CFUNCTYPE(c_int, POINTER(lib_hackrf_transfer))(
            self._rx_callback
        )
        self._cfunc_sweep_callback = CFUNCTYPE(c_int, POINTER(lib_hackrf_transfer))(
            self._sweep_callback
        )
        self._cfunc_tx_callback = CFUNCTYPE(c_int, POINTER(lib_hackrf_transfer))(
            self._tx_callback
        )
        self._rx_pipe_function = None

    def open(self, device_index: int = 0) -> None:
        """
        Open device to start communications
        """
        hdl = libhackrf.hackrf_device_list()
        if device_index >= hdl.contents.devicecount:
            raise ValueError(
                f"HackRF with index {device_index} not attached to host (found {hdl.contents.devicecount} HackRF devices)"
            ) if hdl.contents.devicecount else ValueError(
                "No HackRF devices attached to host"
            )
        self._check_error(
            libhackrf.hackrf_device_list_open(
                hdl, device_index, pointer(self._device_pointer)
            )
        )
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
        Will return 1  when number of samples reaches self._sample_count_limit or when pipe function returns True.
        Internal use only.
        """
        bytes = bytearray(
            cast(
                hackrf_transfer.contents.buffer,
                POINTER(c_byte * hackrf_transfer.contents.buffer_length),
            ).contents
        )
        stop_acquisition = False
        if (
            self._sample_count_limit
            and len(bytes) + self._sample_count >= self._sample_count_limit
        ):
            bytes = bytes[: self._sample_count_limit - self._sample_count]
            stop_acquisition = True
        self._sample_count += len(bytes)
        if self._rx_pipe_function is not None:
            if self._rx_pipe_function(bytes):
                stop_acquisition = True
        else:
            self.buffer += bytes
        if stop_acquisition:
            self._transceiver_mode = TransceiverMode.HACKRF_TRANSCEIVER_MODE_OFF
            self._bias_tee_on = False
            return 1
        return 0

    def start_rx(self, pipe_function: Callable[[bytes], bool] = None) -> None:
        """
        Start receving data, will collect up to sample_count_limit bytes of data. If this value is zero,
        user is responsible to stop data acquisition by executing stop_rx()
        """
        self.buffer = bytearray()
        self._rx_pipe_function = pipe_function
        self._sample_count = 0
        self._transceiver_mode = TransceiverMode.HACKRF_TRANSCEIVER_MODE_RECEIVE
        self._check_error(
            libhackrf.hackrf_start_rx(
                self._device_pointer,
                self._cfunc_rx_callback,
                None,
            )
        )

    def stop_rx(self) -> None:
        """
        Stop receiving that was started by start_rx() (or also by read_samples() under multithreading/multiprocessing)
        """
        self._transceiver_mode = TransceiverMode.HACKRF_TRANSCEIVER_MODE_OFF
        self._bias_tee_on = False
        self._check_error(libhackrf.hackrf_stop_rx(self._device_pointer))

    def read_samples(self, num_samples: int = 131072) -> np.array:
        """
        Synchrous function to read predefined number of samples into buffer and return them as numpy array
        """
        # prevent running forever
        if not num_samples:
            return np.array([])

        self._sample_count_limit = int(2 * num_samples)
        self.start_rx()

        while self._transceiver_mode != TransceiverMode.HACKRF_TRANSCEIVER_MODE_OFF:
            pass
        # convert samples to iq
        values = np.array(self.buffer).astype(np.int8)
        iq = values.astype(np.float64).view(np.complex128)
        iq /= 127.5
        iq -= 1 + 1j
        return iq

    def _sweep_callback(self, hackrf_transfer: lib_hackrf_transfer) -> int:
        """
        Callback function will populate self.buffer with samples.
        As specified in libhackrf docs, it should return nonzero when no more samples needed.
        Will return 1  when number of samples reaches self._sample_count_limit.
        Internal use only.
        """
        bytes = bytearray(
            cast(
                hackrf_transfer.contents.buffer,
                POINTER(c_byte * hackrf_transfer.contents.buffer_length),
            ).contents
        )
        BLOCKS_PER_TRANSFER = 16  # defined in libhackrf.h
        block_size = len(bytes) // BLOCKS_PER_TRANSFER
        data = {}
        for block_index in range(BLOCKS_PER_TRANSFER):
            offset = block_index * block_size
            header = bytes[offset : offset + 10]
            frequency = struct.unpack("<Q", header[2:])
            block_data = bytes[offset + 11 : offset + block_size]
            data[frequency] = block_data

        if self._sweep_pipe_function is not None:
            if self._sweep_pipe_function(data):
                self._transceiver_mode = TransceiverMode.HACKRF_TRANSCEIVER_MODE_OFF
                self._bias_tee_on = False
                return 1
        return 0

    def start_sweep(
        self,
        bands: list[tuple[int, int]],
        num_bytes: int = 16384,
        step_width: int = 1000000,
        pipe_function=None,
        step_offset: int = None,
        interleaved=True,
    ):
        """
        Start frequency sweep scan. Will sweep over several bands (number limited to MAX_SWEEP_RANGES by libhackrf),
        band start and end are specified in MHz, tuning in steps.
        For each tuning step collecting num_bytes (must be a multiple of 16384, default = 16384),
        with tuning step width of step_width_mhz (default = 1)
        An offset of step_offset will be added to tuning (default = sampling_rate/2)
        interleaved sweep style (default = True)
        If pipe_function(dict) is specified, it will be called on data arrival for each signal in separate,
        center_freq, bytes are data for the given band. Pipe function may return boolean
        value. If True is returned, sweep is stopped. Otherwise, sweep ends on stop_rx()
        """
        MAX_SWEEP_RANGES = 10
        BYTES_PER_BLOCK = 16384

        if len(bands) > MAX_SWEEP_RANGES:
            raise ValueError(
                f"Number of sweep ranges must be less than or equal to MAX_SWEEP_RANGES ({MAX_SWEEP_RANGES}) "
            )
        if num_bytes % BYTES_PER_BLOCK:
            raise ValueError(
                f"Number of bytes per band must be a multiple of BYTES_PER_BLOCK ({BYTES_PER_BLOCK})"
            )
        band_freqs = []
        for band in bands:
            band_freqs.append(min(band.start_freq, band.stop_freq))
            band_freqs.append(max(band.start_freq, band.stop_freq))

        if step_offset is None:
            step_offset = self._sample_rate / 2

        self._check_error(
            libhackrf.hackrf_init_sweep(
                self._device_pointer,
                (c_uint16 * len(band_freqs))(*band_freqs),
                len(bands),
                int(num_bytes),
                int(step_width),
                int(step_offset),
                1 if interleaved else 0,
            )
        )

        self._sweep_pipe_function = pipe_function
        self._sample_count = 0
        self._transceiver_mode = TransceiverMode.TRANSCEIVER_MODE_RX_SWEEP
        self._check_error(
            libhackrf.hackrf_start_rx_sweep(
                self._device_pointer, self._cfunc_sweep_callback, None
            )
        )

    def _tx_callback(self, hackrf_transfer: lib_hackrf_transfer) -> int:
        """
        Callback function will feed self.buffer into HackRF in portions.
        As specified in libhackrf docs, it should return nonzero when no more samples needed.
        Internal use only.
        """
        CHUNK_SIZE = 1000000
        chunk, self.buffer = self.buffer[0:CHUNK_SIZE], self.buffer[CHUNK_SIZE:]
        hackrf_transfer.contents.buffer = (c_byte * len(chunk)).from_buffer(
            bytearray(chunk)
        )
        hackrf_transfer.contents.valid_length = len(chunk)
        if not len(self.buffer):
            self._transceiver_mode = TransceiverMode.HACKRF_TRANSCEIVER_MODE_OFF
            self._bias_tee_on = False
            return 1
        return 0

    def start_tx(self) -> None:
        """
        Send data from self.buffer to HackRF. This can be stopped by executing stop_rx()
        """
        self._transceiver_mode = TransceiverMode.HACKRF_TRANSCEIVER_MODE_TRANSMIT
        self._check_error(
            libhackrf.hackrf_start_tx(
                self._device_pointer,
                self._cfunc_tx_callback,
                None,
            )
        )

    def stop_tx(self) -> None:
        """
        Stop receiving that was started by start_rx() (or also by read_samples() under multithreading/multiprocessing)
        """
        self._transceiver_mode = TransceiverMode.HACKRF_TRANSCEIVER_MODE_OFF
        self._bias_tee_on = False
        self._check_error(libhackrf.hackrf_stop_tx(self._device_pointer))

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
        self._check_error(libhackrf.hackrf_set_freq(self._device_pointer, freq))
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
        Set sampling rate in Hertz. HackRF automatically sets baseband filter to 0.75 x sampling rate, rounded down
        to one of valid values. The filter value is computed in this setter.
        """
        self._check_error(libhackrf.hackrf_set_sample_rate(self._device_pointer, rate))
        self._filter_bandwidth = min(
            BASEBAND_FILTER_VALID_VALUES,
            key=lambda x: abs(x - 0.75 * rate) if x - 0.75 * rate < 0 else 1e8,
        )
        self._sample_rate = rate
        return

    @property
    def filter_bandwidth(self) -> int:
        """
        Return current baseband filter bandwidth in Hz
        """
        return self._filter_bandwidth

    @filter_bandwidth.setter
    def filter_bandwidth(self, value_hz: int) -> None:
        """
        Set baseband filter bandwidth in Hz. This value will be changed if sampling rate changes (HackRF computes it automatically
        to be 0.75 x sampling rate, rounded down to one of accepted values in BASEBAND_FILTER_VALID_VALUES_MHZ),
        so this need to be called after sampling rate change.
        This setter will round requested value to closest accepted one (not necessarily round down).
        """
        value_hz = min(BASEBAND_FILTER_VALID_VALUES, key=lambda x: abs(x - value_hz))
        self._check_error(
            libhackrf.hackrf_set_baseband_filter_bandwidth(
                self._device_pointer, value_hz
            )
        )
        self._filter_bandwidth = value_hz

    @property
    def lna_gain(self) -> int:
        """
        Get current low noise amplifier gain.
        """
        return self.lna_gain

    @lna_gain.setter
    def lna_gain(self, value: int) -> None:
        """
        Set low noise amplifier gain.
        """
        value = min(value, 40)
        value = max(value, 0)
        # rounds down to multiple of 8 (15 -> 8, 39 -> 32), etc.
        # internally, hackrf_set_lna_gain does the same thing
        # But we take care of it so we can keep track of the correct gain
        value -= value % 8
        self._check_error(libhackrf.hackrf_set_lna_gain(self._device_pointer, value))
        self._lna_gain = value

    @property
    def vga_gain(self) -> int:
        """
        Get current variable gain amplifier (VGA) gain value.
        """
        return self._vga_gain

    @vga_gain.setter
    def vga_gain(self, value: int) -> None:
        """
        Set variable gain amplifier (VGA) gain value.
        """
        value = min(value, 62)
        value = max(value, 0)
        value -= value % 2
        self._check_error(libhackrf.hackrf_set_vga_gain(self._device_pointer, value))
        self._vga_gain = value

    @property
    def amplifier_on(self) -> bool:
        """
        Check if 14 dB frontend RF amplifier is on or off.
        """
        return self._amplifier_on

    @amplifier_on.setter
    def amplifier_on(self, enable: bool) -> None:
        """
        Enable and disable 14 dB frontend RF amplifier.
        """
        self._check_error(
            libhackrf.hackrf_set_amp_enable(self._device_pointer, 1 if enable else 0)
        )

    @property
    def bias_tee_on(self) -> bool:
        """
        Check if bias voltage of 3.3 V (50 mA max!) is applied onto antenna (off by default)
        """
        return self._bias_tee_on

    @bias_tee_on.setter
    def bias_tee_on(self, enable: bool) -> None:
        """
        Enable and disable 3.3V bias voltage on antenna (50 mA max!). This will be disabled automatically when device goes to idle.
        """
        self._check_error(
            libhackrf.hackrf_set_antenna_enable(
                self._device_pointer, 1 if enable else 0
            )
        )
        self._bias_tee_on = enable

    @property
    def txvga_gain(self) -> int:
        """Get transmit amplifier gain"""
        return self._txvga_gain

    @txvga_gain.setter
    def txvga_gain(self, value: int) -> None:
        """Set transmit amplifier gain, 0 to 47 dB"""
        value = min(value, 47)
        value = max(value, 0)
        self._check_error(libhackrf.hackrf_set_txvga_gain(self._device_pointer, value))
        self._txvga_gain = value

    @property
    def sample_count_limit(self) -> int:
        """
        Get current receive buffer limit. 0 means that start_rx() will collect data until stop_rx() is called.
        """
        return self._sample_count_limit

    @sample_count_limit.setter
    def sample_count_limit(self, bytes: int) -> None:
        """
        Set receive buffer limit. start_rx() will stop collecting data when sample_count_limit is reached
        0 means that start_rx() will collect data until stop_rx() is called.
        """
        self._sample_count_limit = bytes

    def get_serial_no(self):
        sn = lib_read_partid_serialno_t()
        self._check_error(
            libhackrf.hackrf_board_partid_serialno_read(self._device_pointer, sn)
        )
        return "".join([f"{sn.serial_no[i]:08x}" for i in range(4)])
