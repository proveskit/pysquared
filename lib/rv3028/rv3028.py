"""
This class handles the Rv3028 real time clock.

Authors: Nicole Maggard, Michael Pham, and Rachel Sarmiento
"""

from rv3028.registers import (
    BSM,
    EECMD,
    Alarm,
    Control1,
    Control2,
    EEPROMBackup,
    EventControl,
    EventFilter,
    Flag,
    Reg,
    Resistance,
    Status,
)

try:
    from tests.stubs.i2c_device import I2C, I2CDevice
except ImportError:
    from adafruit_bus_device.i2c_device import I2CDevice
    from busio import I2C

_RV3028_DEFAULT_ADDRESS = 0x52


class WEEKDAY:
    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6


class RV3028:
    def __init__(self, i2c, address: int = _RV3028_DEFAULT_ADDRESS):
        if isinstance(i2c, I2C):
            self.i2c_device = I2CDevice(i2c, address)
        elif isinstance(i2c, I2CDevice):
            self.i2c_device = i2c
        else:
            raise TypeError("i2c should be an i2c bus or device!")

    def _read_register(self, register, length=1):
        with self.i2c_device as i2c:
            i2c.write(bytes([register]))
            result = bytearray(length)
            i2c.readinto(result)
            return result

    def _write_register(self, register: Reg, data: bytes):
        with self.i2c_device as i2c:
            i2c.write(bytes([register]) + data)

    def _set_flag(self, register, mask, value):
        try:
            value = int(value)
        except Exception:
            raise ValueError("Argument 'value' must be an integer or boolean")

        data = self._read_register(register)[0]
        data &= ~mask  # Clear the bits

        shift = 0
        temp_mask = mask
        while (temp_mask & 0x01) == 0:
            temp_mask >>= 1
            shift += 1

        max_value = mask >> shift
        if value < 0 or value > max_value:
            raise ValueError(f"Value {value} does not fit in the mask {mask:#04x}")

        data |= (value << shift) & mask  # Set the bits

        self._write_register(register, bytes([data]))

    def _get_flag(self, register, mask, size=0):
        data = self._read_register(register)[0]
        result = (data & mask) >> size

        # Automatically convert to bool if mask is a single bit
        if mask & (mask - 1) == 0:
            return bool(result)
        return result

    def _eecommand(self, command: EECMD):
        while self._get_flag(Reg.STATUS, Status.EEBUSY):
            pass
        self._set_flag(Reg.CONTROL1, Control1.EEPROM_REFRESH_DISABLE, Flag.SET)
        self._set_flag(Reg.STATUS, Status.EEBUSY, Flag.SET)
        self._write_register(
            Reg.EECMD, bytes([EECMD.RESET])
        )  # First command must be 00h
        self._write_register(Reg.EECMD, bytes([command]))  # Update command
        self._set_flag(Reg.STATUS, Status.EEBUSY, Flag.CLEAR)
        self._set_flag(Reg.CONTROL1, Control1.EEPROM_REFRESH_DISABLE, Flag.CLEAR)

    def _bcd_to_int(self, bcd):
        return (bcd & 0x0F) + ((bcd >> 4) * 10)

    def _int_to_bcd(self, value):
        return ((value // 10) << 4) | (value % 10)

    def set_time(self, hours: int, minutes: int, seconds: int) -> None:
        """
        Sets the time on the device. This method configures the device's clock.

        Args:
            hours (int): The hour value to set (0-23 for 24-hour format).
            minutes (int): The minute value to set (0-59).
            seconds (int): The second value to set (0-59).
        """
        data = bytes(
            [
                self._int_to_bcd(seconds),
                self._int_to_bcd(minutes),
                self._int_to_bcd(hours),
            ]
        )
        self._write_register(Reg.SECONDS, data)

    def get_time(self) -> tuple[int, int, int]:
        """
        Retrieves the current time from the device.

        Returns:
            tuple: A tuple containing the current time as (hours, minutes, seconds),
            where:
                hours (int): The hour value (0-23 for 24-hour format).
                minutes (int): The minute value (0-59).
                seconds (int): The second value (0-59).
        """
        data = self._read_register(Reg.SECONDS, 3)
        return (
            self._bcd_to_int(data[2]),  # hours
            self._bcd_to_int(data[1]),  # minutes
            self._bcd_to_int(data[0]),  # seconds
        )

    def set_date(self, year: int, month: int, date: int, weekday: int) -> None:
        """
        Sets the date of the device.

        Args:
            year (int): The year value to set
            month (int): The month value to set (1-12).
            date (int): The date value to set (1-31).
            weekday (int): The day of the week to set (0-6, where 0 represents Sunday).
        """
        data = bytes(
            [
                self._int_to_bcd(weekday),
                self._int_to_bcd(date),
                self._int_to_bcd(month),
                self._int_to_bcd(year),
            ]
        )
        self._write_register(
            Reg.WEEKDAY, data
        )  # this is a weird way to do it but it works

    def get_date(self) -> tuple[int, int, int, int]:
        """
        Gets the date of the device.

        Returns:
            tuple: A 4-tuple (year, month, date, weekday) where:
                year (int): The year value (0-99).
                month (int): The month value (1-12).
                date (int): The date value (1-31).
                weekday (int): The day of the week (0-6, where 0 represents Sunday).
        """
        data = self._read_register(Reg.WEEKDAY, 4)
        return (
            self._bcd_to_int(data[3]),  # year
            self._bcd_to_int(data[2]),  # month
            self._bcd_to_int(data[1]),  # date
            self._bcd_to_int(data[0]),  # weekday
        )

    def set_alarm(
        self, minute: int = None, hour: int = None, weekday: int = None
    ) -> None:
        """
        Set the alarm time. A value of None indicates that that portion of the alarm will not be used.

        Args:
            Alarm minute (0-59) or None
            Alarm hour (0-23) or None
            Alarm weekday (0-6, 0=Sunday) or None
        """
        # Set alarm mask to check for minute, hour, and weekday match
        control2 = self._read_register(Reg.CONTROL2)[0]
        self._set_flag(Reg.CONTROL2, Control2.ALARM_INT_ENABLE, Flag.SET)
        self._write_register(Reg.CONTROL2, bytes([control2]))

        if minute is not None and (minute < 0 or minute > 59):
            raise ValueError("Invalid minute value")
        if hour is not None and (hour < 0 or hour > 23):
            raise ValueError("Invalid hour value")
        if weekday is not None and (weekday < 0 or weekday > 6):
            raise ValueError("Invalid weekday value")

        data = bytes(
            (self._int_to_bcd(param) & Alarm.VALUE)
            if param is not None
            else Alarm.DISABLED
            for param in (minute, hour, weekday)
        )

        self._write_register(Reg.ALARM_MINUTES, data)

    def check_alarm(self, clear: bool = True) -> bool:
        """
        Check if the alarm flag has been triggered.

        Args:
            clear (bool): (Default: True) True to clear the alarm flag, False to leave it set.
        Returns:
            True if alarm flag is set, False otherwise
        """
        result = self._get_flag(Reg.STATUS, Status.ALARM)
        if clear and result:
            self._set_flag(Reg.STATUS, Status.ALARM, Flag.CLEAR)

        return bool(result)

    def get_alarm(self) -> tuple:
        """
        If an alarm has been set on the device, provides the set time.

        Returns:
            A tuple representing the alarm configuration. A return value of None in any field means that that field was not set. Tuple values:
                minute (int or None): the minute value of the alarm (0-59)
                hour (int or None): the hour value of the alarm (0-23)
                weekday (int or None): the weekday of the alarm (0-6, 0 = Sunday)
        """

        # Defining the helper in here limits its scope so outside users can't access it.
        def _get_alarm_field(reg: Reg):
            disabled = self._get_flag(reg, Alarm.DISABLED)
            if disabled:
                return None
            else:
                return self._get_flag(reg, Alarm.VALUE)

        return (
            _get_alarm_field(Reg.ALARM_MINUTES),
            _get_alarm_field(Reg.ALARM_HOURS),
            _get_alarm_field(Reg.ALARM_WEEKDAY),
        )

    def enable_trickle_charger(self, resistance=3000):
        self._set_flag(Reg.EEPROM_BACKUP, EEPROMBackup.TRICKLE_CHARGE_ENABLE, Flag.SET)
        self._set_flag(Reg.EEPROM_BACKUP, EEPROMBackup.TRICKLE_CHARGE_RES, Flag.CLEAR)

        # Set TCR (Trickle Charge Resistor) bits
        if resistance not in [3000, 5000, 9000, 15000]:
            raise ValueError("Invalid trickle charger resistance")
        if resistance == 3000:
            tcr_value = Resistance.RES_3000
        elif resistance == 5000:
            tcr_value = Resistance.RES_5000
        elif resistance == 9000:
            tcr_value = Resistance.RES_9000
        elif resistance == 15000:
            tcr_value = Resistance.RES_15000

        self._set_flag(Reg.EEPROM_BACKUP, EEPROMBackup.TRICKLE_CHARGE_RES, tcr_value)

        # Refresh the EEPROM to apply changes
        self._eecommand(EECMD.REFRESH)

    def disable_trickle_charger(self):
        self._set_flag(
            Reg.EEPROM_BACKUP, EEPROMBackup.TRICKLE_CHARGE_ENABLE, Flag.CLEAR
        )
        self._eecommand(EECMD.REFRESH)

    def configure_evi(self, enable=True):
        """
        Configure EVI for rising edge detection, enable time stamping,
        and enable interrupt.

        :param enable: True to enable EVI, False to disable
        """
        if enable:
            # Configure Event Control Register
            self._set_flag(
                Reg.EVENT_CONTROL, EventControl.EVENT_HIGH_LOW_SELECT, Flag.SET
            )
            self._set_flag(
                Reg.EVENT_CONTROL, EventControl.EVENT_FILTER, EventFilter.FILTER_OFF
            )

            # Enable time stamping and EVI interrupt
            self._set_flag(Reg.CONTROL2, Control2.TIMESTAMP_ENABLE, Flag.SET)
            self._set_flag(Reg.CONTROL2, Control2.EVENT_INT_ENABLE, Flag.SET)
        else:
            self._set_flag(Reg.CONTROL2, Control2.TIMESTAMP_ENABLE, Flag.CLEAR)
            self._set_flag(Reg.CONTROL2, Control2.EVENT_INT_ENABLE, Flag.CLEAR)

    def get_event_timestamp(self):
        """
        Read the timestamp of the last EVI event.

        :return: Tuple of (year, month, date, hours, minutes, seconds, count)
        """
        data = self._read_register(Reg.TIMESTAMP_COUNT, 7)
        return (
            self._bcd_to_int(data[6]),  # year
            self._bcd_to_int(data[5]),  # month
            self._bcd_to_int(data[4]),  # date
            self._bcd_to_int(data[3]),  # hours
            self._bcd_to_int(data[2]),  # minutes
            self._bcd_to_int(data[1]),  # seconds
            data[0],  # count (not BCD)
        )

    def check_event_flag(self, clear=True):
        """
        Check if the Event Flag (EVF) is set in the Status Register.

        :return: True if EVF is set, False otherwise
        """
        result = self._get_flag(Reg.STATUS, Status.EVENT)
        if result and clear:
            self._set_flag(Reg.STATUS, Status.EVENT, Flag.CLEAR)

        return result

    def configure_backup_switchover(self, mode="level", interrupt=False):
        """
        Configure the Automatic Backup Switchover function.

        :param mode: 'level' for Level Switching Mode (LSM),
                     'direct' for Direct Switching Mode (DSM),
                     or 'disabled' to disable switchover
        :param interrupt: True to enable backup switchover interrupt, False to disable
        """

        if mode == "level":
            backup_mode = BSM.LEVEL
        elif mode == "direct":
            backup_mode = BSM.DIRECT
        elif mode == "disabled":
            backup_mode = BSM.DISABLED
        else:
            raise ValueError("Invalid mode. Use 'level', 'direct', or 'disabled'.")

        self._set_flag(Reg.EEPROM_BACKUP, EEPROMBackup.BACKUP_SWITCHOVER, backup_mode)

        # Configure backup switchover interrupt
        if interrupt:
            self._set_flag(
                Reg.EEPROM_BACKUP, EEPROMBackup.BACKUP_SWITCHOVER_INT_ENABLE, Flag.SET
            )
        else:
            self._set_flag(
                Reg.EEPROM_BACKUP, EEPROMBackup.BACKUP_SWITCHOVER_INT_ENABLE, Flag.CLEAR
            )

        # Always enable fast edge detection
        self._set_flag(Reg.EEPROM_BACKUP, EEPROMBackup.FEDE, Flag.SET)

        # Update EEPROM
        self._eecommand(EECMD.REFRESH)

    def check_backup_switchover(self, clear=True):
        """
        Check if a backup switchover has occurred.

        :return: True if switchover occurred, False otherwise
        """
        result = self._get_flag(Reg.STATUS, Status.BACKUP_SWITCH)
        if result and clear:
            self._set_flag(Reg.STATUS, Status.BACKUP_SWITCH, Flag.CLEAR)
        return result
