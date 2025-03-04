# SPDX-FileCopyrightText: 2024 Jerry Needell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""

* Author(s): Jerry Needell
"""

import asyncio
import random
import time

from adafruit_bus_device import spi_device

try:
    from typing import Callable, Optional, Type

    import busio
    import digitalio
    from circuitpython_typing import ReadableBuffer, WriteableBuffer

except ImportError:
    pass

from micropython import const

HAS_SUPERVISOR = False

try:
    import supervisor

    if hasattr(supervisor, "ticks_ms"):
        HAS_SUPERVISOR = True
except ImportError:
    pass


__version__ = "1.0.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_RFM.git"


# RadioHead specific compatibility constants.
_RH_BROADCAST_ADDRESS = const(0xFF)

# The acknowledgement bit in the FLAGS
# The top 4 bits of the flags are reserved for RadioHead. The lower 4 bits are reserved
# for application layer use.
_RH_FLAGS_ACK = const(0x80)
_RH_FLAGS_RETRY = const(0x40)


# supervisor.ticks_ms() contants
_TICKS_PERIOD = const(1 << 29)
_TICKS_MAX = const(_TICKS_PERIOD - 1)
_TICKS_HALFPERIOD = const(_TICKS_PERIOD // 2)


def ticks_diff(ticks1: int, ticks2: int) -> int:
    """Compute the signed difference between two ticks values
    assuming that they are within 2**28 ticks
    """
    diff = (ticks1 - ticks2) & _TICKS_MAX
    diff = ((diff + _TICKS_HALFPERIOD) & _TICKS_MAX) - _TICKS_HALFPERIOD
    return diff


def asyncio_to_blocking(function):
    """run async function as normal blocking function"""

    def blocking_function(self, *args, **kwargs):
        return asyncio.run(function(self, *args, **kwargs))

    return blocking_function


async def asyncio_check_timeout(flag: Callable, limit: float, timeout_poll: float) -> bool:
    """test for timeout waiting for specified flag"""
    timed_out = False
    if HAS_SUPERVISOR:
        start = supervisor.ticks_ms()
        while not timed_out and not flag():
            if ticks_diff(supervisor.ticks_ms(), start) >= limit * 1000:
                timed_out = True
            await asyncio.sleep(timeout_poll)
    else:
        start = time.monotonic()
        while not timed_out and not flag():
            if time.monotonic() - start >= limit:
                timed_out = True
            await asyncio.sleep(timeout_poll)

    return timed_out


# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-nested-blocks
class RFMSPI:
    """Base class for SPI type devices"""

    class RegisterBits:
        """Simplify register access"""

        # Class to simplify access to the many configuration bits avaialable
        # on the chip's registers.  This is a subclass here instead of using
        # a higher level module to increase the efficiency of memory usage
        # (all of the instances of this bit class will share the same buffer
        # used by the parent RFM69 class instance vs. each having their own
        # buffer and taking too much memory).

        # Quirk of pylint that it requires public methods for a class.  This
        # is a decorator class in Python and by design it has no public methods.
        # Instead it uses dunder accessors like get and set below.  For some
        # reason pylint can't figure this out so disable the check.
        # pylint: disable=too-few-public-methods

        # Again pylint fails to see the true intent of this code and warns
        # against private access by calling the write and read functions below.
        # This is by design as this is an internally used class.  Disable the
        # check from pylint.
        # pylint: disable=protected-access

        def __init__(self, address: int, *, offset: int = 0, bits: int = 1) -> None:
            assert 0 <= offset <= 7
            assert 1 <= bits <= 8
            assert (offset + bits) <= 8
            self._address = address
            self._mask = 0
            for _ in range(bits):
                self._mask <<= 1
                self._mask |= 1
            self._mask <<= offset
            self._offset = offset

        def __get__(self, obj: Optional["RFM"], objtype: Type["RFM"]) -> int:
            reg_value = obj.read_u8(self._address)
            return (reg_value & self._mask) >> self._offset

        def __set__(self, obj: Optional["RFM"], val: int) -> None:
            reg_value = obj.read_u8(self._address)
            reg_value &= ~self._mask
            reg_value |= (val & 0xFF) << self._offset
            obj.write_u8(self._address, reg_value)

    # pylint: disable-msg=too-many-arguments
    def __init__(  # noqa: PLR0913
        self,
        spi: busio.SPI,
        cs_pin: digitalio.DigitalInOut,
        baudrate: int = 5000000,
        polarity: int = 0,
        phase: int = 0,
    ):
        self.spi_device = spi_device.SPIDevice(
            spi, cs_pin, baudrate=baudrate, polarity=polarity, phase=phase
        )
        # initialize last RSSI reading
        self.last_rssi = 0.0
        """The RSSI of the last received packet. Stored when the packet was received.
           The instantaneous RSSI value may not be accurate once the
           operating mode has been changed.
        """
        self.last_snr = 0.0
        """The SNR of the last received packet. Stored when the packet was received.
           The instantaneous SNR value may not be accurate once the
           operating mode has been changed.
        """
        # initialize timeouts and delays delays
        self.ack_wait = 0.1
        """The delay time before attempting a retry after not receiving an ACK"""
        self.receive_timeout = 0.5
        """The amount of time to poll for a received packet.
           If no packet is received, the returned packet will be None
        """
        self.xmit_timeout = 2.0
        """The amount of time to wait for the HW to transmit the packet.
           This is mainly used to prevent a hang due to a HW issue
        """
        self.ack_retries = 5
        """The number of ACK retries before reporting a failure."""
        self.ack_delay = None
        """The delay time before attemting to send an ACK.
           If ACKs are being missed try setting this to .1 or .2.
        """
        # initialize sequence number counter for reliabe datagram mode
        self.sequence_number = 0
        # create seen Ids list
        self.seen_ids = bytearray(256)
        # initialize packet header
        # node address - default is broadcast
        self.node = _RH_BROADCAST_ADDRESS
        """The default address of this Node. (0-255).
           If not 255 (0xff) then only packets address to this node will be accepted.
           First byte of the RadioHead header.
        """
        # destination address - default is broadcast
        self.destination = _RH_BROADCAST_ADDRESS
        """The default destination address for packet transmissions. (0-255).
           If 255 (0xff) then any receiving node should accept the packet.
           Second byte of the RadioHead header.
        """
        # ID - contains seq count for reliable datagram mode
        self.identifier = 0
        """Automatically set to the sequence number when send_with_ack() used.
           Third byte of the RadioHead header.
        """
        # flags - identifies ack/reetry packet for reliable datagram mode
        self.flags = 0
        """Upper 4 bits reserved for use by Reliable Datagram Mode.
           Lower 4 bits may be used to pass information.
           Fourth byte of the RadioHead header.
        """
        self.radiohead = True
        """Enable RadioHead compatibility"""

        self.crc_error_count = 0
        self.timeout_poll = 0.001

    # pylint: enable-msg=too-many-arguments

    # Global buffer for SPI commands
    _BUFFER = bytearray(4)

    # pylint: disable=no-member
    # Reconsider pylint: disable when this can be tested
    def read_into(self, address: int, buf: WriteableBuffer, length: Optional[int] = None) -> None:
        """Read a number of bytes from the specified address into the provided
        buffer.  If length is not specified (the default) the entire buffer
        will be filled."""
        if length is None:
            length = len(buf)
        with self.spi_device as device:
            self._BUFFER[0] = address & 0x7F  # Strip out top bit to set 0
            # value (read).
            device.write(self._BUFFER, end=1)
            device.readinto(buf, end=length)

    def read_u8(self, address: int) -> int:
        """Read a single byte from the provided address and return it."""
        self.read_into(address, self._BUFFER, length=1)
        return self._BUFFER[0]

    def write_from(self, address: int, buf: ReadableBuffer, length: Optional[int] = None) -> None:
        """Write a number of bytes to the provided address and taken from the
        provided buffer.  If no length is specified (the default) the entire
        buffer is written."""
        if length is None:
            length = len(buf)
        with self.spi_device as device:
            self._BUFFER[0] = (address | 0x80) & 0xFF  # Set top bit to 1 to
            # indicate a write.
            device.write(self._BUFFER, end=1)
            device.write(buf, end=length)

    def write_u8(self, address: int, val: int) -> None:
        """Write a byte register to the chip.  Specify the 7-bit address and the
        8-bit value to write to that address."""
        with self.spi_device as device:
            self._BUFFER[0] = (address | 0x80) & 0xFF  # Set top bit to 1 to indicate a write.
            self._BUFFER[1] = val & 0xFF
            device.write(self._BUFFER, end=2)

    # pylint: disable=too-many-branches

    async def asyncio_send(  # noqa: PLR0912 PLR0913
        self,
        data: ReadableBuffer,
        *,
        keep_listening: bool = False,
        destination: Optional[int] = None,
        node: Optional[int] = None,
        identifier: Optional[int] = None,
        flags: Optional[int] = None,
    ) -> bool:
        """Send a string of data using the transmitter.
        You can only send 252 bytes at a time
        (limited by chip's FIFO size and appended headers).
        if the propert radiohead is True then this appends a 4 byte header
        to be compatible with the RadioHead library.
        The header defaults to using the initialized attributes:
        (destination,node,identifier,flags)
        It may be temporarily overidden via the kwargs - destination,node,identifier,flags.
        Values passed via kwargs do not alter the attribute settings.
        The keep_listening argument should be set to True if you want to start listening
        automatically after the packet is sent. The default setting is False.

        Returns: True if success or False if the send timed out.
        """
        # Disable pylint warning to not use length as a check for zero.
        # This is a puzzling warning as the below code is clearly the most
        # efficient and proper way to ensure a precondition that the provided
        # buffer be within an expected range of bounds. Disable this check.
        # pylint: disable=len-as-condition
        assert 0 < len(data) <= self.max_packet_length
        # pylint: enable=len-as-condition
        self.idle()  # Stop receiving to clear FIFO and keep it clear.
        # Combine header and data to form payload
        if self.radiohead:
            payload = bytearray(4)
            if destination is None:  # use attribute
                payload[0] = self.destination
            else:  # use kwarg
                payload[0] = destination
            if node is None:  # use attribute
                payload[1] = self.node
            else:  # use kwarg
                payload[1] = node
            if identifier is None:  # use attribute
                payload[2] = self.identifier
            else:  # use kwarg
                payload[2] = identifier
            if flags is None:  # use attribute
                payload[3] = self.flags
            else:  # use kwarg
                payload[3] = flags
            payload = payload + data
        elif destination is not None:  # prepend destination for non RH packets
            payload = destination.to_bytes(1, "big") + data
        else:
            payload = data
        self.fill_fifo(payload)
        # Turn on transmit mode to send out the packet.
        self.transmit()
        # Wait for packet_sent interrupt with explicit polling (not ideal but
        # best that can be done right now without interrupts).
        timed_out = await asyncio_check_timeout(
            self.packet_sent, self.xmit_timeout, self.timeout_poll
        )
        # Listen again if necessary and return the result packet.
        if keep_listening:
            self.listen()
        else:
            # Enter idle mode to stop receiving other packets.
            self.idle()
        self.clear_interrupt()
        return not timed_out

    send = asyncio_to_blocking(asyncio_send)
    """Non-asyncio wrapper to Send a string of data using the transmitter
    using the same arguments and keywords as asyncio_send()
    """

    async def asyncio_send_with_ack(self, data: ReadableBuffer) -> bool:
        """Reliable Datagram mode:
        Send a packet with data and wait for an ACK response.
        The packet header is automatically generated.
        If enabled, the packet transmission will be retried on failure
        """
        if not self.radiohead:
            raise RuntimeError("send_with_ack onl suppoted in RadioHead mode")
        if self.ack_retries:
            retries_remaining = self.ack_retries
        else:
            retries_remaining = 1
        got_ack = False
        self.sequence_number = (self.sequence_number + 1) & 0xFF
        while not got_ack and retries_remaining:
            self.identifier = self.sequence_number
            await self.asyncio_send(data, keep_listening=True)
            # Don't look for ACK from Broadcast message
            if self.destination == _RH_BROADCAST_ADDRESS:
                got_ack = True
            else:
                # wait for a packet from our destination
                ack_packet = await self.asyncio_receive(timeout=self.ack_wait, with_header=True)
                if ack_packet is not None:
                    if ack_packet[3] & _RH_FLAGS_ACK:
                        # check the ID
                        if ack_packet[2] == self.identifier:
                            got_ack = True
                            break
            # pause before next retry -- random delay
            if not got_ack:
                # delay by random amount before next try
                await asyncio.sleep(self.ack_wait + self.ack_wait * random.random())
            retries_remaining = retries_remaining - 1
            # set retry flag in packet header
            self.flags |= _RH_FLAGS_RETRY
        self.flags = 0  # clear flags
        return got_ack

    send_with_ack = asyncio_to_blocking(asyncio_send_with_ack)
    """Non-asyncio wrapper to Send a string of data using the transmitter
    using the same arguments and keywords as asyncio_send_with_ack()
    """

    async def asyncio_receive(  # noqa: PLR0912
        self,
        *,
        keep_listening: bool = True,
        with_header: bool = False,
        timeout: Optional[float] = None,
    ) -> Optional[bytearray]:
        """Wait to receive a packet from the receiver. If a packet is found the payload bytes
        are returned, otherwise None is returned (which indicates the timeout elapsed with no
        reception).
        If keep_listening is True (the default) the chip will immediately enter listening mode
        after reception of a packet, otherwise it will fall back to idle mode and ignore any
        future reception.
        Packets may have a 4-byte header for compatibility with the
        RadioHead library.
        The header consists of 4 bytes (To,From,ID,Flags). The default setting will  strip
        the header before returning the packet to the caller.
        If with_header is True then the 4 byte header will be returned with the packet.
        The payload then begins at packet[4].
        """
        if not self.radiohead and with_header:
            raise RuntimeError("with_header only supported for RadioHead mode")
        timed_out = False
        if timeout is None:
            timeout = self.receive_timeout
        if timeout is not None:
            # Wait for the payloadready signal.  This is not ideal and will
            # surely miss or overflow the FIFO when packets aren't read fast
            # enough, however it's the best that can be done from Python without
            # interrupt supports.
            # Make sure we are listening for packets.
            self.listen()
            timed_out = await asyncio_check_timeout(self.payload_ready, timeout, self.timeout_poll)
        # Payload ready is set, a packet is in the FIFO.
        packet = None
        # save last RSSI reading
        self.last_rssi = self.rssi
        self.last_snr = self.snr

        # Enter idle mode to stop receiving other packets.
        self.idle()
        if not timed_out:
            if self.enable_crc and self.crc_error:
                self.crc_error_count += 1
            else:
                packet = self.read_fifo()
                if (packet is not None) and self.radiohead:
                    if len(packet) < 5:
                        # reject the packet if it is too small to contain the RAdioHead Header
                        packet = None
                    if packet is not None:
                        if (
                            self.node != _RH_BROADCAST_ADDRESS  # noqa: PLR1714
                            and packet[0] != _RH_BROADCAST_ADDRESS
                            and packet[0] != self.node
                        ):
                            packet = None
                        if not with_header and packet is not None:  # skip the header if not wanted
                            packet = packet[4:]
        # Listen again if necessary and return the result packet.
        if keep_listening:
            self.listen()
        else:
            # Enter idle mode to stop receiving other packets.
            self.idle()
        self.clear_interrupt()
        return packet

    receive = asyncio_to_blocking(asyncio_receive)
    """Non-asyncio wrapper to Receive a packet
    using the same arguments and keywords as asyncio_receive()
    """

    async def asyncio_receive_with_ack(  # noqa: PLR0912
        self,
        *,
        keep_listening: bool = True,
        with_header: bool = False,
        timeout: Optional[float] = None,
    ) -> Optional[bytearray]:
        """Wait to receive a RadioHead packet from the receiver then send an ACK packet in response.
        AKA Reliable Datagram mode.
        If a packet is found the payload bytes are returned, otherwise None is returned
        (which indicates the timeout elapsed with no reception).
        If keep_listening is True (the default) the chip will immediately enter listening mode
        after receipt of a packet, otherwise it will fall back to idle mode and ignore
        any incomming packets until it is called again.
        All packets must have a 4-byte header for compatibility with the  RadioHead library.
        The header consists of 4 bytes (To,From,ID,Flags). The default setting will  strip
        the header before returning the packet to the caller.
        If with_header is True then the 4 byte header will be returned with the packet.
        The payload then begins at packet[4].
        """
        if not self.radiohead:
            raise RuntimeError("receive_with_ack only supported for RadioHead mode")
        timed_out = False
        if timeout is None:
            timeout = self.receive_timeout
        if timeout is not None:
            # Wait for the payloadready signal.  This is not ideal and will
            # surely miss or overflow the FIFO when packets aren't read fast
            # enough, however it's the best that can be done from Python without
            # interrupt supports.
            # Make sure we are listening for packets.
            self.listen()
            timed_out = await asyncio_check_timeout(self.payload_ready, timeout, self.timeout_poll)
        # Payload ready is set, a packet is in the FIFO.
        packet = None
        # save last RSSI reading
        self.last_rssi = self.rssi
        self.last_snr = self.snr

        # Enter idle mode to stop receiving other packets.
        self.idle()
        if not timed_out:
            if self.enable_crc and self.crc_error:
                self.crc_error_count += 1
            else:
                packet = self.read_fifo()
                if (packet is not None) and self.radiohead:
                    if len(packet) < 5:
                        # reject the packet if it is too small to contain the RAdioHead Header
                        packet = None
                    if packet is not None:
                        if (
                            self.node != _RH_BROADCAST_ADDRESS  # noqa: PLR1714
                            and packet[0] != _RH_BROADCAST_ADDRESS
                            and packet[0] != self.node
                        ):
                            packet = None
                        # send ACK unless this was an ACK or a broadcast
                        elif ((packet[3] & _RH_FLAGS_ACK) == 0) and (
                            packet[0] != _RH_BROADCAST_ADDRESS
                        ):
                            # delay before sending Ack to give receiver a chance to get ready
                            if self.ack_delay is not None:
                                await asyncio.sleep(self.ack_delay)
                            # send ACK packet to sender (data is b'!')
                            await self.asyncio_send(
                                b"!",
                                destination=packet[1],
                                node=packet[0],
                                identifier=packet[2],
                                flags=(packet[3] | _RH_FLAGS_ACK),
                            )
                            # reject Retries if we have seen this idetifier from this source before
                            if (self.seen_ids[packet[1]] == packet[2]) and (
                                packet[3] & _RH_FLAGS_RETRY
                            ):
                                packet = None
                            else:  # save the packet identifier for this source
                                self.seen_ids[packet[1]] = packet[2]
                        if (
                            packet is not None and (packet[3] & _RH_FLAGS_ACK) != 0
                        ):  # Ignore it if it was an ACK packet
                            packet = None
                        if not with_header and packet is not None:  # skip the header if not wanted
                            packet = packet[4:]
        # Listen again if necessary and return the result packet.
        if keep_listening:
            self.listen()
        else:
            # Enter idle mode to stop receiving other packets.
            self.idle()
        self.clear_interrupt()
        return packet

    receive_with_ack = asyncio_to_blocking(asyncio_receive_with_ack)
    """Non-asyncio wrapper to Receive a packet
    using the same arguments and keywords as asyncio_receive_with_ack()
    """
